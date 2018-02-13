from rest_framework import serializers
from Search.models import SearchResult, SearchResultRating, SearchQuery, SearchIndex

class SearchResultRatingSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault())
    class Meta:
        model = SearchResultRating
        fields = ('rating', 'user', 'result')

class SearchResultSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SearchResult
        fields = ('slide', 'rank')

class SearchQuerySerializer(serializers.HyperlinkedModelSerializer):
    # queryJSON, being a custom model field type, needs a custom invocation of the field serializer.
    queryJson = serializers.JSONField()

    # Making results read only in the API.
    results = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name="queryJson")
    class Meta:
        model = SearchQuery
        fields = ('index', 'queryJson', 'created', 'results')

class SearchIndexSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SearchIndex
        fields = ('created', 'searchAlgo')
