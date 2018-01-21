import json
from LibLisa import textCleanUp, methodProfiler, blockProfiler, lastCallProfile

class SlideSearchBase(object):
    """
    Base class of slide search engines.
    """
    def __init__(self, slideInfoFilepath):
        """
        Constructor for SlideSearchW2V takes the path of slide contents file as input.
        """
        with blockProfiler("SlideSearchBase.__init__"):
            with open(slideInfoFilepath, "r", encoding="utf8") as fp:
                slideInfoSet = json.load(fp)
                slideInfoSet = slideInfoSet["results"]

            # Check for duplicate slide records, for the same slide file.
            slidePaths = set([slideInfo["Slide"] for slideInfo in slideInfoSet])
            pathToSlideIds = {slidePath:[] for slidePath in slidePaths}
            for slideInfo in slideInfoSet:
                pathToSlideIds[slideInfo["Slide"]].append(slideInfo["ID"])
            self.duplicateSlideIds = [(k, v) for (k, v) in pathToSlideIds.items() if len(v) != 1]
            json.dump(self.duplicateSlideIds, open("debugDuplicateSlideIDs.json", "w"), indent=2)

            # Cleanup text and build a set of bad strings and all strings.
            badStrings = set()
            allStrings = set()
            self.slideInfoSet = textCleanUp(slideInfoSet, badStrings, allStrings)
            self.badStrings = badStrings
            for badString in badStrings:
                print(badString)

            for (index, slideInfo) in enumerate(self.slideInfoSet):
                # Replace path elements with path.
                slideInfo["Path"] = (slideInfo["Concept"], slideInfo["Construct"])
                del slideInfo["Concept"]
                del slideInfo["Construct"]

                # Set up booleans.
                for booleanAttr in ["Icon", "Image"]:
                    slideInfo[booleanAttr] = True if (slideInfo[booleanAttr] == "yes") else False

                slideInfo["Index"] = index
            json.dump(self.slideInfoSet, open(slideInfoFilepath + "Cleaned.json", "w"), indent=2)

    @methodProfiler
    def permittedSlides(self, queryInfo):
        """
            queryInfo contains filters, which are applied on slides in slideInfoSet. Remaining slides are returned.
            queryInfo filters can be as below.
            {
                # Optional
                "permittedConstructs" : [
                    ("permittedConcept1", "PermittedConstruct1"),
                    ("permittedConcept2", "PermittedConstruct2"),
                    ("permittedConcept3", "PermittedConstruct3"),
                    ...
                ],

                # Optional
                "permittedIcon"  : True | False,

                # Optional
                "permittedImage"  : True | False,

                # Optional
                "permittedStyle"  : True | False,

                # Optional
                "permittedVisualStyle"  : True | False
            }
        """
        for slideInfo in self.slideInfoSet:
            if "permittedConstructs" in queryInfo.keys():
                found = False
                for (concept, construct) in queryInfo["permittedConstructs"]:
                    if slideInfo["Concept"] == concept and slideInfo["Construct"] == construct:
                        found = True
                        break
                if not found:
                    # Constraints not met. No Similarity.
                    continue

            if "permittedIcon" in queryInfo.keys():
                if slideInfo["Icon"] != queryInfo["permittedIcon"]:
                    # Constraints not met. No Similarity.
                    continue

            if "permittedImage" in queryInfo.keys():
                if slideInfo["Image"] != queryInfo["permittedImage"]:
                    # Constraints not met. No Similarity.
                    continue

            if "permittedLayout" in queryInfo.keys():
                if slideInfo["Layout"] not in queryInfo["permittedLayouts"]:
                    # Constraints not met. No Similarity.
                    continue

            if "permittedStyle" in queryInfo.keys():
                if slideInfo["Style"] not in queryInfo["permittedStyle"]:
                    # Constraints not met. No Similarity.
                    continue

            if "permittedVisualStyle" in queryInfo.keys():
                if slideInfo["VisualStyle"] not in queryInfo["permittedVisualStyle"]:
                    # Constraints not met. No Similarity.
                    continue
            yield slideInfo

    def slideSimilarity(self, queryInfo, permittedSlides):
        raise NotImplementedError("Derived classes must define this function.")

    @methodProfiler
    def slideSearch(self, queryInfo):
        """
        Gets a query JSON as input. Computes similarity of the query JSON with all indexed slides and 
        returns all of them sorted in the order of best match.
        """
        queryInfo = textCleanUp(queryInfo)

        # Apply filter part of queryInfo.
        resultList = list(self.permittedSlides(queryInfo))

        # Compute scores of remaining slides.
        slideScores = self.slideSimilarity(queryInfo, resultList)

        # Drop slides with negative score.
        resultList = [slideInfo for slideInfo in resultList if slideScores[slideInfo["Index"]] > 0]

        # Sort remaining permitted slides according to score.
        resultList.sort(key = lambda slideInfo : -slideScores[slideInfo["Index"]])

        # Append scores with items in resultList.
        resultList = [(slideScores[slideInfo["Index"]], slideInfo) for slideInfo in resultList]

        return resultList