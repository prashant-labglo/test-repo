"""
    Class used to encapsulate word2vec distance model.
    Using the model, we compute word distances, word to tag-set distances, and
    query phrase to tag-set distances.
"""
import gensim, os, json, pylru
from LibLisa import lisaConfig, methodProfiler, blockProfiler, lastCallProfile

class Word2vecDistanceModel(object):
    """
        Class used to encapsulate word2vec distance model.
        Using the model, we compute word distances, word to tag-set distances, and
        query phrase to tag-set distances.
    """
    def __init__(self):
        """
        Constructor
        """
        with blockProfiler("Word2vecDistanceModel.__init__"):
            # self.word2vecModel = gensim.models.KeyedVectors.load_word2vec_format('C:/Users/NishantSharma/source/repos/word2vec-slim/GoogleNews-vectors-negative300-SLIM.bin', binary=True)
            self.word2vecModel = gensim.models.KeyedVectors.load_word2vec_format(lisaConfig.word2vecModelPath, binary=True)

    def word2wordSemanticSimilarity(self, word1, word2):
        """
        Measures semantic similarity between two words, using word2vec.
        """
        try:
            return self.word2vecModel.similarity(word1, word2)
        except KeyError:
            # print("Key not found: {0} or {1}".format(word1, word2))
            return -2

    @methodProfiler
    def word2TagsetSemanticSimilarity(self, word, tagset):
        """
        Measures semantic similarity between word and a tagset, using word2vec.
        """
        maxSimilarity = -1
        mostSimilarTag = None
        for tag in tagset:
            tagSimilarity = self.word2wordSemanticSimilarity(word, tag)
            if (tagSimilarity > maxSimilarity):
                maxSimilarity = tagSimilarity 
                mostSimilarTag = tag
        return maxSimilarity

    @methodProfiler
    def queryPhrase2TagsetSimilarity(self, words, tagset):
        """
        Measures semantic similarity between a query phrase and a tagset, using word2vec.
        """
        # Get semantic similarity
        semanticSimilarity = sum([self.word2TagsetSemanticSimilarity(word, tagset) for word in words])

        # tfidfSimilarity = sum([self.word2TagsetSimilarity(word, tagset) for word in words])

        # Return result.
        return semanticSimilarity

word2vecDistanceModel = Word2vecDistanceModel()
print("Profiling data for building Word2vecDistanceModel:\n {0}".format(json.dumps(lastCallProfile(), indent=4)))

