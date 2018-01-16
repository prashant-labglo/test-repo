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

from LibLisa import lisaConfig
from SlideSearchBase import SlideSearchBase

class SlideSearchW2V(SlideSearchBase):
    """
    Search engine object for slides.
    The similarity is measured by simply taking a dot product between the two word vectors.
    """
    def __init__(self, slideInfoFilepath):
        """
        Constructor for SlideSearchIndex takes the path of slide contents file as input.
        """
        # Invoke base class constructor.
        super().__init__(slideInfoFilepath)

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

