"""
Builds a view for the slide search index. Commands can be issued over a REST API to
re-index slide-db for search.
"""
import json, os, re, sys, requests, time, threading
from django.core.cache import cache, caches
from cachetools import LRUCache
from rest_framework.renderers import JSONRenderer
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework import status

from LibLisa import lastCallProfile, lisaConfig, textCleanUp, methodProfiler, blockProfiler
from SlideSearch import Word2vecDistanceModel, SlideSearchW2V, SlideSearchLambdaMart
from Search.models import SearchIndex, IndexTypeChoices
from Search.serializers import SearchIndexSerializer
from SlideDB.models import Slide, Concept, SubConcept, Construct
from SlideDB.serializers import SlideSerializer, ConceptSerializer, SubConceptSerializer, ConstructSerializer

def getSearchIndexInstance(pk, tryCreate=False):
    key = "Search Index {0}".format(pk)
    modelInstance = SearchIndexViewSet.searchIndexCache.get(key)
    if modelInstance is not None:
        # Set initial cached attributes.
        if "innerIndex" not in modelInstance.__dict__.keys():
            modelInstance.innerIndex = None
            modelInstance.Tx = None
            modelInstance.Ty = None
            modelInstance.Tqids = None
            modelInstance.fittingDone = None

        return modelInstance
    else:
        modelInstance = SearchIndex.objects.get(pk=pk)
        if modelInstance is None and tryCreate:
            modelInstance = SearchIndex()

        if modelInstance is not None:
            # Set initial cached attributes.
            modelInstance.innerIndex = None
            modelInstance.Tx = None
            modelInstance.Ty = None
            modelInstance.Tqids = None
            modelInstance.fittingDone = None

            SearchIndexViewSet.searchIndexCache[key] = modelInstance

            return modelInstance
        else:
            return None

class SearchIndexViewSet(viewsets.ModelViewSet):
    """
    Class to build a view for the slide search index. 
    Commands can be issued over a REST API to re-index slide-db for search.
    """
    queryset = SearchIndex.objects.all()
    serializer_class = SearchIndexSerializer

    # Model to find word distances using word2vec.
    word2vecDistanceModel = Word2vecDistanceModel()
    print("Profiling data for building Word2vecDistanceModel:\n {0}".format(json.dumps(lastCallProfile(), indent=4)))

    # Initialize inner index to None.
    searchIndexCache = LRUCache(maxsize=3)

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
        searchIndexInstance = getSearchIndexInstance(pk)
        if searchIndexInstance is None:
            return Response("Search Index with pk={0} not found".format(pk), status=status.HTTP_404_NOT_FOUND)

        # Build data to index.
        dataForIndexing = {}
        print("Starting prepareSlideHierarchy")
        for (model, serializer) in [
            (Slide, SlideSerializer), 
            (Concept, ConceptSerializer), 
            (SubConcept, SubConceptSerializer), 
            (Construct, ConstructSerializer)
        ]:
            # serializedData = serializer(model.objects.all(), many=True, context={'request': request}).data
            dataForIndexing[model.__name__ + "s"] = model.objects.all()

        print("Data to index extracted.")

        # Slide search using LambdaMART.
        lisaConfig.slideSearch.isDjangoModel = True
        searchIndexInstance.dataForIndexing = dataForIndexing
        searchIndexInstance.innerIndex = SlideSearchLambdaMart(
            dataForIndexing,
            lisaConfig.slideSearch,
            self.word2vecDistanceModel)
        print("Inner index prepared.")
        return Response({"Done" : 1})

    @detail_route(methods=['post', 'get'])
    def prepareTrainingData(self, request, pk=None):    
        """
        Ranking slides is done using a ML based Learning-To-Rank approach.
        This means that rankings change basde on learning.
        Now, learning requires training data. This method loads or builds the training data.
        """
        print("Starting prepareTrainingData")

        searchIndexInstance = getSearchIndexInstance(pk)
        if searchIndexInstance is None:
            return Response("Search Index with pk={0} not found".format(pk), status=status.HTTP_404_NOT_FOUND)

        # Find the location of file to save.
        trainingDataFilePath = lisaConfig.dataFolderPath + "{0}/trainingData.json".format(pk)
        os.makedirs(os.path.dirname(trainingDataFilePath), exist_ok=True)

        if request.method == "POST":
            try:
                forceCreate=request.data["forceCreate"]
            except:
                forceCreate = False

            if searchIndexInstance.innerIndex is None:
                self.prepareSlideHierarchy(request, pk)

            if forceCreate or not(os.path.exists(trainingDataFilePath)):
                # Training data does not exist. Must be created from scratch.
                slideSearchIndexSeed = SlideSearchW2V(
                    searchIndexInstance.dataForIndexing,
                    lisaConfig.slideSearch,
                    self.word2vecDistanceModel)
                (Tx, Ty, Tqids, TresultIds) = searchIndexInstance.innerIndex.buildSeedTrainingSet(slideSearchIndexSeed)
                with open(trainingDataFilePath, "w") as fp:
                    json.dump(
                        {"Tx":Tx, "Ty":Ty, "Tqids":Tqids, "TresultIds":TresultIds},
                        fp,
                        indent=4)
                searchIndexInstance.Tx = Tx
                searchIndexInstance.Ty = Ty
                searchIndexInstance.Tqids = Tqids
                searchIndexInstance.TresultIds = TresultIds
            else:
                trainingData = json.load(open(trainingDataFilePath, "r"))
                searchIndexInstance.Tx = trainingData["Tx"]
                searchIndexInstance.Ty = trainingData["Ty"]
                searchIndexInstance.Tqids = trainingData["Tqids"]
                searchIndexInstance.TresultIds = trainingData["TresultIds"]
            return Response({"Done" : 1})
        elif request.method == "GET":
            if searchIndexInstance.Tx is None:
                return Response({"Status" : "Not Loaded"})
            else:
                retval = []
                for i in range(len(searchIndexInstance.Tx)):
                    retval.append({
                            "Tqids" : searchIndexInstance.Tqids[i],
                            "Tx": searchIndexInstance.Tx[i],
                            "Ty": searchIndexInstance.Ty[i],
                            "TresultIds": searchIndexInstance.TresultIds[i]})
                with open(lisaConfig.dataFolderPath + "trainingDataFormatted.json", "w") as fp:
                    json.dump(retval, fp, indent=4)
                return Response(retval)

    @detail_route(methods=['post', 'get'])
    def fit(self, request, pk=None):
        """
        We call this to build model parameters from training data.
        """
        print("Starting prepareTrainingData")
        searchIndexInstance = getSearchIndexInstance(pk)
        if searchIndexInstance is None:
            return Response("Search Index with pk={0} not found".format(pk), status=status.HTTP_404_NOT_FOUND)

        if request.method == "POST":
            if searchIndexInstance.Tx is None:
                self.prepareTrainingData(request, pk)
            # LambdaMART index is now trained using the training data.
            searchIndexInstance.innerIndex.fit(self.Tx, self.Ty, self.Tqids)
            searchIndexInstance.fittingDone = True
            return Response({"Done" : 1})
        elif request.method == "GET":
            return Response(searchIndexInstance.innerIndex.json())

    @detail_route(methods=['post'])
    def query(self, request, pk=None):
        """
        We call this to build model parameters from training data.
        """
        searchIndexInstance = getSearchIndexInstance(pk)
        if searchIndexInstance is None:
            return Response("Search Index with pk={0} not found".format(pk), status=status.HTTP_404_NOT_FOUND)

        if searchIndexInstance.fittingDone is None:
            self.fit(request, pk)

        queryInfo = request.data
        if not queryInfo:
            queryInfo = {"Keywords" : ["Agenda"]}

        queryInfo = textCleanUp(queryInfo)

        if "count" not in queryInfo.keys():
            queryInfo["count"] = 500

        result = searchIndexInstance.innerIndex.slideSearch(queryInfo)

        resultCurated = []
        for (index, (score, slide)) in enumerate(result):
            curatedSlide = { "id":slide.id, "KeywordsFound":[]}
            tags = slide.tags.names()
            for keyword in queryInfo["Keywords"]:
                if keyword in tags:
                    curatedSlide["KeywordsFound"].append(keyword)
            resultCurated.append((score, curatedSlide))
            if index >= queryInfo["count"]:
                break

        with open(lisaConfig.dataFolderPath + "queryResponse.json", "w") as fp:
            json.dump({"query":request.data, "result":resultCurated}, fp, indent=4)
        return Response(resultCurated)