"""
    Slide Search based upon Lambda MART.
        LambdaMART implementation used is pyltr(https://github.com/jma127/pyltr).
    Design
        https://prezentium.sharepoint.com/sites/lisadev/Shared%20Documents/01_Design/Atto%20-%20Design%20-%20Slide%20Search.docx?web=1
    References:
        Microsoft LTR dataset: https://www.microsoft.com/en-us/research/project/mslr
"""

import json
import gensim, pyltr

from itertools import accumulate

from LibLisa import lisaConfig
from SlideSearchBase import SlideSearchBase
from SectionModel import SectionModel

class SlideSearchLambdaMart(SlideSearchBase):
    """
    Search engine object for slides, using LambdaMART.
    """
    def __init__(self, slideInfoFilepath):
        """
        Constructor for SlideSearchIndex takes the path of slide contents file as input.
        """
        # Invoke base class constructor.
        super().__init__(slideInfoFilepath)

        # Build the word corpus.
        completeCorpus = [extractCorpus(slide) for slide in self.slideInfoSet]

        # Create a word dictionary for use in vector building.
        self.dictionary = gensim.corpora.Dictionary(completeCorpus)

        # Build section wise corpora and model for slide tags.
        slideTagCorpora = [slideInfo["Tags"] for slideInfo in self.slideInfoSet]
        self.slideTagModel = SectionModel(slideTagCorpora, self.dictionary)

        # Build corpora for construct paths.
        constructsPathCorpora = set([slideInfo["Path"] for slideInfo in self.slideInfoSet])
        self.constructsPathList = [list(constructsPath) for constructsPath in constructsPathCorpora]
        self.constructsPathToIndex = { tuple(path):index for (index, path) in enumerate(self.constructsPathList) }
        self.constructsPathModel = SectionModel(self.constructsPathList, self.dictionary)

    def features(self, queryDoc):
        """
        Computes feature vector, one for eacg slides in DB.
        ftrVec(queryDoc, slideInfo) will determine the rating score of slideInfo, when querying for slideInfo.
        """
        # Create construct feature array for path model.
        constructsFtrArray = self.constructsPathModel.get_features(queryDoc)

        # Convert construct level features into initial slide level features.
        slideFtrArray = [constructsFtrArray[self.constructsPathToIndex[slideInfo["Path"]]] for slideInfo in self.slideInfoSet]

        slideFtrArray = self.slideTagModel.get_features(queryDoc, slideFtrArray)

        return slideFtrArray

    def buildSeedTrainingSet(self, seedDataBuilder):
        """
        To train LambdaMART model, we need to first build a basic training set.
        This training set should work for the case when true rating data is not available.
        """
        (Tx, Ty, Tqids) = ([], [], [])

        for word in self.dictionary.values():
            simulatedQuery = {"Keywords" : [word]}
            results = seedDataBuilder.slideSearch(simulatedQuery)
            # Only retain top 10.
            results = results[0:30]
            gaps = [(results[i+1][0] - results[i][0]) for i in range(len(results)-1)]
            if not gaps:
                continue
            maxGapIndex = gaps.index(max(gaps))
            for (index, (slideScore, slideInfo)) in enumerate(results):
                if (abs(index - maxGapIndex) >= 10):
                    # Ignore results, which are very far.
                    continue
                if (index < maxGapIndex):
                    Ty.append(4)
                else:
                    Ty.append(0)

                Tx.append(self.features(simulatedQuery))
                Tqids.append(word)
        return (Tx, Ty, Tqids)

    def fit(self, Tx, Ty, Tqids):
        # Use NDCG metric.
        self.LambdaMartMetric = pyltr.metrics.NDCG(k=10)
        
        # Monitor progress and stop early.
        self.LambdaMartMonitor = pyltr.models.monitors.ValidationMonitor(VX, Vy, Vqids, metric=self.LambdaMartMetric, stop_after=250)

        # Build model instance.
        self.LambdaMartModel = pyltr.models.LambdaMART(
            metric=self.LambdaMartMetric,
            n_estimators=50,
            learning_rate=0.02,
            max_features=0.5,
            query_subsample=0.5,
            max_leaf_nodes=10,
            min_samples_leaf=64,
            verbose=1,
        )

        # Fit the model.
        self.LambdaMartModel.fit(TX, Ty, Tqids, monitor=monitor)

    def slideSearch(self, queryDoc):
        # Calculate feature vector for all slides in the DB.
        ftrVec = self.features(queryDoc)

        # Use LambdaMART model to calculate the scores of each slide in DB.
        predictions = [(score, self.slideInfoSet[index]) for (index, score) in enumerate(self.predict(ftrVec))]

        # Sort the slides according to score.
        predictions.sort(key = lambda tuple : tuple[0])

        # Return the result.
        return predictions

def extractCorpus(slideComponent):
    if any([isinstance(slideComponent, T) for T in [str, int, bool]]):
        return [ str(slideComponent) ]
    elif isinstance(slideComponent, list) or isinstance(slideComponent, tuple):
        retval = []
        for item in slideComponent:
            retval.extend(extractCorpus(item))
        if isinstance(slideComponent, tuple):
            retval = tuple(retval)
        return retval
    elif isinstance(slideComponent, dict):
        retval = []
        for (key, value) in slideComponent.items():
            retval.append(key)
            retval.extend(extractCorpus(value))
        return retval
    else:
        import pdb;pdb.set_trace()
