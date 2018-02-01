"""
    Slide Search based upon Lambda MART.
        LambdaMART implementation used is pyltr(https://github.com/jma127/pyltr).
    Design
        https://prezentium.sharepoint.com/sites/lisadev/Shared%20Documents/01_Design/Atto%20-%20Design%20-%20Slide%20Search.docx?web=1
    References:
        Microsoft LTR dataset: https://www.microsoft.com/en-us/research/project/mslr
"""

import json, re
import gensim, pyltr

from itertools import accumulate

from LibLisa import lisaConfig, methodProfiler, blockProfiler, lastCallProfile
from SlideSearch.SlideSearchBase import SlideSearchBase, getPath
from SlideSearch.SectionModel import SectionModel

class SlideSearchLambdaMart(SlideSearchBase):
    """
    Search engine object for slides, using LambdaMART.
    """
    def __init__(self, dataToIndex, config, word2vecDistanceModel):
        """
        Constructor for SlideSearchIndex takes the path of slide contents file as input.
        """
        with blockProfiler("SlideSearchLambdaMart.__init__"):
            # Invoke base class constructor.
            super().__init__(dataToIndex, config)

            # Build the word corpus.
            if not self.dataToIndex["Slides"]:
                self.dictionary = None
                self.slideTagModel = None
                self.constructPathList = []
                self.constructPathToIndex = {}
                self.constructPathModel = None
            else:
                completeCorpus = [extractCorpus(slide) for slide in self.dataToIndex["Slides"]]

                # Create a word dictionary for use in vector building.
                self.dictionary = gensim.corpora.Dictionary(completeCorpus)

                # Build section wise corpora and model for slide tags.
                slideTagCorpora = [slide["tags"] for slide in self.dataToIndex["Slides"]]
                self.slideTagModel = SectionModel(slideTagCorpora, self.dictionary, word2vecDistanceModel)

                # Build corpora for construct paths.
                constructPathCorpora = set([getPath(slide) for slide in self.dataToIndex["Slides"]])
                self.constructPathList = [list(constructPath) for constructPath in constructPathCorpora]
                self.constructPathToIndex = { tuple(path):index for (index, path) in enumerate(self.constructPathList) }
                self.constructPathModel = SectionModel(self.constructPathList, self.dictionary, word2vecDistanceModel)

    @methodProfiler
    def features(self, queryInfo, permittedSlides=None):
        """
        Computes feature vector, one for eacg slides in DB.
        ftrVec(queryInfo, slide) will determine the rating score of slide, when querying for slide.
        """
        if permittedSlides is None:
            permittedSlides = self.dataToIndex["Slides"]
            permittedIndices = range(len(self.dataToIndex["Slides"]))
        else:
            permittedIndices = [slide["Index"] for slide in permittedSlides]

        # Create construct feature array from path model.
        constructFtrArray = self.constructPathModel.get_features(queryInfo)

        # Use construct level features as initial slide level features.
        slideFtrArray = []
        for slide in permittedSlides:
            # Get construct level features for the current slide.
            constructFtr = constructFtrArray[self.constructPathToIndex[getPath(slide)]]
            # Append a copy of features into the slide feature array.
            slideFtrArray.append(list(constructFtr))

        # To the features already built, append features corresponding to slide tag model.
        slideFtrArray = self.slideTagModel.get_features(queryInfo, slideFtrArray, permittedIndices)

        return slideFtrArray

    @methodProfiler
    def buildSeedTrainingSet(self, seedDataBuilder):
        """
        To train LambdaMART model, we need to first build a basic training set.
        This training set should work for the case when true rating data is not available.
        """
        (Tx, Ty, Tqids) = ([], [], [])

        for (wordIndex, word) in self.dictionary.items():
            if re.search("[0-9]", word):
                # Words with digits are not interesting for search.
                continue
            print("{0}: Processing word {1}.".format(wordIndex, word))
            simulatedQuery = {"Keywords" : [word]}
            results = seedDataBuilder.slideSearch(simulatedQuery)
            print("Profiling data for slideSearch:\n {0}".format(json.dumps(lastCallProfile(), indent=4)))

            with blockProfiler("buildSeedTrainingSet.QueryCollationFromResults."+word):
                # Only retain top 10.
                results = results[0:30]
                gaps = [(results[i+1][0] - results[i][0]) for i in range(len(results)-1)]
                if not gaps:
                    continue
                maxGapIndex = gaps.index(max(gaps))
                selectedSlides = []
                for (index, (slideScore, slide)) in enumerate(results):
                    if (abs(index - maxGapIndex) >= 5):
                        # Ignore results, which are very far.
                        continue
                    if (index < maxGapIndex):
                        Ty.append(4)
                    else:
                        Ty.append(0)

                    selectedSlides.append(slide)
                    Tqids.append(word)

            with blockProfiler("buildSeedTrainingSet.FeatureComputation."+word):
                Tx.extend(self.features(simulatedQuery, selectedSlides))
            print("Profiling data for query collation:\n {0}".format(json.dumps(lastCallProfile(), indent=4)))

        return (Tx, Ty, Tqids)

    @methodProfiler
    def fit(self, Tx, Ty, Tqids):
        # Use NDCG metric.
        self.LambdaMartMetric = pyltr.metrics.NDCG(k=10)
        
        # Monitor progress and stop early.
        self.LambdaMartMonitor = pyltr.models.monitors.ValidationMonitor(Tx, Ty, Tqids, metric=self.LambdaMartMetric, stop_after=250)

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
        self.LambdaMartModel.fit(Tx, Ty, Tqids, monitor=self.LambdaMartMonitor)

    @methodProfiler
    def slideSimilarity(self, queryInfo, permittedSlides):
        # Calculate feature vector for all slides in the DB.
        ftrVec = self.features(queryInfo, permittedSlides)

        # Use LambdaMART model to calculate the scores of each slide in DB.
        # Retval is a dictionary from "original index" of a slide to its score.
        retval = {}
        for (index, score) in enumerate(self.LambdaMartModel.predict(ftrVec)):
            slide = permittedSlides[index]
            originalSlideIndex = slide["Index"]
            retval[originalSlideIndex] = score

        # Return the result.
        return retval

@methodProfiler
def extractCorpus(slideComponent):
    """
    Extract string corpus to search for in the slides.
    """
    if isinstance(slideComponent, str):
        return re.split("\W+", slideComponent)
    if any([isinstance(slideComponent, T) for T in [int, bool]]):
        return []
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
