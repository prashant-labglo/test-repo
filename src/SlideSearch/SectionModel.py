import gensim

class SectionModel(object):
    """
    Indexes a text segment for search and provides the ability to generate features like:
        BM25, TFIDF, SemanticSimilarity, 
    """
    def __init__(self, corpus, dictionary):
        self.corpus = corpus

        # Create a word dictionary for use in vector building.
        # self.dictionary = gensim.corpora.Dictionary(self.corpus)
        self.dictionary = dictionary

        # Build a TFIDF model for the corpus.
        self.tfidfModel = gensim.models.TfidfModel(self.corpus, dictionary=self.dictionary)

        self.bm25 = gensim.summarization.bm25.BM25(self.corpus)

        self.average_idf = sum(float(val) for val in self.bm25.idf.values()) / len(self.bm25.idf)

    def get_bm25(self, queryDoc, corpusIndex):
        return self.bm25.get_score(queryDoc, corpusIndex, self.average_idf)

    def get_features(self, queryDoc, ftrArray=None):
        if ftrArray is None:
            ftrArray = [[] for i in range(len(self.corpus))]

        for (corpusIndex, corpusDoc) in enumerate(self.corpus):
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

            ftrArray[corpusIndex].extend([sum_tf, sum_idf, sum_tfidf])
        return ftrArray

