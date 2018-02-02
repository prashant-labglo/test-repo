"""
Builds a view for the slide search index. Commands can be issued over a REST API to
re-index slide-db for search.
"""
import json, os, re, sys, requests, time, threading
from rest_framework.renderers import JSONRenderer

from LibLisa import lastCallProfile, lisaConfig
from SlideSearch import Word2vecDistanceModel, SlideSearchW2V, SlideSearchLambdaMart
from SlideDB.models import Slide, Concept, SubConcept, Construct
from SlideDB.serializers import SlideSerializer, ConceptSerializer, SubConceptSerializer, ConstructSerializer

class SearchIndex(object):
    """
    Class to build a view for the slide search index. 
    Commands can be issued over a REST API to re-index slide-db for search.
    """
    def __init__(self):
        """
        Constructor
        """
        self.word2vecDistanceModel = Word2vecDistanceModel()
        # Model to find word distances using word2vec.
        print("Profiling data for building Word2vecDistanceModel:\n {0}".format(json.dumps(lastCallProfile(), indent=4)))

        # See if we have already created training data.
        self.trainingDataFilePath = lisaConfig.dataFolderPath + "trainingData.json"

        self.innerIndex = None

    def indexCurrentSnapshot(request):
        """
        Builds self.innerIndex using the current slide hierarchy data in ZenCentral SlideDB.
        self.innerIndex can then be used to make and answer slide search queries.
        """
        # Build data to index.
        dataToIndex = {}
        for (model, serializer) in [
            (Slide, SlideSerializer), 
            (Concept, ConceptSerializer), 
            (SubConcept, SubConceptSerializer), 
            (Construct, ConstructSerializer)
        ]:
            serializedData = serializer(model.objects.all(), many=True, context={'request': request}).data
            dataToIndex[model.__name__ + "s"] = JSONRenderer().render(serializedData)

        # Slide search using LambdaMART.
        self.innerIndex = SlideSearchLambdaMart(dataToIndex, lisaConfig.slideSearch, self.word2vecDistanceModel)

        self.loadTrainingData()

    def loadTrainingData(self, forceCreate=False):
        """
        Ranking slides is done using a ML based Learning-To-Rank approach.
        This means that rankings change basde on learning.
        Now, learning requires training data. This method loads or builds the training data.
        """
        if forceCreate or not(os.path.exists(self.trainingDataFilePath)):
            # Training data does not exist. Must be created from scratch.
            slideSearchIndexSeed = SlideSearchW2V(self.dataToIndex, self.config, self.word2vecDistanceModel)
            (self.Tx, self.Ty, self.Tqids) = slideSearchIndex.buildSeedTrainingSet(slideSearchIndexSeed)
            with open(trainingDataFilePath, "w") as fp:
                json.dump({"Tx":Tx, "Ty":Ty, "Tqids":Tqids}, fp, indent=4)
        else:
            trainingData = json.load(open(self.trainingDataFilePath, "r"))
            (self.Tx, self.Ty, self.Tqids) = (trainingData["Tx"], trainingData["Ty"], trainingData["Tqids"])

    def fit(self):
        """
        We call this to build model parameters from training data.
        """
        # LambdaMART index is now trained using the training data.
        self.innerIndex.fit(self.Tx, self.Ty, self.Tqids)

slideSearchIndex = SearchIndex()
