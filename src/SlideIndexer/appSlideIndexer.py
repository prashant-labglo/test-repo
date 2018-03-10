"""
Slide Indexer periodically wakes up and downloads latest slide hierarchy from LisaZepto.
All modified slides are then uploaded into ZenCentral SlideDB service.
"""

import threading, time, json, os, random
from attrdict import AttrDict
from LibLisa import lisaConfig, blockProfiler, lastCallProfile
from SlideIndexer.SearchClient import SearchClient
from SlideIndexer.SlideDbClient import SlideDbClient
from SlideIndexer.LisaZeptoClient import LisaZeptoClient

from SlideSearch import SlideSearchW2V, SlideSearchLambdaMart, getSlideRatingVecs

# Instantiate REST clients.
slideDbClient = SlideDbClient()
searchClient = SearchClient()

def searchIndexCreatorThreadFunc():
    """
    Downloads data from Lisa Zepto.
    Uploads the same into ZenClient SlideDB REST API.
    Removes any entries from ZenClient SlideDB REST API which are not found in downloaded
    Lisa Zepto.
    """
    # Login into REST clients.
    slideDbClient.login()
    searchClient.login()

    # Main loop.
    while True:
        # Get all changes made since last update.
        dataForIndexing = slideDbClient.getSlideHierarchy()

        # Slide search using LambdaMART.
        slideSearchIndex = SlideSearchLambdaMart(dataForIndexing, lisaConfig.slideIndexer)

        # Collate slides rating data from the server.
        slideRatingsData = searchClient.getSlideRatingsData(dataForIndexing)
        with open(lisaConfig.slideRatingsDataFilePath, "w") as fp:
            json.dump(slideRatingsData, fp, indent=4)

        # If slide ratings data quantity is small, simulate it.
        if len(slideRatingsData) < 1000:
            indexType = "SimulatedRatings"

            # Generate slide ratings data, unless available from cached file.
            cachedFilePath = lisaConfig.simulatedSlideRatingsDataFilePath
            if cachedFilePath is None or not os.path.exists(cachedFilePath):
                slideSearchIndexSeed = SlideSearchW2V(dataForIndexing, lisaConfig.slideIndexer)
                slideRatingsData = slideSearchIndex.buildSeedTrainingSet(slideSearchIndexSeed)
                if cachedFilePath is not None:
                    with open(cachedFilePath, "w") as fp:
                        json.dump(slideRatingsData, fp, indent=4)
            else:
                with open(cachedFilePath, "r") as fp:
                    slideRatingsData = json.load(fp)
            rankingSources = [] 
        else:
            indexType = "UserRatings"
            rankingSources = [queryObj["id"] for queryObj in slideRatingsData]

        # Convert ratings data into (Tx, Ty, Tqids and TresultIds)
        slideRatingVecs = getSlideRatingVecs(slideSearchIndex, slideRatingsData, dataForIndexing)

        # Now train LambdaMART index using the ratings data.
        evalResults = slideSearchIndex.fit(slideRatingVecs)

        # Upload the slide search index.
        searchClient.uploadSlideSearchIndex(slideSearchIndex, indexType, rankingSources, evalResults)

        # Sleep for iteration period, before trying again.
        time.sleep(lisaConfig.slideIndexer.IterationPeriod)

searchIndexCreatorThreadFunc()
