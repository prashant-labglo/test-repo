import gensim
from LibLisa import lisaConfig, methodProfiler, blockProfiler, lastCallProfile

class Word2vecDistanceModel(object):
    def __init__(self):
        with blockProfiler("Word2vecDistanceModel.__init__"):
            # self.word2vecModel = gensim.models.KeyedVectors.load_word2vec_format('C:/Users/NishantSharma/source/repos/word2vec-slim/GoogleNews-vectors-negative300-SLIM.bin', binary=True)
            self.word2vecModel = gensim.models.KeyedVectors.load_word2vec_format(lisaConfig.word2vecModelPath, binary=True)

    def word2wordSemanticSimilarity(self, word1, word2):
        try:
            return self.word2vecModel.similarity(word1, word2)
        except KeyError:
            # print("Key not found: {0} or {1}".format(word1, word2))
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


