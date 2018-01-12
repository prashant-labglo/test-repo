"""
    Design
        https://prezentium.sharepoint.com/sites/lisadev/Shared%20Documents/01_Design/Atto%20-%20Design%20-%20Slide%20Search.docx?web=1
    References:
        Download word2vec from here: http://mccormickml.com/2016/04/12/googles-pretrained-word2vec-model-in-python/
        Smaller version of same flie: https://github.com/eyaler/word2vec-slim

        LambdaMART Implementation
        https://bitbucket.org/tunystom/rankpy
"""

import json
import gensim

def textCleanUp(jsonObject, badStrings=None):
    """
    Removes unnecessary whitespace and makes everything lowercase for an arbitrary JSON.
    """
    if (isinstance(jsonObject, str)):
        if badStrings is not None and (" " in jsonObject or "," in jsonObject):
            badStrings.add(jsonObject)
        return jsonObject.lower().strip().replace(" ", "_")
    if (isinstance(jsonObject, list)):
        # Some of the strings are of kind "a, b". They should be flattened into list.
        if any([isinstance(item, str) and "," in item for item in jsonObject]):
            badStrings.add(jsonObject[0])
            jsonObject = ",".join(jsonObject).split(",")

        # If we are not dealing with list of strings, then we need to clean them up, recursively.
        jsonObject = [textCleanUp(item, badStrings) for item in jsonObject]

        # Remove empty string
        jsonObject = [item for item in jsonObject if item]

        # Remove duplicates if we are dealing with list of strings.
        if all([isinstance(item, str) for item in jsonObject]):
            jsonObject = list(set(jsonObject))
        return jsonObject

    if (isinstance(jsonObject, dict)):
        return {key:textCleanUp(value, badStrings) for (key, value) in jsonObject.items()}
    return jsonObject

class SlideSearchIndex(object):
    """
    Search engine object for slides.
    """
    def __init__(self, word2vecModelPath, slideInfoFilepath):
        """
        Constructor for SlideSearchIndex takes the path of slide contents file as input.
        """
        with open(slideInfoFilepath, "r", encoding="utf8") as fp:
            slideInfoSet = json.load(fp)
        badStrings = set()
        self.slideInfoSet = textCleanUp(slideInfoSet, badStrings)
        self.badStrings = badStrings
        for badString in badStrings:
            print(badString)
        json.dump(self.slideInfoSet, open(slideInfoFilepath + "Cleaned.json", "w"))

        # self.word2vecModel = gensim.models.KeyedVectors.load_word2vec_format('C:/Users/NishantSharma/source/repos/word2vec-slim/GoogleNews-vectors-negative300-SLIM.bin', binary=True)
        self.word2vecModel = gensim.models.KeyedVectors.load_word2vec_format(word2vecModelPath, binary=True)

    def word2wordSemanticSimilarity(self, word1, word2):
        try:
            return self.word2vecModel.similarity(word1, word2)
        except KeyError:
            print("Key not found: {0} or {1}".format(word1, word2))
            return -2

    def word2TagsetSemanticSimilarity(self, word, tagset):
        maxSimilarity = -1
        mostSimilarTag = None
        for tag in tagset:
            tagSimilarity = self.word2wordSemanticSimilarity(word, tag)
            if (tagSimilarity > maxSimilarity):
                maxSimilarity = tagSimilarity 
                mostSimilarTag = tag

        return maxSimilarity

    def queryPhrase2TagsetSimilarity(self, words, tagset):
        # Get semantic similarity
        semanticSimilarity = sum([self.word2TagsetSemanticSimilarity(word, tagset) for word in words])

        # tfidfSimilarity = sum([self.word2TagsetSimilarity(word, tagset) for word in words])

        # Return result.
        return semanticSimilarity

    def slideSimilarity(self, queryJson, slideInfo):
        """
            QueryJson can be of the following form.
            {
                # Optional
                "Keywords" : ["keyword1", "keyword2", ...],

                # Optional
                "permittedConstructs" : [
                    ("permittedConcept1", "permittedSubConcept1", "PermittedConstruct1"),
                    ("permittedConcept2", "permittedSubConcept2", "PermittedConstruct2"),
                    ("permittedConcept3", "permittedSubConcept3", "PermittedConstruct3"),
                    ...
                ],

                # Optional
                "permittedIcon"  : True | False,

                # Optional
                "permittedImage"  : True | False,

                # Optional
                "permittedStyle"  : True | False,

                # Optional
                "permittedVisualStyle"  : True | False
            }
        """
        queryJson = textCleanUp(queryJson)
        if "permittedConstructs" in queryJson.keys():
            found = False
            for (concept, subConcept, construct) in queryJson["permittedConstructs"]:
                if slideInfo["Concept"] == concept and slideInfo["SubConcept"] == subConcept and slideInfo["Construct"] == construct:
                    found = True
                    break
            if not found:
                # Constraints not met. No Similarity.
                return -2

        if "permittedIcon" in queryJson.keys():
            if slideInfo["Icon"] != queryJson["permittedIcon"]:
                # Constraints not met. No Similarity.
                return -2

        if "permittedImage" in queryJson.keys():
            if slideInfo["Image"] != queryJson["permittedImage"]:
                # Constraints not met. No Similarity.
                return -2

        if "permittedLayout" in queryJson.keys():
            if slideInfo["Layout"] not in queryJson["permittedLayouts"]:
                # Constraints not met. No Similarity.
                return -2

        if "permittedStyle" in queryJson.keys():
            if slideInfo["Style"] not in queryJson["permittedStyle"]:
                # Constraints not met. No Similarity.
                return -2

        if "permittedVisualStyle" in queryJson.keys():
            if slideInfo["VisualStyle"] not in queryJson["permittedVisualStyle"]:
                # Constraints not met. No Similarity.
                return -2

        return self.queryPhrase2TagsetSimilarity(queryJson["Keywords"], slideInfo["Identifiers"])

    def slideSearch(self, queryJson):
        resultList = []
        for slideInfo in self.slideInfoSet["results"]:
            slideScore = self.slideSimilarity(queryJson, slideInfo)
            if slideScore > 0:
                resultList.append((slideScore, slideInfo))

        resultList.sort(key = lambda tuple : tuple[0])
        return resultList

if __name__ == "__main__":
    slideSearchIndex = SlideSearchIndex(
        #'C:/Users/NishantSharma/source/repos/word2vec/GoogleNews-vectors-negative300.bin',
        'C:/Users/NishantSharma/source/repos/word2vec-slim/GoogleNews-vectors-negative300-SLIM.bin',
        ".\slidelist_json.json")

    import pdb;pdb.set_trace()
    slideSearchIndex.slideSearch({"Keywords" : ["Agenda"]})


