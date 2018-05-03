"""
    Slide Search based upon Lambda MART.
        LambdaMART implementation used is pyltr(https://github.com/jma127/pyltr).
    Design
        https://prezentium.sharepoint.com/sites/lisadev/Shared%20Documents/01_Design/Atto%20-%20Design%20-%20Slide%20Search.docx?web=1
    References:
        Microsoft LTR dataset: https://www.microsoft.com/en-us/research/project/mslr
"""

import json, re, pickle
import gensim, pyltr

import numpy as np
from itertools import accumulate
from attrdict import AttrDict

from LibLisa import lisaConfig, methodProfiler, blockProfiler, lastCallProfile
from SlideSearch.SlideSearchBase import SlideSearchBase
from SlideSearch.SectionModel import SectionModel

class SlideSearchLambdaMart(SlideSearchBase):
    """
    Search engine object for slides, using LambdaMART.
    """
    def __init__(self, dataForIndexing, config):
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
                def extractSlideCorpus(slide):
                    retval = []
                    retval.extend(self.getTags(slide))
                    return retval

                completeCorpus = [extractSlideCorpus(slide) for slide in allSlides]

                # Create a word dictionary for use in vector building.
                self.dictionary = gensim.corpora.Dictionary(completeCorpus)

                # Build section wise corpora and model for slide tags.
                slideTagCorpora = [self.getTags(slide) for slide in allSlides]

                self.slideTagModel = SectionModel(slideTagCorpora, self.dictionary)

                # Build corpora for construct paths.
                constructPathCorpora = set([self.getPath(slide) for slide in allSlides])
                self.constructPathList = [list(constructPath) for constructPath in constructPathCorpora]
                self.constructPathToIndex = { tuple(path):index for (index, path) in enumerate(self.constructPathList) }
                self.constructPathModel = SectionModel(self.constructPathList, self.dictionary)

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
            slideToIndexMap = { self.getAttr(slide, "id"):index for (index, slide) in enumerate(allSlides) }
            permittedIndices = [slideToIndexMap[self.getAttr(slide, "id")] for slide in permittedSlides]

        # Create construct feature array from path model.
        constructFtrArray = self.constructPathModel.get_features(queryInfo)

        # Use construct level features as initial slide level features.
        slideFtrArray = []
        for slide in permittedSlides:
            toAppend = []
            # Get construct level features for the current slide.
            toAppend.extend(constructFtrArray[self.constructPathToIndex[self.getPath(slide)]])

            # Add zeptoDownloads count as a feature.
            toAppend.append(self.getAttr(slide, "zeptoDownloads"))

            # Append a copy of features into the slide feature array.
            slideFtrArray.append(toAppend)

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
            for tag in self.getTags(slide):
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
                wordToMatchingSlideIds[word] = list(map(lambda slide:slide["id"], matchingSlides))
            json.dump(wordToMatchingSlideIds, fp, indent=4)

        # Only retain words with frequency less than 1% of total slides.
        freqThreshold = int(0.02 * len(self.dataForIndexing["Slides"]))
        nonMatchingSlideCount = int(0.02 * len(self.dataForIndexing["Slides"]))
        wordToMatchingSlides = [(word, matchingSlides) for (word, matchingSlides) in wordToMatchingSlides if len(matchingSlides) < freqThreshold]

        retval = []
        for (index, (word, matchingSlides)) in enumerate(wordToMatchingSlides):
            with blockProfiler("buildSeedTrainingSet."+word):
                simulatedQuery = {"id" : word}
                simulatedQuery["queryJson"] = {"RatingKeywords" : [word]}

                # Now, find slides, which are close but are not matching.
                closeButNotMatchingSlides = []
                i = 0
                results = seedDataBuilder.slideSearch(simulatedQuery["queryJson"])
                while len(closeButNotMatchingSlides) < nonMatchingSlideCount:
                    if results[i][1] not in matchingSlides:
                        closeButNotMatchingSlides.append(results[i][1])
                    i += 1

                simulatedQueryResults = []
                simulatedQuery["results"] = simulatedQueryResults

                maxDownloads1 = max([slide["zeptoDownloads"] for slide in matchingSlides])
                maxDownloads2 = max([slide["zeptoDownloads"] for slide in closeButNotMatchingSlides])
                maxDownloads = float(max(maxDownloads1, maxDownloads2) + 0.0001)
                # Build positive results.
                for slide in matchingSlides:
                    simulatedQueryResult = {
                            "avgRating" : 5 + int(10 * slide["zeptoDownloads"]/maxDownloads),
                            "slide" : slide["id"],
                        }
                    simulatedQueryResults.append(simulatedQueryResult)

                # Build negative results.
                for slide in closeButNotMatchingSlides:
                    simulatedQueryResult = {
                            "avgRating" : -15 + int(10 * slide["zeptoDownloads"]/maxDownloads),
                            "slide" : slide["id"],
                        }
                    simulatedQueryResults.append(simulatedQueryResult)

                retval.append(simulatedQuery)
            print("{0}: Processed word {1}, occuring in {2}.".format(index, word, wordToMatchingSlideIds[word]))
        return retval

    @methodProfiler
    def fit(self, slideRatingVecs):
        """

        slideRatingVecs:  
            Contains feature vector computed for each pair of query and one result row in the DB.
            Partitioned into three groups.
                slidaRatingVecs["T"] : Slide rating vectors for training.
                slidaRatingVecs["V"] : Slide rating vectors for validation.
                slidaRatingVecs["E"] : Slide rating vectors for final evaluation.
            Each of the above three have
                slidaRatingVecs["T"]["X"] : feature vectors for the pair.
                slidaRatingVecs["T"]["y"] : Rating values for the pair.
                slidaRatingVecs["T"]["qids"] : Query ID for the pair.
            qids can be used to determine if the training rows correspond to same query
            string or different.
        """
        # Use NDCG metric.
        self.LambdaMartMetric = pyltr.metrics.NDCG(k=10)
        
        # Monitor progress and stop early.
        self.LambdaMartMonitor = pyltr.models.monitors.ValidationMonitor(
            slideRatingVecs["V"]["X"],
            slideRatingVecs["V"]["y"],
            slideRatingVecs["V"]["qids"],
            metric=self.LambdaMartMetric,
            stop_after=250)

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
        self.LambdaMartModel.fit(
            slideRatingVecs["T"]["X"],
            slideRatingVecs["T"]["y"],
            slideRatingVecs["T"]["qids"],
            monitor=self.LambdaMartMonitor)

        Epred = self.LambdaMartModel.predict(slideRatingVecs["E"]["X"])
        randomRankingMetric = self.LambdaMartMetric.calc_mean_random(
            slideRatingVecs["E"]["qids"],
            slideRatingVecs["E"]["y"])

        ourModelRankingMetric = self.LambdaMartMetric.calc_mean(
            slideRatingVecs["E"]["qids"],
            np.array(slideRatingVecs["E"]["y"]),
           Epred)

        return {
                    "randomRankingMetric": float(randomRankingMetric),
                    "ourModelRankingMetric": float(ourModelRankingMetric)
               }

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
        if ftrVec:
            for (index, score) in enumerate(self.LambdaMartModel.predict(ftrVec)):
                slide = permittedSlides[index]
                retval[index] = score

        # Return the result.
        return retval

    @methodProfiler
    def saveTrainingResult(self, filename):
        """
        Pre Conditions:
            fit has already been called.
            We have already called fit. We are only interested in the result of fit().
            Nothing else is really important.
        Things to save:
            1) self.LambdaMartMetric.
            2) self.LambdaMartMonitor.
            3) self.LambdaMartModel.
        """
        tupleToSave = (self.LambdaMartMetric, self.LambdaMartMonitor, self.LambdaMartModel)
        with open(filename, "wb") as fp:
            pickle.dump(tupleToSave, fp)

    @methodProfiler
    def loadTrainingResult(self, filePointer, schemaVersion):
        """
        Inverse of saveTrainingResult, it loads the data saved by saveTrainingResult().
        """
        if schemaVersion == 1:
            savedTuple = pickle.load(filePointer)
            (self.LambdaMartMetric, self.LambdaMartMonitor, self.LambdaMartModel) = savedTuple
        else:
            raise NotImplemented("Incorrect schema version.")

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

