from SlideSearchWord2vec import SlideSearchW2V
from SlideSearchLambdaMART import SlideSearchLambdaMart

if __name__ == "__main__":
    slideSearchIndex = SlideSearchLambdaMart(".\slidelist_json.json")

    slideSearchIndexSeed = SlideSearchW2V(".\slidelist_json.json")
    (Tx, Ty, Tqids) = slideSearchIndex.buildSeedTrainingSet(slideSearchIndexSeed)

    slideSearchIndex.fit(Tx, Ty, Tqids)

    # Make a query.
    doc = ["agenda"]
    slideSearchIndex.slideSearch({"Keywords" : ["Agenda"]})


