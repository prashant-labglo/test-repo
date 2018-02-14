"""
Builds a view for the slide search index. Commands can be issued over a REST API to
re-index slide-db for search.
"""
import json, os, re, sys, requests, time, threading
from rest_framework.renderers import JSONRenderer
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework import status

from LibLisa import lastCallProfile, lisaConfig, textCleanUp, methodProfiler, blockProfiler
from Search.models import SearchIndex, IndexTypeChoices
from Search.serializers import SearchIndexSerializer
from SlideDB.models import Slide, Concept, SubConcept, Construct
from SlideDB.serializers import SlideSerializer, ConceptSerializer, SubConceptSerializer, ConstructSerializer

class SearchIndexViewSet(viewsets.ModelViewSet):
    """
    Class to build a view for the slide search index. 
    Commands can be issued over a REST API to re-index slide-db for search.
    """
    queryset = SearchIndex.objects.all()
    serializer_class = SearchIndexSerializer

    def __init__(self, *argc, **kargv):
        """
        Constructor
        """
        super().__init__(*argc, **kargv)

    @detail_route(methods=['post'])
    def prepareSlideHierarchy(self, request, pk=None):
        """
        Prepare slide hierarchy in SlideDB for indexing.

        Builds self.innerIndex using the current slide hierarchy data in ZenCentral SlideDB.
        self.innerIndex can then be used to make and answer slide search queries.
        """
        searchIndexObj = SearchIndex.objects.get(pk=pk)
        if searchIndexObj is None:
            return Response("Search Index with pk={0} not found".format(pk), status=status.HTTP_404_NOT_FOUND)

        searchIndexObj.prepareSlideHierarchy()

        return Response({"status":"Done"})

    @detail_route(methods=['post', 'get'])
    def prepareTrainingData(self, request, pk=None):    
        """
        Ranking slides is done using a ML based Learning-To-Rank approach.
        This means that rankings change basde on learning.
        Now, learning requires training data. This method loads or builds the training data.
        """
        print("Starting prepareTrainingData")

        searchIndexObj = SearchIndex.objects.get(pk=pk)
        if searchIndexObj is None:
            return Response("Search Index with pk={0} not found".format(pk), status=status.HTTP_404_NOT_FOUND)

        if request.method == "POST":
            try:
                forceCreate=request.data["forceCreate"]
            except:
                forceCreate = False

            searchIndexObj.prepareTrainingData(forceCreate)
            return Response({"Done" : 1})
        elif request.method == "GET":
            return Response(searchIndexObj.getTrainingData())

    @detail_route(methods=['post', 'get'])
    def fit(self, request, pk=None):
        """
        We call this to build model parameters from training data.
        """
        print("Starting prepareTrainingData")
        searchIndexObj = SearchIndex.objects.get(pk=pk)
        if searchIndexObj is None:
            return Response("Search Index with pk={0} not found".format(pk), status=status.HTTP_404_NOT_FOUND)

        if request.method == "POST":
            searchIndexObj.fit()
            return Response({"Done" : 1})
        elif request.method == "GET":
            return Response(searchIndexObj.backend.innerIndex.json())
