import gensim

from LibLisa import methodProfiler, blockProfiler, lastCallProfile

class SectionModel(object):
    """
    Indexes a text segment for search and provides the ability to generate features like:
        BM25, TFIDF, SemanticSimilarity, 
    """
    def __init__(self, corpus, dictionary, word2vecDistanceModel):
        with blockProfiler("SectionModel.__init__"):
            self.corpus = corpus

            # Create a word dictionary for use in vector building.
            # self.dictionary = gensim.corpora.Dictionary(self.corpus)
            self.dictionary = dictionary

            # One of the features is word2vec distance.
            self.word2vecDistanceModel = word2vecDistanceModel

            # Build a TFIDF model for the corpus.
            self.tfidfModel = gensim.models.TfidfModel(self.corpus, dictionary=self.dictionary)

            self.bm25 = gensim.summarization.bm25.BM25(self.corpus)

            self.average_idf = sum(float(val) for val in self.bm25.idf.values()) / len(self.bm25.idf)

    @methodProfiler
    def get_bm25(self, queryDoc, corpusIndex):
        return self.bm25.get_score(queryDoc, corpusIndex, self.average_idf)

    @methodProfiler
    def get_features(self, queryDoc, ftrArray=None, permittedIndices=None):
        if permittedIndices is None:
            permittedIndices = range(len(self.corpus))

        if ftrArray is None:
            ftrArray = [[] for i in range(len(permittedIndices))]

        curIndex = 0
        for corpusIndex in permittedIndices:
            corpusDoc = self.corpus[corpusIndex]

            sum_tf = 0
            sum_idf = 0
            sum_tfidf = 0
            for word in queryDoc["Keywords"]:
                if word not in self.bm25.f[corpusIndex]:
                    continue
                tf = self.bm25.f[corpusIndex][word]
                idf = self.bm25.idf[word] if self.bm25.idf[word] >= 0 else EPSILON * self.average_idf

                sum_tf += tf
                sum_idf += idf
                sum_tfidf += tf * idf

            # Append TF-IDF features.
            ftrArray[curIndex].extend([sum_tf, sum_idf, sum_tfidf])

            # Append word2vec distance.
            word2vecDistance = self.word2vecDistanceModel.queryPhrase2TagsetSimilarity(queryDoc["Keywords"], corpusDoc)
            ftrArray[curIndex].append(word2vecDistance)

            curIndex += 1
        return ftrArray

