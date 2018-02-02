from rest_framework import serializers
from Search.models import SearchResult, SearchQuery, SearchSession

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
        fields = ('session', 'queryJson', 'created', 'results')

class SearchSessionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SearchSession
        fields = ('created',)
