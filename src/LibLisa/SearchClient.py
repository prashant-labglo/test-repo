"""
Slide search client is a REST API client which can make search queries to ZenCentral REST API for slide search.
"""
import tempfile, pickle
from LibLisa.behaviors import Behavior
from LibLisa.CoreApiRestClient import CoreApiRestClient
from LibLisa.config import lisaConfig
from coreapi.utils import File as CoreApiFile

class SearchClient(CoreApiRestClient):
    """
    SearchClient is a REST API client which can make search queries to ZenCentral REST API for slide search.
    """
    def __init__(self):
        """
        Constructor
        """
        super().__init__(lisaConfig.slideSearch)

    def getSlideRatingsData(self, slideHierarchy, ratedResultsCountMin=20):
        """
        Get ratings data from the slide search client. 
        """
        queryObjects = self.getModelInstances("queries")
        for queryObject in queryObjects:
            queryObject["results"] = []

        queryObjectsDict = {queryObject["id"]:queryObject for queryObject in queryObjects }
        resultObjects = self.getModelInstances("results")

        slideObjectsDict = {slideObject["id"]:slideObject for slideObject in slideHierarchy["Slides"] }

        resultObjectsDict = {}
        for resultObject in resultObjects:
            # Replace slide id with slide dict.
            slideId = resultObject["slide"]
            resultObject["slide"] = slideObjectsDict[slideId]

            # Append result to result array in resultObjects.
            queryId = resultObject["query"]
            queryObject = queryObjectsDict[queryId]
            assert(len(queryObject["results"]) == resultObject["rank"])
            queryObject["results"].append(resultObject)

        qualifiedQueries = []
        for queryObject in queryObjects:
            ratedResultsRun = 0
            for resultObject in queryObject["results"]:
                if resultObject["avgRating"] is None:
                    break
                else:
                    ratedResultsRun += 1
            if ratedResultsRun >= ratedResultsCountMin:
                qualifiedQueries.append(queryObject)

        return qualifiedQueries

    def uploadSlideSearchIndex(self, slideSearchIndex, indexType, rankingSources):
        slideSearchIndexFilename = lisaConfig.dataFolderPath + "slideSearchIndex.pkl"
        with open(slideSearchIndexFilename, "wb") as fp:
            pickle.dump(slideSearchIndex, fp)

        with open(slideSearchIndexFilename, "rb") as fp:
            retval = self.client.action(
                self.schema, 
                [self.config.appName, 'indices', 'create'], 
                params={
                    "indexType":indexType,
                    "rankingSources" : rankingSources,
                    "schemaVersion" : 0,
                    "pickedModelFile" : fp,
                    },
                encoding="multipart/form-data")

        return retval
