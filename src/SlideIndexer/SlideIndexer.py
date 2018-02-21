"""
Slide Indexer periodically wakes up and downloads latest slide hierarchy from LisaZepto.
All modified slides are then uploaded into ZenCentral SlideDB service.
"""

import threading, time, json, os
from attrdict import AttrDict
from LibLisa import lisaConfig, LisaZeptoClient, SlideDbClient, SearchClient, blockProfiler, lastCallProfile
from SlideSearch import Word2vecDistanceModel, SlideSearchW2V, SlideSearchLambdaMart

# Instantiate REST clients.
slideDbClient = SlideDbClient()
searchClient = SearchClient()

def getSlideRatingVecs(slideSearchIndex, slideRatingsData, slideHierarchy):
    (Tx, Ty, Tqids, TresultIds) = ([], [], [], [])
    for (index, ratedQuery) in enumerate(slideRatingsData):
        print("{0}: Processing query({1}) searching for keywords({2}).".format(
            index, 
            None if "id" not in ratedQuery else ratedQuery["id"],
            ratedQuery["queryJson"]["Keywords"]))

        # Build Ty and Tqids. Also build selectedSlides array to build Tx later.
        selectedSlides = []
        for queryResult in ratedQuery["results"]:
            Ty.append(queryResult["avgRating"])
            Tqids.append(ratedQuery["id"])
            slideId = queryResult["slide"]
            selectedSlides.append(slideHierarchy["Slides"][slideId])

        with blockProfiler("buildSeedTrainingSet.FeatureComputation"):
            Tx.extend(slideSearchIndex.features(ratedQuery["queryJson"], selectedSlides))

        print("Profiling data for query collation:\n {0}".format(json.dumps(lastCallProfile(), indent=4)))

    return AttrDict({"Tx":Tx, "Ty":Ty, "Tqids":Tqids, "TresultIds":TresultIds})

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

    # Initialize a word2vecDistanceModel to be used regularly.
    word2vecDistanceModel = Word2vecDistanceModel()
    print("Profiling data for building Word2vecDistanceModel:\n {0}".format(json.dumps(lastCallProfile(), indent=4)))

    # Main loop.
    while True:
        # Get all changes made since last update.
        dataForIndexing = slideDbClient.getSlideHierarchy()

        # Slide search using LambdaMART.
        slideSearchIndex = SlideSearchLambdaMart(dataForIndexing, lisaConfig.slideIndexer, word2vecDistanceModel)

        # Collate slides rating data from the server.
        slideRatingsData = searchClient.getSlideRatingsData(dataForIndexing)

        # File to save slideRatings data in.
        slideRatingsDataFilePath = lisaConfig.dataFolderPath + "slideRatingsData.json"
        with open(slideRatingsDataFilePath, "w") as fp:
            json.dump(slideRatingsData, fp, indent=4)

        # If slide ratings data quantity is small, simulate it.
        if len(slideRatingsData) < 1000:
            indexType = "SimulatedRatings"
            # Generate slide ratings data.
            simulatedSlideRatingsDataFilePath = lisaConfig.dataFolderPath + "simulatedSlideRatingsData.json"
            #if os.path.exists(simulatedSlideRatingsDataFilePath):
            #    with open(simulatedSlideRatingsDataFilePath, "r") as fp:
            #        slideRatingsData = json.load(fp)
            #else:
            slideSearchIndexSeed = SlideSearchW2V(dataForIndexing, lisaConfig.slideIndexer, word2vecDistanceModel)
            slideRatingsData = slideSearchIndex.buildSeedTrainingSet(slideSearchIndexSeed)
            with open(simulatedSlideRatingsDataFilePath, "w") as fp:
                json.dump(slideRatingsData, fp, indent=4)
            rankingSources = None
        else:
            indexType = "UserRatings"
            rankingSources = [queryObj["id"] for queryObj in slideRatingsData]

        # Convert ratings data into (Tx, Ty, Tqids and TresultIds)
        slideRatingVecs = getSlideRatingVecs(slideSearchIndex, slideRatingsData, dataForIndexing)

        # Now train LambdaMART index using the ratings data.
        slideSearchIndex.fit(slideRatingVecs.Tx, slideRatingVecs.Ty, slideRatingVecs.Tqids)

        # Upload the slide search index.
        searchClient.uploadSlideSearchIndex(slideSearchIndex, indexType, rankingSources)

        # Sleep for iteration period, before trying again.
        time.sleep(lisaConfig.slideIndexer.IterationPeriod)

searchIndexCreatorThreadFunc()