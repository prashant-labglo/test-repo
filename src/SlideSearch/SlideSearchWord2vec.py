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

from LibLisa import lisaConfig, methodProfiler, blockProfiler, lastCallProfile
from SlideSearch.SlideSearchBase import SlideSearchBase

class SlideSearchW2V(SlideSearchBase):
    """
    Search engine object for slides.
    The similarity is measured by simply taking a dot product between the two word vectors.
    """
    def __init__(self, dataForIndexing, config, word2vecDistanceModel):
        """
        Constructor for SlideSearchIndex takes the path of slide contents file as input.
        """
        # Invoke base class constructor.
        super().__init__(dataForIndexing, config)

        self.word2vecDistanceModel = word2vecDistanceModel

    @methodProfiler
    def slideSimilarity(self, queryInfo, permittedSlides):
        """
        Method to compute similarity score for all slides listed in the permittedSlides.
        """
        retval = {}
        for (index, slide) in enumerate(permittedSlides):
            slideScore = self.word2vecDistanceModel.queryPhrase2TagsetSimilarity(queryInfo["Keywords"], self.getTags(slide))
            retval[index] = slideScore

        return retval

