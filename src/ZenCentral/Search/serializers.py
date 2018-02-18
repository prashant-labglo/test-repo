from collections import OrderedDict
from rest_framework import serializers, pagination
from Search.models import SearchResult, SearchResultRating, SearchQuery, SearchIndex
from Search.models import IndexTypeChoices
from ZenCentral import fields
from rest_framework.response import Response

from django.contrib.auth import get_user_model

class SearchResultRatingSerializer(serializers.ModelSerializer):
    #user = serializers.PrimaryKeyRelatedField(
    #    read_only=True,
    #    default=serializers.CurrentUserDefault())
    class Meta:
        model = SearchResultRating
        fields = ('rated', 'result', 'user')

class SearchResultSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    myRating = serializers.IntegerField(read_only=False)
    ratings = SearchResultRatingSerializer(many=True)
    class Meta:
        model = SearchResult
        fields = ('id', 'slide', 'rank', 'query', 'ratings', 'myRating')
        read_only_fields = ('id', 'slide', 'rank', 'query', 'ratings')

class NestedSearchResultRatingSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault())
    class Meta:
        model = SearchResultRating
        fields = ('rated', 'user')

class NestedSearchResultSerializer(serializers.ModelSerializer):
    avgRating = serializers.FloatField(read_only=True)
    myRating = serializers.IntegerField(read_only=False)
    id = serializers.IntegerField(read_only=True)
    class Meta:
        model = SearchResult
        fields = ('id', 'slide', 'avgRating', 'myRating', 'score')

class PaginatedSearchResultListSerializer(serializers.ListSerializer):
    def to_representation(self, page):
        """Convert `username` to lowercase."""
        paginationObj = self.context["paginationObj"]
        retval = OrderedDict([
            ('count', page.paginator.count),
            ('next', paginationObj.get_next_link()),
            ('previous', paginationObj.get_previous_link()),
            ('results', super().to_representation(page))
        ])
        return retval
    def to_internal_value(self, data):
        return super().to_internal_value(data["results"])

    @property
    def data(self):
        ret = super(serializers.ListSerializer, self).data
        return ret

class PaginatedSearchResultSerializer(NestedSearchResultSerializer):
    class Meta(NestedSearchResultSerializer.Meta):
        list_serializer_class=PaginatedSearchResultListSerializer

class SearchQuerySerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    # queryJSON, being a custom model field type, needs a custom invocation of the field serializer.
    queryJson = serializers.JSONField()

    # Making results read only in the API.
    results = serializers.SerializerMethodField('paginated_results')

    class Meta:
        model = SearchQuery
        fields = ('id', 'index', 'queryJson', 'created', 'results')

    def paginated_results(self, obj):
        querySet = SearchResult.objects.filter(query=obj)
        paginationObj = pagination.PageNumberPagination()
        paginationObj.page_size_query_param = "page_size"
        paginationObj.page_size = 10
        paginationObj.paginate_queryset(querySet, self.context['request'])
        serializer = PaginatedSearchResultSerializer(paginationObj.page, many=True, context={'request': self.context['request'], 'paginationObj': paginationObj})
        return serializer.data

class SearchIndexSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    indexType = fields.EnumSerializerField(IndexTypeChoices)
    class Meta:
        model = SearchIndex
        fields = ('id', 'created', 'indexType', 'rankingSources')
