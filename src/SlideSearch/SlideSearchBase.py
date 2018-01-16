import json
from LibLisa import textCleanUp

class SlideSearchBase(object):
    """
    Base class of slide search engines.
    """
    def __init__(self, slideInfoFilepath):
        """
        Constructor for SlideSearchW2V takes the path of slide contents file as input.
        """
        with open(slideInfoFilepath, "r", encoding="utf8") as fp:
            slideInfoSet = json.load(fp)
            slideInfoSet = slideInfoSet["results"]
        badStrings = set()
        allStrings = set()
        self.slideInfoSet = textCleanUp(slideInfoSet, badStrings, allStrings)
        self.badStrings = badStrings
        for badString in badStrings:
            print(badString)

        for slideInfo in self.slideInfoSet:
            # Replace path elements with path.
            slideInfo["Path"] = (slideInfo["Concept"], slideInfo["SubConcept"], slideInfo["Construct"])
            del slideInfo["Concept"]
            del slideInfo["SubConcept"]
            del slideInfo["Construct"]

            # Set up booleans.
            for booleanAttr in ["Icon", "Image"]:
                slideInfo[booleanAttr] = True if (slideInfo[booleanAttr] == "yes") else False

        json.dump(self.slideInfoSet, open(slideInfoFilepath + "Cleaned.json", "w"), indent=2)

    def slideSimilarity(self, queryInfo, slideInfo):
        """
            QueryJson can be of the following form.
            {
                # Optional
                "Keywords" : ["keyword1", "keyword2", ...],

                # Optional
                "permittedConstructs" : [
                    ("permittedConcept1", "permittedSubConcept1", "PermittedConstruct1"),
                    ("permittedConcept2", "permittedSubConcept2", "PermittedConstruct2"),
                    ("permittedConcept3", "permittedSubConcept3", "PermittedConstruct3"),
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
        queryInfo = textCleanUp(queryInfo)
        if "permittedConstructs" in queryInfo.keys():
            found = False
            for (concept, subConcept, construct) in queryInfo["permittedConstructs"]:
                if slideInfo["Concept"] == concept and slideInfo["SubConcept"] == subConcept and slideInfo["Construct"] == construct:
                    found = True
                    break
            if not found:
                # Constraints not met. No Similarity.
                return -2

        if "permittedIcon" in queryInfo.keys():
            if slideInfo["Icon"] != queryInfo["permittedIcon"]:
                # Constraints not met. No Similarity.
                return -2

        if "permittedImage" in queryInfo.keys():
            if slideInfo["Image"] != queryInfo["permittedImage"]:
                # Constraints not met. No Similarity.
                return -2

        if "permittedLayout" in queryInfo.keys():
            if slideInfo["Layout"] not in queryInfo["permittedLayouts"]:
                # Constraints not met. No Similarity.
                return -2

        if "permittedStyle" in queryInfo.keys():
            if slideInfo["Style"] not in queryInfo["permittedStyle"]:
                # Constraints not met. No Similarity.
                return -2

        if "permittedVisualStyle" in queryInfo.keys():
            if slideInfo["VisualStyle"] not in queryInfo["permittedVisualStyle"]:
                # Constraints not met. No Similarity.
                return -2

        return self.queryPhrase2TagsetSimilarity(queryInfo["Keywords"], slideInfo["Tags"])

    def slideSearch(self, queryInfo):
        """
        Gets a query JSON as input. Computes similarity of the query JSON with all indexed slides and 
        returns all of them sorted in the order of best match.
        """
        resultList = []
        for slideInfo in self.slideInfoSet:
            slideScore = self.slideSimilarity(queryInfo, slideInfo)
            if slideScore > 0:
                resultList.append((slideScore, slideInfo))

        resultList.sort(key = lambda tuple : tuple[0])
        return resultList
