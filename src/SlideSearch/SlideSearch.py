"""

    Design
        https://prezentium.sharepoint.com/sites/lisadev/Shared%20Documents/01_Design/Atto%20-%20Design%20-%20Slide%20Search.docx?web=1
    References:
        Download word2vec from here: http://mccormickml.com/2016/04/12/googles-pretrained-word2vec-model-in-python/
        Smaller version of same flie: https://github.com/eyaler/word2vec-slim
"""

import json
import gensim

# Read JSON file.
def textCleanUp(data):
    """
    Removes unnecessary whitespace and makes everything lowercase.
    """
    if (isinstance(data, str)):
        return data.lower().strip().replace(" ", "_")
    if (isinstance(data, list)):
        return [textCleanUp(item) for item in data]
    if (isinstance(data, dict)):
        return {key:textCleanUp(value) for (key, value) in data.items()}
    return data

class SlideSearchIndex(object):
    def __init__(self, slideInfoFilepath):

        slideInfoSet = json.load(open(slideInfoFilepath, "r", encoding="utf8"))
        self.slideInfoSet = textCleanUp(slideInfoSet)

        self.word2vecModel = gensim.models.KeyedVectors.load_word2vec_format('C:/Users/NishantSharma/source/repos/word2vec-slim/GoogleNews-vectors-negative300-SLIM.bin', binary=True)

    def word2wordSemanticSimilarity(self, word1, word2):
        try:
            return self.word2vecModel.similarity(word1, word2)
        except KeyError:
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
                "permittedConstructs" : [
                    ("permittedConcept1", "permittedSubConcept1", "PermittedConstruct1"),
                    ("permittedConcept2", "permittedSubConcept2", "PermittedConstruct2"),
                    ("permittedConcept3", "permittedSubConcept3", "PermittedConstruct3"),
                    ...
                ]
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
    slideSearchIndex = SlideSearchIndex(".\slidelist.json")

    import pdb;pdb.set_trace()
    slideSearchIndex.slideSearch({"Keywords" : ["Agenda"]})


