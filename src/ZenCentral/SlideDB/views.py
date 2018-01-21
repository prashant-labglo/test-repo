from rest_framework import viewsets
from SlideDB.models import Concept, SlideType, Slide
from SlideDB.serializers import ConceptSerializer, SlideTypeSerializer, SlideSerializer
from django.shortcuts import render

# Create your views here.
class ConceptViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows concepts to be viewed or edited.
    """
    queryset = Concept.objects.all()
    serializer_class = ConceptSerializer

class SlideTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows slideTypes to be viewed or edited.
    """
    queryset = SlideType.objects.all()
    serializer_class = SlideTypeSerializer

class SlideViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows slides to be viewed or edited.
    """
    queryset = Slide.objects.all()
    serializer_class = SlideSerializer
