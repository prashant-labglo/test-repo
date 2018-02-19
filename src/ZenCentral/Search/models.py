import json, os
from attrdict import AttrDict
from cachetools import LRUCache
from jsonfield import JSONField
from enumfields import Enum, EnumField
from django.utils import timezone
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, post_delete, pre_save
from SlideDB.models import Slide, Concept, SubConcept, Construct
from SlideSearch import Word2vecDistanceModel, SlideSearchW2V, SlideSearchLambdaMart
from LibLisa import lastCallProfile, lisaConfig, textCleanUp, methodProfiler, blockProfiler
from ZenCentral.middleware import get_current_user

UserModel = get_user_model()

class SearchResultRating(models.Model):
    """
    Model for rating search results.
    
    Each user can rate the result differently. So rating object is kept outside result.
    """
    rated = models.IntegerField(
        default=0,
        validators=[MaxValueValidator(3), MinValueValidator(-3)]
     )

    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    result = models.ForeignKey("SearchResult", related_name="ratings", on_delete=models.CASCADE)
    class Meta:
        unique_together = ('user', 'result',)

# Create your models here.
class SearchResult(models.Model):
    """
    Each search query may output a large number of search results shown to the user.
    """
    slide = models.ForeignKey(Slide, on_delete=models.CASCADE)
    rank = models.IntegerField()
    query = models.ForeignKey('SearchQuery', related_name="results", on_delete=models.CASCADE)

    # Add rating.
    score = models.FloatField()
    
    class Meta:
        ordering = ('rank', )

    @property
    def myRating(self):
        """
        For the current result object, this method finds the rating of the
        "current user" and returns it.

        This property is used by Search result serializers for the REST API.
        """
        curUser = get_current_user()
        if curUser.is_anonymous:
            return None
        ratingObj = SearchResultRating.objects.get(result=self, user=curUser)
        if ratingObj is None:
            return None
        return ratingObj.rated

    @myRating.setter
    def myRating(self, newRating):
        """
        For the current result object, this method 'sets' the rating of the
        "current user".

        This property is used by Search result serializers for the REST API.
        """
        curUser = get_current_user()
        if not curUser.is_anonymous:
            ratingObj = SearchResultRating.objects.get(result=self, user=curUser)
            if ratingObj is not None:
                ratingObj.rated = newRating
            else:
                ratingObj = SearchResultRating(rated=newRating, result=self, user=curUser)
                ratingObj.save()
        else:
            raise PermissionError("Anonymous user cannot rate.")

    @property
    def avgRating(self):
        """
        For the current result object, this method finds the average rating of
        among users and returns it.

        This property is used by Search result serializers for the REST API.
        """
        sumRatings = 1
        countRatings = 0
        for ratingObj in SearchResultRating.objects.filter(result=self):
            countRatings += 1
            sumRatings += ratingObj.rated
        if countRatings is 0:
            return None
        return sumRatings/countRatings

class SearchQuery(models.Model):
    """
    Model class for any query made by any user.
    """
    # Session linking.
    index = models.ForeignKey("SearchIndex", related_name="queries", on_delete=models.CASCADE)

    # Query definition.
    queryJson = JSONField(default={"Keywords":["agenda"]})

    # TimeStamps
    created = models.DateTimeField(editable=False)

    @classmethod
    def pre_save(cls, sender, instance, *args, **kwargs):
        """
        Upon save, we update timestamps and populate other values, if missing.
        """
        if not instance.id:
            instance.created = timezone.now()

        if "Keywords" not in instance.queryJson or not instance.queryJson["Keywords"]:
            instance.queryJson = {"Keywords":["agenda"]}

        instance.queryJson["Keywords"] = [word.lower() for word in instance.queryJson["Keywords"]]
        if "count" not in instance.queryJson.keys():
            instance.queryJson["count"] = 100

class IndexTypeChoices(Enum):
    """
    Enum class for type of search index being created.
    """
    TrainingSeed = 0
    LambdaMART = 1

class SearchIndex(models.Model):
    """
    Database model for slide search index.
    """
    created = models.DateTimeField(editable=False)
    indexType = EnumField(IndexTypeChoices, default=IndexTypeChoices.LambdaMART)
    # All Rankings made for rankingSources are also available for rankings for this search index.
    rankingSources = models.ManyToManyField('SearchIndex', blank=True)

    # Model to find word distances using word2vec.
    word2vecDistanceModel = Word2vecDistanceModel()

    # Cache object is used to select which search index data structures to
    # keep in memory. A maximum of 3 are kept in memory at a time.
    searchIndexCache = LRUCache(maxsize=3)

    @property
    def backend(self):
        """
        At a time, any number of django model objects corresponding to the
        same DB instance can be in memory.

        1 db instance of search engine  <-----> 10 model instances in memory.

        However, in case of model objects of the search engine, we allocate a large
        memory foot print when we load it into memory. Those big data structures
        should exist as a single instance in memory.

        1 db instance of search engine  <-----> 10 model instances in memory.
                                                      \   \   \  |  /  /  /
                                                         searchIndexCache
                                                                |
                                          1 instance of searchIndexModelObj.backend                     

        SearchIndex.searchIndexCache acts as the cache for dictionary objects, 
        which are per-index-unique.

        And searchIndexModelObj.backend returns the per-index-unique dictionary object
        with all necessary data structures required for the search index.
        """
        modelInstance = SearchIndex.searchIndexCache.get(self.id)
        if modelInstance is not None:
            # Set initial cached attributes
            return modelInstance
        else:
            modelInstance = AttrDict()

            # Set initial cached attributes.
            modelInstance.innerIndex = None
            modelInstance.Tx = None
            modelInstance.Ty = None
            modelInstance.Tqids = None
            modelInstance.fittingDone = None

            self.searchIndexCache[self.id] = modelInstance

        return modelInstance

    def save(self, *args, **kwargs):
        """
        On save, we may update timestamps.
        """
        if not self.id:
            self.created = timezone.now()
        return super().save(*args, **kwargs)

    def prepareSlideHierarchy(self):
        """
        Prepare slide hierarchy in SlideDB for indexing.

        Builds self.innerIndex using the current slide hierarchy data in ZenCentral SlideDB.
        self.innerIndex can then be used to make and answer slide search queries.
        """
        # Build data to index.
        dataForIndexing = {}
        print("Starting prepareSlideHierarchy")
        for model in [Concept, SubConcept, Construct, Slide]:
            # serializedData = serializer(model.objects.all(), many=True, context={'request': request}).data
            dataForIndexing[model.__name__ + "s"] = model.objects.all()

        print("Data to index extracted.")

        # Slide search using LambdaMART.
        lisaConfig.slideSearch.isDjangoModel = True
        self.backend.dataForIndexing = dataForIndexing
        self.backend.innerIndex = SlideSearchLambdaMart(
            dataForIndexing,
            lisaConfig.slideSearch,
            self.word2vecDistanceModel)
        print("Inner index prepared.")

    def prepareTrainingData(self, forceCreate=False):
        """
        Ranking slides is done using a ML based Learning-To-Rank approach.
        This means that rankings change basde on learning.
        Now, learning requires training data. This method loads or builds the training data.
        """
        print("Starting prepareTrainingData")
        if self.backend.innerIndex is None:
            self.prepareSlideHierarchy()

        # Find the location of file to save.
        trainingDataFilePath = lisaConfig.dataFolderPath + "{0}/trainingData.json".format(self.id)
        os.makedirs(os.path.dirname(trainingDataFilePath), exist_ok=True)

        if forceCreate or not(os.path.exists(trainingDataFilePath)):
            # Training data does not exist. Must be created from scratch.
            slideSearchIndexSeed = SlideSearchW2V(
                self.backend.dataForIndexing,
                lisaConfig.slideSearch,
                self.word2vecDistanceModel)
            (Tx, Ty, Tqids, TresultIds) = self.backend.innerIndex.buildSeedTrainingSet(slideSearchIndexSeed)
            with open(trainingDataFilePath, "w") as fp:
                json.dump(
                    {"Tx":Tx, "Ty":Ty, "Tqids":Tqids, "TresultIds":TresultIds},
                    fp,
                    indent=4)
            self.backend.Tx = Tx
            self.backend.Ty = Ty
            self.backend.Tqids = Tqids
            self.backend.TresultIds = TresultIds
        else:
            with open(trainingDataFilePath, "r") as fp:
                trainingData = json.load(fp)
            self.backend.Tx = trainingData["Tx"]
            self.backend.Ty = trainingData["Ty"]
            self.backend.Tqids = trainingData["Tqids"]
            self.backend.TresultIds = trainingData["TresultIds"]
    def getTrainingData(self):
        if self.backend.Tx is None:
            return Response({"Status" : "Not Loaded"})
        else:
            retval = []
            for i in range(len(self.backend.Tx)):
                retval.append({
                        "Tqids" : self.backend.Tqids[i],
                        "Tx": self.backend.Tx[i],
                        "Ty": self.backend.Ty[i],
                        "TresultIds": self.backend.TresultIds[i]})
            trainingDataFormattedFilePath = lisaConfig.dataFolderPath + "{0}/trainingDataFormatted.json".format(pk)
            with open(trainingDataFormattedFilePath, "w") as fp:
                json.dump(retval, fp, indent=4)

            return retval

    def fit(self):
        """
        We call this to build model parameters from training data.
        """
        print("Starting prepareTrainingData")
        if self.backend.Tx is None:
            self.prepareTrainingData()

        # LambdaMART index is now trained using the training data.
        self.backend.innerIndex.fit(self.backend.Tx, self.backend.Ty, self.backend.Tqids)
        self.backend.fittingDone = True

# Connects pre_save signal of SearchQuery.
pre_save.connect(SearchQuery.pre_save, sender=SearchQuery) 