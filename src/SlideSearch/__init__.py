"""
SlideSearch is a python module which focus purely on ML algorithm aspects of searching for
slides.
"""
import json, os, re, sys
import numpy as np

from LibLisa import lastCallProfile, lisaConfig, LisaZeptoClient, blockProfiler

from SlideSearch.Word2VecDistanceModel import Word2vecDistanceModel
from SlideSearch.SlideSearchWord2vec import SlideSearchW2V
from SlideSearch.SlideSearchLambdaMART import SlideSearchLambdaMart

def getSlideRatingVecs(slideSearchIndex, slideRatingsData, slideHierarchy):
    """
    Downloads all the slide rating data which is used to train a local PYLTR model for
    slide rankings.
    """
    retval = {}

    slidesDict = {slide["id"]:slide for slide in slideHierarchy["Slides"]}

    for label in ["T", "V", "E"]: # Training, Validatoin and Evaluation.
        retval[label] = {"x" : [], "y" : [], "qids" : [], "resultIds": []}

    for (index, ratedQuery) in enumerate(np.random.permutation(slideRatingsData)):
        # Pick label in a round robin manner on a random permutation.
        label = ["T", "V", "E"][(index % 3)]

        print("{0}: Processing query({1}) searching for keywords({2}) as {3}.",
            index, 
            None if "id" not in ratedQuery else ratedQuery["id"],
            ratedQuery["queryJson"]["Keywords"],
            label)

        # Build Ty and Tqids. Also build selectedSlides array to build Tx later.
        selectedSlides = []
        for queryResult in ratedQuery["results"]:
            retval[label]["y"].append(queryResult["avgRating"])
            retval[label]["qids"].append(ratedQuery["id"])
            slideId = queryResult["slide"]
            selectedSlides.append(slidesDict[slideId])
        with blockProfiler("buildSeedTrainingSet.FeatureComputation"):
            retval[label]["x"].extend(slideSearchIndex.features(ratedQuery["queryJson"], selectedSlides))

        print("Profiling data for query collation:\n {0}".format(json.dumps(lastCallProfile(), indent=4)))
    return retval

# Test code.
if __name__ == "__main__":
    # Get a Lisa Zepto client.
    lisaZeptoClient = LisaZeptoClient()
    lisaZeptoClient.login()

    # Load Zepto data and save it into file for future reference.
    latestZeptoData = lisaZeptoClient.getLatestData()
    with open(lisaConfig.dataFolderPath + "latestZeptoData.json", "w") as fp:
        json.dump(latestZeptoData, fp, indent=2)

    # Repair the Zepto data.
    latestZeptoDataRepaired = lisaZeptoClient.repairZeptoData(latestZeptoData)
    with open(lisaConfig.dataFolderPath + "latestZeptoDataRepaired.json", "w") as fp:
        json.dump(latestZeptoDataRepaired, fp, indent=2)

    # Transform Zepto data for use with SlideDB.
    latestZeptoDataTransformed = lisaZeptoClient.transformZeptoData(latestZeptoDataRepaired)
    with open(lisaConfig.dataFolderPath + "latestZeptoDataTransformed.json", "w") as fp:
        json.dump(latestZeptoDataTransformed, fp, indent=2)

    # Model to find word distances using word2vec.
    word2vecDistanceModel = Word2vecDistanceModel()
    print("Profiling data for building Word2vecDistanceModel:\n {0}".format(json.dumps(lastCallProfile(), indent=4)))

    # Assign indices to all slides.
    for (index, slide) in enumerate(latestZeptoDataTransformed["Slides"]):
        slide.id = index

    # Slide search using LambdaMART.
    lisaConfig["slideSearch"].isDjangoModel = False
    slideSearchIndex = SlideSearchLambdaMart(latestZeptoDataTransformed, lisaConfig.slideSearch, word2vecDistanceModel)

    # See if we have already created training data.
    slideRatingsDataFilePath = lisaConfig.dataFolderPath + "slideRatingsData.json"
    #if os.path.exists(slideRatingsDataFilePath):
    #    with open(slideRatingsDataFilePath, "r") as fp:
    #        slideRatingsData = json.load(fp)
    #        (Tx, Ty, Tqids) = (slideRatingsData["Tx"], slideRatingsData["Ty"], slideRatingsData["Tqids"])
    #else:
    # Training requires seed data. Seed data is created by applying SlideSearchW2V.
    slideSearchIndexSeed = SlideSearchW2V(latestZeptoDataTransformed, lisaConfig.slideSearch, word2vecDistanceModel)
    slideRatingsData = slideSearchIndex.buildSeedTrainingSet(slideSearchIndexSeed)
    with open(slideRatingsDataFilePath, "w") as fp:
        json.dump(slideRatingsData, fp, indent=4)

    # Convert ratings data into vectors for training, validation and evaluation.
    slideRatingVecs = getSlideRatingVecs(slideSearchIndex, slideRatingsData, latestZeptoDataTransformed)

    # LambdaMART index is now trained using the training data.
    slideSearchIndex.fit(slideRatingVecs)

    # Make a query.
    while True:
        queryStr = input("Enter search keywords:")
        keywords = re.split("\W+", queryStr)
        queryInfo = {"Keywords" : keywords}
        result = slideSearchIndex.slideSearch(queryInfo)
        print("Results:")
        json.dump(result[0:10], sys.stdout, indent=4)

