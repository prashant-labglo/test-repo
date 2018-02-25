import json
from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from Search.models import SearchResult, SearchResultRating, SearchQuery, SearchIndex
from SlideDB.models import Slide
from Search.serializers import NestedSearchResultSerializer, SearchResultSerializer, SearchResultRatingSerializer, SearchQuerySerializer, SearchIndexSerializer
from ZenCentral.views import profiledModelViewSet
from LibLisa import lastCallProfile, lisaConfig, textCleanUp, methodProfiler, blockProfiler

from django.shortcuts import render

# Create your views here.
class SearchResultRatingViewSet(profiledModelViewSet):
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

class SearchQueryViewSet(profiledModelViewSet):
    """
    API endpoint that allows SearchQuerys to be viewed or edited.
    """
    queryset = SearchQuery.objects.all()
    serializer_class = SearchQuerySerializer

    @methodProfiler
    def create(self, request):
        """
        Method called when we are create a query instance using a POST method.
        """
        # Create the query instance by calling parent method.
        queryJson = request.data

        with blockProfiler("create.InsertSearchQuery"):
            retval = super().create(request)
        if retval.status_code != status.HTTP_201_CREATED:
            return retval
        else:
            with blockProfiler("create.GetSearchResults"):
                queryObj = SearchQuery.objects.get(pk=retval.data["id"])
                searchIndex = queryObj.index
                queryObj.resultJson = searchIndex.slideSearch(queryObj)
                queryObj.save()

            with blockProfiler("create.SerializeSearchResults"):
                # QueryObj may have now changed.
                queryObj = SearchQuery.objects.get(pk=retval.data["id"])

                # Update retval with new data and return.
                retval.data = SearchQuerySerializer(queryObj, context={'request': request}).data

                # Next and previous URLs in the pagination class work for GET queries.
                # However, they are incorrect for post queries.
                # A "slight" hack to modify these links so that they work for the current POST query.
                paginatedResults = retval.data["results"]
                if paginatedResults["next"] is not None:
                    paginatedResults["next"] = paginatedResults["next"].replace("?", str(queryObj.id) + "/?")
                if paginatedResults["previous"] is not None:
                    paginatedResults["previous"] = paginatedResults["previous"].replace("?", str(queryObj.id) + "/?")
            return retval

class SearchIndexViewSet(profiledModelViewSet):
    """
    Class to build a view for the slide search index. 
    Commands can be issued over a REST API to re-index slide-db for search.
    """
    queryset = SearchIndex.objects.all()
    serializer_class = SearchIndexSerializer
