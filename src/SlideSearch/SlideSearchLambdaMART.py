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
    def __init__(self, dataForIndexing, config, word2vecDistanceModel):
        """
        Constructor for SlideSearchIndex takes the path of slide contents file as input.
        """
        isDjangoModel = config["isDjangoModel"]
        with blockProfiler("SlideSearchLambdaMart.__init__"):
            # Invoke base class constructor.
            super().__init__(dataForIndexing, config)

            # Build the word corpus.
            if not self.dataForIndexing["Slides"]:
                self.dictionary = None
                self.slideTagModel = None
                self.constructPathList = []
                self.constructPathToIndex = {}
                self.constructPathModel = None
            else:
                allSlides = self.dataForIndexing["Slides"]
                def getTags(slide):
                    return slide.tags.names() if isDjangoModel else slide["tags"]
                def extractSlideCorpus(slide):
                    retval = []
                    retval.extend(getTags(slide))
                    return retval

                completeCorpus = [extractSlideCorpus(slide) for slide in allSlides]

                # Create a word dictionary for use in vector building.
                self.dictionary = gensim.corpora.Dictionary(completeCorpus)

                # Build section wise corpora and model for slide tags.
                slideTagCorpora = [getTags(slide) for slide in allSlides]

                self.slideTagModel = SectionModel(slideTagCorpora, self.dictionary, word2vecDistanceModel)

                # Build corpora for construct paths.
                constructPathCorpora = set([getPath(slide) for slide in allSlides])
                self.constructPathList = [list(constructPath) for constructPath in constructPathCorpora]
                self.constructPathToIndex = { tuple(path):index for (index, path) in enumerate(self.constructPathList) }
                self.constructPathModel = SectionModel(self.constructPathList, self.dictionary, word2vecDistanceModel)

    @methodProfiler
    def features(self, queryInfo, permittedSlides=None):
        """
        Computes feature vector, one for eacg slides in DB.
        ftrVec(queryInfo, slide) will determine the rating score of slide, when querying for slide.
        """
        allSlides = self.dataForIndexing["Slides"]
        if permittedSlides is None:
            permittedSlides = allSlides
            permittedIndices = range(len(allSlides))
        else:
            slideToIndexMap = { slide:index for (index, slide) in enumerate(allSlides) }
            permittedIndices = [slideToIndexMap[slide] for slide in permittedSlides]

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
        # Build a word occurence dictionary mapping words to slides where they occur.
        wordToMatchingSlides = {}
        for slide in self.dataForIndexing["Slides"]:
            slideTags = slide.tags.names() if self.config["isDjangoModel"] else slide["tags"]
            for tag in slideTags:
                if re.search("[0-9]", tag):
                    # Tags with digits are not interesting for search.
                    continue
                if tag in wordToMatchingSlides:
                    wordToMatchingSlides[tag].append(slide)
                else:
                    wordToMatchingSlides[tag] = [slide]
        wordToMatchingSlides = list(wordToMatchingSlides.items())

        # Sort words according to the # of slides they occur in.
        wordToMatchingSlides.sort(key = lambda tuple:len(tuple[1]))
        # Save word occurence dictionary.
        with open(lisaConfig.dataFolderPath + "trainingWords.json", "w") as fp:
            wordToMatchingSlideIds = {}
            for (word, matchingSlides) in wordToMatchingSlides:
                wordToMatchingSlideIds[word] = list(map(lambda slide:slide.id, matchingSlides))
            json.dump(wordToMatchingSlideIds, fp, indent=4)

        # Only retain words with frequency less than 1% of total slides.
        freqThreshold = int(0.01 * len(self.dataForIndexing["Slides"]))
        nonMatchingSlideCount = int(0.02 * len(self.dataForIndexing["Slides"]))
        wordToMatchingSlides = [(word, matchingSlides) for (word, matchingSlides) in wordToMatchingSlides if len(matchingSlides) < freqThreshold]

        (Tx, Ty, Tqids, TresultIds) = ([], [], [], [])
        for (index, (word, matchingSlides)) in enumerate(wordToMatchingSlides):
            print("{0}: Processing word {1}, occuring in {2}.".format(index, word, wordToMatchingSlideIds[word]))
            simulatedQuery = {"Keywords" : [word]}
            results = seedDataBuilder.slideSearch(simulatedQuery)
            print("Profiling data for slideSearch:\n {0}".format(json.dumps(lastCallProfile(), indent=4)))

            # Now, find slides, which are close but are not matching.
            closeButNotMatchingSlides = []
            i = 0
            while len(closeButNotMatchingSlides) < nonMatchingSlideCount:
                if results[i][1] not in matchingSlides:
                    closeButNotMatchingSlides.append(results[i][1])
                i += 1

            selectedSlides = []
            for slide in matchingSlides:
                Ty.append(4)
                selectedSlides.append(slide)
                Tqids.append(word)
                TresultIds.append(slide.id)

            for slide in closeButNotMatchingSlides:
                Ty.append(0)
                selectedSlides.append(slide)
                Tqids.append(word)
                TresultIds.append(slide.id)

            with blockProfiler("buildSeedTrainingSet.FeatureComputation."+word):
                Tx.extend(self.features(simulatedQuery, selectedSlides))

            print("Profiling data for query collation:\n {0}".format(json.dumps(lastCallProfile(), indent=4)))

        return (Tx, Ty, Tqids, TresultIds)

    @methodProfiler
    def fit(self, Tx, Ty, Tqids):
        """
        Tx: Vector computed for each pair of query and one result row in the DB.
        Ty: Rating numbers for how good or bad the match for above pair is.
        Tqids: Query ID column. Query string can be same for many of the rows in Tx above.
            Tqid can be used to determine if the training rows correspond to same query
            string or different.
        """
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

    def json(self):
        retval = {}
        retval["feature_importances_"] = self.LambdaMartModel.feature_importances_
        retval["oob_improvement_"] = self.LambdaMartModel.oob_improvement_
        retval["train_score_"] = self.LambdaMartModel.train_score_
        #retval["estimators_"] = self.LambdaMartModel.estimators_
        retval["estimators_fitted_"] = self.LambdaMartModel.estimators_fitted_
        return retval

    @methodProfiler
    def slideSimilarity(self, queryInfo, permittedSlides):
        """
        This method computes similarity scores for all slides in permittedSlides.
        Query made in queryInfo.
        """
        # Calculate feature vector for all slides in the DB.
        ftrVec = self.features(queryInfo, permittedSlides)

        # Use LambdaMART model to calculate the scores of each slide in DB.
        # Retval is a dictionary from "original index" of a slide to its score.
        retval = {}
        for (index, score) in enumerate(self.LambdaMartModel.predict(ftrVec)):
            slide = permittedSlides[index]
            retval[index] = score

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
