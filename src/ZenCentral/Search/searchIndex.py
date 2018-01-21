import json, os, re, sys

from LibLisa import lastCallProfile

from SlideSearch import Word2vecDistanceModel, SlideSearchW2V, SlideSearchLambdaMart

# Model to find word distances using word2vec.
word2vecDistanceModel = Word2vecDistanceModel()
print("Profiling data for building Word2vecDistanceModel:\n {0}".format(json.dumps(lastCallProfile(), indent=4)))

# Slide search using LambdaMART.
slideSearchIndex = SlideSearchLambdaMart(".\slidelist_json.json", word2vecDistanceModel)

# See if we have already created training data.
trainingDataFilename = "./trainingData.json"
if os.path.exists(trainingDataFilename):
    with open(trainingDataFilename, "r") as fp:
        trainingData = json.load(fp)
        (Tx, Ty, Tqids) = (trainingData["Tx"], trainingData["Ty"], trainingData["Tqids"])
else:
    # Training requires seed data. Seed data is created by applying SlideSearchW2V.
    slideSearchIndexSeed = SlideSearchW2V(".\slidelist_json.json", word2vecDistanceModel)
    (Tx, Ty, Tqids) = slideSearchIndex.buildSeedTrainingSet(slideSearchIndexSeed)
    with open(trainingDataFilename, "w") as fp:
        json.dump({"Tx":Tx, "Ty":Ty, "Tqids":Tqids}, fp, indent=4)

# LambdaMART index is now trained using the training data.
slideSearchIndex.fit(Tx, Ty, Tqids)
