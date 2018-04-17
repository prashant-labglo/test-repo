import json, os, pickle
from django.contrib.postgres.fields import JSONField as PostgresJSONField
from cachetools import LRUCache
from jsonfield import JSONField
from enumfields import Enum, EnumField
from django.utils import timezone
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, post_delete, pre_save
from SlideDB.models import Slide, Concept, SubConcept, Construct
from SlideSearch import slideSearchIndexLoad
from LibLisa import lastCallProfile, lisaConfig, methodProfiler, blockProfiler
from LibLisa.config import lisaConfig
from ZenCentral.middleware import get_current_user

UserModel = get_user_model()


class SearchResultRating(models.Model):
    """
    Model for rating search results.
    Rating is a user's perception of the fitness of a slide against a SearchQuery.
    """
    rated = models.IntegerField(default=0, validators=[MaxValueValidator(3), MinValueValidator(-3)])

    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    slide = models.ForeignKey(Slide, related_name="ratings", on_delete=models.CASCADE)
    query = models.ForeignKey("SearchQuery", related_name="ratings", on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'slide',)

    @property
    def allDownloads(self):
        results = SearchResult.objects.filter(slide=self.slide, queryInvocation__query=self.query)
        allDownloads = sum([obj.downloads for obj in results])
        return allDownloads


class SearchResult(models.Model):
    """
    Each search query may output a large number of search results shown to the user.
    """
    slide = models.ForeignKey(Slide, on_delete=models.CASCADE)
    rank = models.IntegerField()
    queryInvocation = models.ForeignKey('SearchQueryInvocation', related_name="results", on_delete=models.CASCADE)
    downloads = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    # Add rating.
    score = models.FloatField()
    
    class Meta:
        ordering = ('queryInvocation', 'rank', )

    @classmethod
    def pre_save(cls, sender, instance, *args, **kwargs):
        """
        Upon save, we populate other values, if missing.
        """
        if not instance.id:
            instance.downloads = 0

    @property
    def thumbnailFile(self):
        return self.slide.thumbnailFile

    @property
    def pptFile(self):
        return self.slide.pptFile

    @property
    def slideDownloadFeatures(self):
        """
        For the current result object, this method finds the rating of the
        "current user" and returns it.

        These properties are used by pyltr models to improve search quality.
        """
        otherResultsWithSameSlide = SearchResult.objects.filter(slide=self.slide)
        downloadCount = 0
        for result in otherResultsWithSameSlide:
            downloadCount += result.allDownloads

        if downloadCount == 0:
            return (0, 0)
        else:
            return (downloadCount, downloadCount/len(otherResultsWithSameSlide))

    @property
    def myDownloads(self):
        """
        For the current result object, this method finds the download count of the
        "current user" and returns it.

        This property is used by Search result serializers for the REST API.
        """

        curUser = get_current_user()
        if curUser.is_anonymous:
            return None
        ratingObj = SearchResultRating.objects.get(
            slide=self.slide, query=self.queryInvocation.query, user=curUser
        )
        if ratingObj is None:
            return None
        return self.downloads

    @myDownloads.setter
    def myDownloads(self, newDownloads):
        """
        For the current result object, this method 'increments' the downloads count
        of the "current user".

        This property is used by Search result serializers for the REST API.
        """
        curUser = get_current_user()
        if not curUser.is_anonymous:
            ratingObj = SearchResultRating.objects.get(
                slide=self.slide, query=self.queryInvocation.query, user=curUser
            )
            if ratingObj is not None:
                if newDownloads > self.downloads:
                    self.downloads += 1
            else:
                raise ValueError("Cannot increment download count, without rating the slide.")
            self.save()
        else:
            raise PermissionError("Anonymous user cannot increment download count.")

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
        ratingObj = SearchResultRating.objects.get(
            slide=self.slide, query=self.queryInvocation.query, user=curUser
        )
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
            ratingObj = SearchResultRating.objects.get(
                slide=self.slide, query=self.queryInvocation.query, user=curUser
            )
            if ratingObj is not None:
                ratingObj.rated = newRating
            else:
                ratingObj = SearchResultRating(
                    rated=newRating, slide=self.slide, query=self.queryInvocation.query, user=curUser
                )
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
        for ratingObj in SearchResultRating.objects.filter(slide=self.slide, query=self.queryInvocation.query):
            countRatings += 1
            sumRatings += ratingObj.rated
        if countRatings is 0:
            return None
        return sumRatings/countRatings


class SearchQuery(models.Model):
    """
    Model class to save the input search query by user.
    """

    # Query definition.
    queryJson = PostgresJSONField(default={"Keywords": []})


class SearchQueryInvocation(models.Model):
    """
    Model class for any query made by any user.
    """
    # Session linking.
    index = models.ForeignKey("SearchIndex", related_name="invocations", on_delete=models.CASCADE)

    query = models.ForeignKey("SearchQuery", related_name="invocations", on_delete=models.CASCADE)

    # A list of results and their scores.
    resultJson = JSONField(default=[])

    # TimeStamps
    created = models.DateTimeField(editable=False)

    @classmethod
    def pre_save(cls, sender, instance, *args, **kwargs):
        """
        Upon save, we update timestamps and populate other values, if missing.
        """
        if not instance.id:
            instance.created = timezone.now()


class IndexTypeChoices(Enum):
    """
    Enum class for type of search index being created.
    """
    SimulatedRatings = 0
    UserRatings = 1


class SearchIndex(models.Model):
    """
    Database model for slide search index.
    """
    created = models.DateTimeField(editable=False)

    indexType = EnumField(IndexTypeChoices, default=IndexTypeChoices.UserRatings)

    # All Rankings made for rankingSources are also available for rankings for this search index.
    rankingSources = models.ManyToManyField('SearchQuery', blank=True)

    # Result of evaluation of the index.
    evalResults = JSONField(default={})

    def pickFilename(instance, filename):
        filename = "Type_{0}.Compat_{1}.ID_{2}.Create_{3}.pkl".format(
            instance.indexType,
            instance.schemaVersion,
            instance.id,
            instance.created)
        return os.path.join(lisaConfig.uploadsFolder, filename)

    pickledModelFile = models.FileField(upload_to=pickFilename)

    schemaVersion = models.IntegerField()

    # Cache object is used to select which search index data structures to
    # keep in memory. A maximum of 3 are kept in memory at a time.
    searchIndexCache = LRUCache(maxsize=3)

    @property
    @methodProfiler
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
        if modelInstance is None:
            # Build data to index.
            dataForIndexing = {}
            print("Starting preparation of dataForIndexing")
            for model in [Concept, SubConcept, Construct, Slide]:
                # serializedData = serializer(model.objects.all(), many=True, context={'request': request}).data
                modelArray = []
                dataForIndexing[model.__name__ + "s"] = model.objects.all()

            lisaConfig["slideSearch"].isDjangoModel = True
            print("Starting slideSearchIndexLoad")
            # Load and cache model instance.
            modelInstance = slideSearchIndexLoad(
                self.pickledModelFile,
                dataForIndexing,
                lisaConfig.slideSearch,
                self.schemaVersion)
            SearchIndex.searchIndexCache[self.id] = modelInstance
        return modelInstance

    def save(self, *args, **kwargs):
        """
        On save, we may update timestamps.
        """
        if not self.id:
            self.created = timezone.now()
        return super().save(*args, **kwargs)

    @methodProfiler
    def slideSearch(self, queryObj):
        searchIndexBackend = queryObj.index.backend
        retval = searchIndexBackend.slideSearch(queryObj.queryJson, getIDs=True)

        return retval

# Connects pre_save signal of SearchQuery.
pre_save.connect(SearchQueryInvocation.pre_save, sender=SearchQueryInvocation)
pre_save.connect(SearchResult.pre_save, sender=SearchResult)
