from rest_framework import viewsets
from SlideDB.models import Concept, SubConcept, Construct, Slide
from SlideDB.serializers import ConceptSerializer, SubConceptSerializer, ConstructSerializer, SlideSerializer
from django.shortcuts import render

# Create your views here.
class ConceptViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows concepts to be viewed or edited.
    """
    queryset = Concept.objects.all()
    serializer_class = ConceptSerializer

class SubConceptViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows subConcepts to be viewed or edited.
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
