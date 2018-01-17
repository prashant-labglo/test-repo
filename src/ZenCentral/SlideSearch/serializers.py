from rest_framework import serializers
from SlideSearch.models import SearchResult, SearchQuery, SearchSession

class SearchResultSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SearchResult
        fields = ('slide', 'rank')

class SearchQuerySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SearchQuery
        fields = ('session', 'queryJson', 'created', 'results')

class SearchSessionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SearchSession
        fields = ('created',)
