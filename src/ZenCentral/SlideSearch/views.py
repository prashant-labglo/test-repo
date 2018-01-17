from rest_framework import viewsets
from SlideSearch.models import SearchResult, SearchQuery, SearchSession
from SlideSearch.serializers import SearchResultSerializer, SearchQuerySerializer, SearchSessionSerializer
from django.shortcuts import render

# Create your views here.
class SearchResultViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows SearchResults to be viewed or edited.
    """
    queryset = SearchResult.objects.all()
    serializer_class = SearchResultSerializer

class SearchQueryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows SearchQuerys to be viewed or edited.
    """
    queryset = SearchQuery.objects.all()
    serializer_class = SearchQuerySerializer

class SearchSessionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows SearchSessions to be viewed or edited.
    """
    queryset = SearchSession.objects.all()
    serializer_class = SearchSessionSerializer
