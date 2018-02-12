"""
SlideSearch is a python module which focus purely on ML algorithm aspects of searching for
slides.
"""
import json, os, re, sys

from LibLisa import lastCallProfile, lisaConfig, LisaPhpClient

from SlideSearch.Word2VecDistanceModel import Word2vecDistanceModel
from SlideSearch.SlideSearchWord2vec import SlideSearchW2V
from SlideSearch.SlideSearchLambdaMART import SlideSearchLambdaMart

# Test code.
if __name__ == "__main__":
    # Get a Lisa PHP client.
    lisaPhPClient = LisaPhpClient()
    lisaPhPClient.login()

    # Load Zepto data and save it into file for future reference.
    latestZeptoData = lisaPhPClient.getLatestData()
    with open(lisaConfig.dataFolderPath + "latestZeptoData.json", "w") as fp:
        json.dump(latestZeptoData, fp, indent=2)

    # Repair the Zepto data.
    latestZeptoDataRepaired = lisaPhPClient.repairZeptoData(latestZeptoData)
    with open(lisaConfig.dataFolderPath + "latestZeptoDataRepaired.json", "w") as fp:
        json.dump(latestZeptoDataRepaired, fp, indent=2)

    # Transform Zepto data for use with SlideDB.
    latestZeptoDataTransformed = lisaPhPClient.transformZeptoData(latestZeptoDataRepaired)
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
    trainingDataFilePath = lisaConfig.dataFolderPath + "trainingData.json"
    if os.path.exists(trainingDataFilePath):
        with open(trainingDataFilePath, "r") as fp:
            trainingData = json.load(fp)
            (Tx, Ty, Tqids) = (trainingData["Tx"], trainingData["Ty"], trainingData["Tqids"])
    else:
        # Training requires seed data. Seed data is created by applying SlideSearchW2V.
        slideSearchIndexSeed = SlideSearchW2V(latestZeptoDataTransformed, lisaConfig.slideSearch, word2vecDistanceModel)
        (Tx, Ty, Tqids) = slideSearchIndex.buildSeedTrainingSet(slideSearchIndexSeed)
        with open(trainingDataFilePath, "w") as fp:
            json.dump({"Tx":Tx, "Ty":Ty, "Tqids":Tqids}, fp, indent=4)

    # LambdaMART index is now trained using the training data.
    slideSearchIndex.fit(Tx, Ty, Tqids)

    # Make a query.
    while True:
        queryStr = input("Enter search keywords:")
        keywords = re.split("\W+", queryStr)
        queryInfo = {"Keywords" : keywords}
        result = slideSearchIndex.slideSearch(queryInfo)
        print("Results:")
        json.dump(result[0:10], sys.stdout, indent=4)

