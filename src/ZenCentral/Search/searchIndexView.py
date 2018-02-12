"""
Builds a view for the slide search index. Commands can be issued over a REST API to
re-index slide-db for search.
"""
import json, os, re, sys, requests, time, threading
from rest_framework.renderers import JSONRenderer
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from LibLisa import lastCallProfile, lisaConfig, textCleanUp, methodProfiler, blockProfiler
from SlideSearch import Word2vecDistanceModel, SlideSearchW2V, SlideSearchLambdaMart
from Search.models import SearchIndex
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

    # Class level config section.
    trainingDataFilePath = lisaConfig.dataFolderPath + "trainingData.json"

    # Model to find word distances using word2vec.
    word2vecDistanceModel = Word2vecDistanceModel()
    print("Profiling data for building Word2vecDistanceModel:\n {0}".format(json.dumps(lastCallProfile(), indent=4)))

    # Initialize inner index to None.
    innerIndex = None
    Tx = None
    Ty = None
    Tqids = None
    fittingDone = None

    def __init__(self, *argc, **kargv):
        """
        Constructor
        """
        super().__init__(*argc, **kargv)

    @list_route(methods=['post'])
    def prepareSlideHierarchy(self, request, pk=None):
        """
        Prepare slide hierarchy in SlideDB for indexing.

        Builds self.innerIndex using the current slide hierarchy data in ZenCentral SlideDB.
        self.innerIndex can then be used to make and answer slide search queries.
        """
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
        SearchIndexViewSet.dataForIndexing = dataForIndexing
        SearchIndexViewSet.innerIndex = SlideSearchLambdaMart(dataForIndexing, lisaConfig.slideSearch, self.word2vecDistanceModel)
        print("Inner index prepared.")
        return Response({"Done" : 1})

    @list_route(methods=['post', 'get'])
    def prepareTrainingData(self, request, pk=None):
        """
        Ranking slides is done using a ML based Learning-To-Rank approach.
        This means that rankings change basde on learning.
        Now, learning requires training data. This method loads or builds the training data.
        """
        print("Starting prepareTrainingData")
        if request.method == "POST":
            try:
                forceCreate=request.data["forceCreate"]
            except:
                forceCreate = False

            if self.innerIndex is None:
                self.prepareSlideHierarchy(request, pk)

            if forceCreate or not(os.path.exists(self.trainingDataFilePath)):
                # Training data does not exist. Must be created from scratch.
                slideSearchIndexSeed = SlideSearchW2V(
                    self.dataForIndexing,
                    lisaConfig.slideSearch,
                    self.word2vecDistanceModel)
                (Tx, Ty, Tqids, TresultIds) = self.innerIndex.buildSeedTrainingSet(slideSearchIndexSeed)
                with open(self.trainingDataFilePath, "w") as fp:
                    json.dump({"Tx":Tx, "Ty":Ty, "Tqids":Tqids, "TresultIds":TresultIds}, fp, indent=4)
                (SearchIndexViewSet.Tx, SearchIndexViewSet.Ty, SearchIndexViewSet.Tqids, SearchIndexViewSet.TresultIds) = (Tx, Ty, Tqids, TresultIds)
            else:
                trainingData = json.load(open(self.trainingDataFilePath, "r"))
                (SearchIndexViewSet.Tx, SearchIndexViewSet.Ty, SearchIndexViewSet.Tqids, SearchIndexViewSet.TresultIds) = (trainingData["Tx"], trainingData["Ty"], trainingData["Tqids"], trainingData["TresultIds"])
            return Response({"Done" : 1})
        elif request.method == "GET":
            if SearchIndexViewSet.Tx is None:
                return Response({"Status" : "Not Loaded"})
            else:
                retval = []
                for i in range(len(SearchIndexViewSet.Tx)):
                    retval.append({
                            "Tqids" : SearchIndexViewSet.Tqids[i],
                            "Tx": SearchIndexViewSet.Tx[i],
                            "Ty": SearchIndexViewSet.Ty[i],
                            "TresultIds": SearchIndexViewSet.TresultIds[i]})
                with open(lisaConfig.dataFolderPath + "trainingDataFormatted.json", "w") as fp:
                    json.dump(retval, fp, indent=4)
                return Response(retval)
    @list_route(methods=['post', 'get'])
    def fit(self, request, pk=None):
        """
        We call this to build model parameters from training data.
        """
        print("Starting prepareTrainingData")
        if request.method == "POST":
            if self.Tx is None:
                self.prepareTrainingData(request, pk)
            # LambdaMART index is now trained using the training data.
            SearchIndexViewSet.innerIndex.fit(self.Tx, self.Ty, self.Tqids)
            SearchIndexViewSet.fittingDone = True
            return Response({"Done" : 1})
        elif request.method == "GET":
            return Response(SearchIndexViewSet.innerIndex.json())

    @list_route(methods=['post'])
    def query(self, request, pk=None):
        """
        We call this to build model parameters from training data.
        """
        if self.fittingDone is None:
            self.fit(request, pk)

        queryInfo = request.data
        if not queryInfo:
            queryInfo = {"Keywords" : ["Agenda"]}

        queryInfo = textCleanUp(queryInfo)

        if "count" not in queryInfo.keys():
            queryInfo["count"] = 500

        result = self.innerIndex.slideSearch(queryInfo)

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
