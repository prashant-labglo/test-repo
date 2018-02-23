import json, os, pickle
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
        ordering = ('query', 'rank', )

    @property
    def thumbnailFile(self):
        return self.slide.thumbnailFile

    @property
    def pptFile(self):
        return self.slide.pptFile

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
    queryJson = JSONField(default={"Keywords":[]})

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
            instance.queryJson["Keywords"] = []
        elif isinstance(instance.queryJson["Keywords"], str):
            instance.queryJson["Keywords"] = [instance.queryJson["Keywords"]]

        if "HasIcon" in instance.queryJson:
            instance.queryJson["HasIcon"] = True if instance.queryJson["HasIcon"] else False

        if "HasImage" in instance.queryJson:
            instance.queryJson["HasImage"] = True if instance.queryJson["HasImage"] else False

        instance.queryJson["Keywords"] = [word.lower() for word in instance.queryJson["Keywords"]]
        if "count" not in instance.queryJson.keys():
            instance.queryJson["count"] = 100

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

    pickledModelFile = models.FileField(upload_to="searchIndices")

    schemaVersion = models.IntegerField()
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
            return pickle.load(self.pickledModelFile)

    def save(self, *args, **kwargs):
        """
        On save, we may update timestamps.
        """
        if not self.id:
            self.created = timezone.now()
        return super().save(*args, **kwargs)

    def slideSearch(self, queryObj):
        searchIndexBackend = queryObj.index.backend
        return searchIndexBackend.slideSearch(queryObj.queryJson, getIDs=True)

# Connects pre_save signal of SearchQuery.
pre_save.connect(SearchQuery.pre_save, sender=SearchQuery) 
