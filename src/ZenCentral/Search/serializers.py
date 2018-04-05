from collections import OrderedDict
from rest_framework import serializers, pagination
from rest_framework.reverse import reverse
from ZenCentral.middleware import get_current_request
from LibLisa import methodProfiler
from SlideDB.models import Slide
from Search.models import SearchResult, SearchResultRating, SearchQuery, SearchIndex
from Search.models import IndexTypeChoices
from ZenCentral import fields


class UpsertingOnPostResultRatingSerializer(serializers.Serializer):
    """
    - Serializer to create and update the Search Result Rating objects with post request.
    - If this class is derived from ModelSerializer", we get validation issues when updating an object in POST request.
    """

    rated = serializers.IntegerField()
    result = serializers.IntegerField()

    def create(self, validated_data):
        try:
            result_obj = SearchResult.objects.get(id=validated_data['result'])
        except:
            raise serializers.ValidationError({'result': 'SearchResult object not present'})
        SearchResultRating.objects.create(
            rated=validated_data['rated'], result=result_obj, user=self.context['request'].user
        )
        return validated_data


class SearchResultRatingSerializer(serializers.ModelSerializer):
    """
    Serializer for /search/ratings
    """
    user = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault())

    class Meta:
        model = SearchResultRating
        fields = ('rated', 'result', 'user')


class SearchResultSerializer(serializers.ModelSerializer):
    """
    Serializer for /search/results
    """
    id = serializers.IntegerField(read_only=True)
    myRating = serializers.IntegerField(read_only=True)
    ratings = SearchResultRatingSerializer(many=True)

    class Meta:
        model = SearchResult
        fields = ('id', 'slide', 'rank', 'query', 'ratings', 'myRating', 'avgRating')
        read_only_fields = ('id', 'slide', 'rank', 'query', 'ratings')


class NestedSearchResultRatingSerializer(serializers.ModelSerializer):
    """
    In /search/queries, we directly serialize search results under each query.
    Each result has a number of ratings.
    This class helps serialize rating object, when it appears under a query's result
    in /search/queries.
    """
    user = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault())

    class Meta:
        model = SearchResultRating
        fields = ('rated', 'user')


class NestedSearchResultSerializer(serializers.ModelSerializer):
    """
    In /search/queries, we directly serialize search results under each query.
    This class helps serialize search result object, when it appears under a query.
    in /search/queries.
    """
    avgRating = serializers.FloatField(read_only=True)
    myRating = serializers.IntegerField(read_only=False)
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = SearchResult
        fields = ('id', 'slide', 'avgRating', 'myRating', 'score', 'pptFile', 'thumbnailFile')


class PaginatedSearchResultListSerializer(serializers.ListSerializer):
    """
    This class makes the pagination possible for search results serialized by
    NestedSearchResultSerializer.

    NestedSearchResultSerializer does this by over-riding its list serializer.
    Job of a list-serializer is to serialize/de-serialize list of underlying objects.
    This class is THE over-ridden list-serializer for NestedSearchResultSerializer.

    It inserts and de-inserts pagination information in the serialization pipeline.

    originalResults = [....]
            |
            |
           \ /
            |
    paginatedResults = {
        "next" : "http://....&page=#",
        "prev" : "http://....&page=#",
        "count" : #Count,
        "results" : originalResultsArray[pageNo:pageNo+100]
    }
    """
    def to_representation(self, page):
        """
        Insert pagination information.
        """
        paginationObj = self.context["paginationObj"]
        retval = OrderedDict([
            ('count', page.paginator.count),
            ('next', paginationObj.get_next_link()),
            ('previous', paginationObj.get_previous_link()),
            ('results', super().to_representation(page))
        ])
        return retval

    def to_internal_value(self, data):
        """
        Remove pagination data and return.
        """
        return super().to_internal_value(data["results"])

    @property
    def data(self):
        """
        Overriding the data property is also required. Somewhat unfortunate.
        """
        ret = super(serializers.ListSerializer, self).data
        return ret


class PaginatedSearchResultSerializer(NestedSearchResultSerializer):
    """
    In /search/queries, when we are serializing paginated search results,
    the pagination information(see diag below) needs to be inserted and
    de-inserted in the serialization pipeline.

    originalResults = [....]
            |
            |
           \ /
            |
    paginatedResults = {
        "next" : "http://....&page=#",
        "prev" : "http://....&page=#",
        "count" : #Count,
        "results" : originalResultsArray[pageNo:pageNo+100]
    }
    
    This class achieves the above insertion/removal of pagination information by
    overriding list_serializer_class of NestedSearchResultSerializer.
    """
    class Meta(NestedSearchResultSerializer.Meta):
        list_serializer_class=PaginatedSearchResultListSerializer


class QueryResultsIteratorWithAutoInsertion(object):
    """
    For a query object, there can be large number of search results.
    We want to insert results on demand, as the DB insertion is slow.
    """
    def __init__(self, queryObj):
        """
        Constructor.
        """
        self.queryObj = queryObj

        # Needed for old queries. Build resultJson, if it doesn't exist.
        if not self.queryObj.resultJson:
            results = SearchResult.objects.filter(query=self.queryObj)
            self.queryObj.resultJson = [(result.score, result.slide.id) for result in results]
            self.queryObj.save()

    def __len__(self):
        """
        Returns complete length of the results list.
        """
        return len(self.queryObj.resultJson)

    def __getitem__(self, key):
        """
        Makes the class scriptable.
        """
        if isinstance(key, int):
            # Handle negative indices
            if key < 0 :
                key += len( self )

            # Handle out of range access.
            if key < 0 or key >= len(self.queryObj.resultJson) :
                raise IndexError("The index (%d) is out of range."%key)
            try:
                # First try pre-existing DB entries.
                return SearchResult.objects.get(query=self.queryObj, rank=key)
            except SearchResult.DoesNotExist:
                # Create a new entry for DB and insert it.
                (score, slideId) = self.queryObj.resultJson[key]
                slide = Slide.objects.get(id=slideId)
                searchResult = SearchResult(slide=slide, rank=key, query=self.queryObj, score=score)
                searchResult.save()
                return searchResult
        elif isinstance(key, slice):
            start = 0 if key.start is None else key.start
            step = 1 if key.step is None else key.step
            return [self[index] for index in range(start, key.stop, step)]


class SearchQuerySerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for /search/queries.
    """
    id = serializers.IntegerField(read_only=True)
    # queryJSON, being a custom model field type, needs a custom invocation of the field serializer.
    queryJson = serializers.JSONField()

    # Making results read only in the API.
    results = serializers.SerializerMethodField('paginated_results')

    class Meta:
        model = SearchQuery
        fields = ('id', 'index', 'queryJson', 'created', 'results')

    def to_internal_value(self, data):
        if "index" not in data.keys() or not data["index"]:
            # Converts json data received into SearcuQuery instance.
            # Fills up missing data with defaults, wherever applicable.
            latestIndex = SearchIndex.objects.latest("created")
            indexUrl = reverse("searchindex-detail", request=get_current_request(), args=[latestIndex.id])
            try:
                data["index"] = indexUrl
            except:
                data = dict(data)
                data["index"] = indexUrl

        queryJson = data["queryJson"]

        if "Keywords" not in queryJson or not queryJson["Keywords"]:
            queryJson["Keywords"] = []
        elif isinstance(queryJson["Keywords"], str):
            queryJson["Keywords"] = [queryJson["Keywords"]]

        if "HasIcon" in queryJson:
            queryJson["HasIcon"] = True if queryJson["HasIcon"] else False

        if "HasImage" in queryJson:
            queryJson["HasImage"] = True if queryJson["HasImage"] else False

        queryJson["Keywords"] = [word.lower() for word in queryJson["Keywords"]]

        data["queryJson"] = queryJson

        instance = super(SearchQuerySerializer, self).to_internal_value(data)
        return instance

    @methodProfiler
    def paginated_results(self, queryObj):
        """
        The results are serialized/de-serialized using a method.
        """
        querySet = QueryResultsIteratorWithAutoInsertion(queryObj)

        paginationObj = pagination.PageNumberPagination()
        paginationObj.page_size_query_param = "page_size"
        paginationObj.page_size = 10
        paginationObj.paginate_queryset(querySet, self.context['request'])
        serializer = PaginatedSearchResultSerializer(paginationObj.page, many=True, context={'request': self.context['request'], 'paginationObj': paginationObj})
        return serializer.data


class SearchIndexSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for /search/indices.
    """
    id = serializers.IntegerField(read_only=True)
    indexType = fields.EnumSerializerField(IndexTypeChoices)

    # evalResults, being a custom model field type, needs a custom invocation of the field serializer.
    evalResults = serializers.JSONField()

    class Meta:
        model = SearchIndex
        fields = ('id', 'created', 'indexType', 'rankingSources', 'evalResults', 'schemaVersion', 'pickledModelFile')
