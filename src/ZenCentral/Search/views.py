from rest_framework import viewsets
from Search.models import SearchResult, SearchQuery, SearchSession
from Search.serializers import SearchResultSerializer, SearchQuerySerializer, SearchSessionSerializer
from django.shortcuts import render
from Search.searchIndex import slideSearchIndex

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

class SearchSessionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows SearchSessions to be viewed or edited.
    """
    queryset = SearchSession.objects.all()
    serializer_class = SearchSessionSerializer
