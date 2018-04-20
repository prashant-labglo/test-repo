from rest_framework import viewsets
from rest_framework import status

from django.shortcuts import get_object_or_404

from Search.models import SearchResult, SearchResultRating, SearchQueryInvocation, SearchIndex, SearchQuery

from Search.serializers import (
    NestedSearchResultSerializer, SearchResultSerializer, SearchResultRatingSerializer, SearchQueryInvocationSerializer,
    SearchIndexSerializer, UpsertingOnPostResultRatingSerializer, SearchQuerySerializer
)
from ZenCentral.views import profiledModelViewSet
from LibLisa import lastCallProfile, lisaConfig, methodProfiler, blockProfiler


class SearchResultRatingViewSet(profiledModelViewSet):
    """
    API endpoint that allows SearchResults to be viewed or edited.
    """
    queryset = SearchResultRating.objects.all()

    def get_serializer_class(self):
        return UpsertingOnPostResultRatingSerializer if self.request.method == 'POST' else SearchResultRatingSerializer

    def perform_create(self, serializer):
        """
        Method to override the post request to update if the object present or to create new object.
        """
        result = serializer.validated_data['result']
        result_obj = get_object_or_404(SearchResult, id=result)
        qset = SearchResultRating.objects.filter(
            user=self.request.user, slide=result_obj.slide, query=result_obj.queryInvocation.query
        )
        if qset:
            qset[0].rated = serializer.data['rated']
            qset[0].save()
        else:
            serializer.save(user=self.request.user)

    # Post list route.
    # When a query is made, the search results are created and returned.


class SearchResultViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows SearchResults to be viewed or edited.
    """
    queryset = SearchResult.objects.all()
    serializer_class = SearchResultSerializer

    # Post list route.
    # When a query is made, the search results are created and returned.


class SearchQueryInvocationViewSet(profiledModelViewSet):
    """
    API endpoint that allows SearchQuerys to be viewed or edited.
    """
    queryset = SearchQueryInvocation.objects.all()
    serializer_class = SearchQueryInvocationSerializer

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
                queryObj = SearchQueryInvocation.objects.get(pk=retval.data["id"])
                searchIndex = queryObj.index
                queryObj.resultJson = searchIndex.slideSearch(queryObj)
                queryObj.save()

            with blockProfiler("create.SerializeSearchResults"):
                # QueryObj may have now changed.
                queryObj = SearchQueryInvocation.objects.get(pk=retval.data["id"])

                # Update retval with new data and return.
                retval.data = SearchQueryInvocationSerializer(queryObj, context={'request': request}).data

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


class SearchQueryViewSet(profiledModelViewSet):
    """
    API endpoint that allows SearchQuerys to be viewed or edited.
    """

    queryset = SearchQuery.objects.all()
    serializer_class = SearchQuerySerializer
