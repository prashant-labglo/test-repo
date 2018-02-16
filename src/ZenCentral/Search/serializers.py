from rest_framework import serializers
from Search.models import SearchResult, SearchResultRating, SearchQuery, SearchIndex
from Search.models import IndexTypeChoices
from ZenCentral import fields

from django.contrib.auth import get_user_model

class SearchResultRatingSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault())
    class Meta:
        model = SearchResultRating
        fields = ('rated', 'user', 'result')

class SearchResultSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    myRating = serializers.IntegerField(read_only=False)
    class Meta:
        model = SearchResult
        fields = ('id', 'slide', 'rank', 'query', 'ratings', 'myRating')
        read_only_fields = ('id', 'slide', 'rank', 'query', 'ratings')

class NestedSearchResultRatingSerializer(serializers.ModelSerializer):
    #user = serializers.PrimaryKeyRelatedField(
    #    read_only=True,
    #    default=serializers.CurrentUserDefault())
    class Meta:
        model = SearchResultRating
        fields = ('rated', 'user')

class NestedSearchResultSerializer(serializers.ModelSerializer):
    avgRating = serializers.FloatField(read_only=True)
    myRating = serializers.IntegerField(read_only=False)
    id = serializers.IntegerField(read_only=True)
    def __init__(self, *argv, **kargv):
        super().__init__(*argv, **kargv)
    class Meta:
        model = SearchResult
        fields = ('id', 'slide', 'avgRating', 'myRating', 'score')

class SearchQuerySerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    # queryJSON, being a custom model field type, needs a custom invocation of the field serializer.
    queryJson = serializers.JSONField()

    # Making results read only in the API.
    results = NestedSearchResultSerializer(many=True, read_only=True)

    class Meta:
        model = SearchQuery
        fields = ('id', 'index', 'queryJson', 'created', 'results')

class SearchIndexSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    indexType = fields.EnumSerializerField(IndexTypeChoices)
    class Meta:
        model = SearchIndex
        fields = ('id', 'created', 'indexType', 'rankingSources')
