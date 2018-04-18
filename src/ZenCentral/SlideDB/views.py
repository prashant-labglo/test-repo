from rest_framework import viewsets
from rest_framework.response import Response
from SlideDB.models import Concept, SubConcept, Construct, Slide
from SlideDB.serializers import ConceptSerializer, SubConceptSerializer, ConstructSerializer, SlideSerializer


class ConceptViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows concepts to be viewed or edited.
    """
    queryset = Concept.objects.filter(enabled=True)
    serializer_class = ConceptSerializer

    def list(self, request, *args, **kwargs):
        """
        List method override to get the all slides from database.
        This method is using in creating the indexer.
        """

        qset = Concept.objects.all()
        queryset = self.filter_queryset(qset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SubConceptViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows concepts to be viewed or edited.
    """
    queryset = SubConcept.objects.all()
    serializer_class = SubConceptSerializer


class ConstructViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows constructs to be viewed or edited.
    """
    queryset = Construct.objects.all()
    serializer_class = ConstructSerializer


class SlideViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows slides to be viewed or edited.
    """
    queryset = Slide.objects.all()
    serializer_class = SlideSerializer
