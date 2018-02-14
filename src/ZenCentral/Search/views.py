import json
from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from Search.models import SearchResult, SearchResultRating, SearchQuery
from Search.serializers import SearchResultSerializer, SearchResultRatingSerializer, SearchQuerySerializer
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
        # Create the query instance by calling parent method.
        retval = super().create(request)
        if retval.status_code != status.HTTP_201_CREATED:
            return retval
        else:
            queryObj = SearchQuery.objects.get(pk=retval.data["id"])

            searchIndexBackend = queryObj.index.backend

            if searchIndexBackend.fittingDone is None:
                queryObj.index.fit()

            if "count" not in queryObj.queryJson.keys():
                queryObj.queryJson["count"] = 500
                queryObj.save()

            result = searchIndexBackend.innerIndex.slideSearch(queryObj.queryJson)

            resultCurated = []
            for (index, (score, slide)) in enumerate(result):
                curatedSlide = { "id":slide.id, "KeywordsFound":[]}
                tags = slide.tags.names()
                for keyword in queryObj.queryJson["Keywords"]:
                    if keyword in tags:
                        curatedSlide["KeywordsFound"].append(keyword)
                resultCurated.append((score, curatedSlide))
                if index >= queryObj.queryJson["count"]:
                    break

            with open(lisaConfig.dataFolderPath + "queryResponse.json", "w") as fp:
                json.dump({"query":request.data, "result":resultCurated}, fp, indent=4)
            return Response(resultCurated)