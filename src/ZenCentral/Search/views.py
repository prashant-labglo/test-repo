from rest_framework import viewsets
from Search.models import SearchResult, SearchResultRating, SearchQuery
from Search.serializers import SearchResultSerializer, SearchResultRatingSerializer, SearchQuerySerializer
from Search.searchIndexView import SearchIndexViewSet

from django.shortcuts import render

# Create your views here.
class SearchResultRatingViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows SearchResults to be viewed or edited.
    """
    queryset = SearchResultRating.objects.all()
    serializer_class = SearchResultRatingSerializer

    # Post list route.
    # When a query is made, the search results are created and returned.

# Create your views here.
class SearchResultViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows SearchResults to be viewed or edited.
    """
    queryset = SearchResult.objects.all()
    serializer_class = SearchResultSerializer

    # Post list route.
    # When a query is made, the search results are created and returned.

class SearchQueryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows SearchQuerys to be viewed or edited.
    """
    queryset = SearchQuery.objects.all()
    serializer_class = SearchQuerySerializer

    def create(self, request):
        # import pdb;pdb.set_trace()

        # Populate results field with actual results.
        #queryJson = request.data["queryJson"]
        #resultList = [SearchResult(result) for result in slideSearchIndex.slideSearch(queryJson)]
        #request.data["results"] = resultList

        # Create the query instance by calling parent method.
        super().create(self, request)