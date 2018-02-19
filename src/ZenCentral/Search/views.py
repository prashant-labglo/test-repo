import json
from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from Search.models import SearchResult, SearchResultRating, SearchQuery
from Search.serializers import NestedSearchResultSerializer, SearchResultSerializer, SearchResultRatingSerializer, SearchQuerySerializer
from Search.searchIndexView import SearchIndexViewSet
from LibLisa import lastCallProfile, lisaConfig, textCleanUp, methodProfiler, blockProfiler

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
        """
        Method called when we are create a query instance using a POST method.
        """
        # Create the query instance by calling parent method.
        queryJson = request.data

        retval = super().create(request)
        if retval.status_code != status.HTTP_201_CREATED:
            return retval
        else:
            queryObj = SearchQuery.objects.get(pk=retval.data["id"])

            searchIndexBackend = queryObj.index.backend

            if searchIndexBackend.fittingDone is None:
                queryObj.index.fit()

            result = searchIndexBackend.innerIndex.slideSearch(queryObj.queryJson)

            for (index, (score, slide)) in enumerate(result):
                searchResult = SearchResult(slide=slide, rank=index, query=queryObj, score=score)
                searchResult.save()

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