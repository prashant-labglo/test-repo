import json
from LibLisa import textCleanUp, methodProfiler, blockProfiler, lastCallProfile
from LibLisa.config import lisaConfig

class SlideSearchBase(object):
    """
    Base class of slide search engines.
    """
    def __init__(self, dataForIndexing, config):
        """
        Constructor for SlideSearchW2V takes the path of slide contents file as input.
        """
        self.dataForIndexing = dataForIndexing
        self.config = config

    @methodProfiler
    def permittedSlides(self, queryInfo):
        """
            queryInfo contains filters, which are applied on slides in self.dataForIndexing["Slides"]. Remaining slides are returned.
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
        for slide in self.dataForIndexing["Slides"]:
            if "permittedConstructs" in queryInfo.keys():
                found = False
                for (concept, construct) in queryInfo["permittedConstructs"]:
                    if slide["Concept"] == concept and slide["Construct"] == construct:
                        found = True
                        break
                if not found:
                    # Constraints not met. No Similarity.
                    continue

            if "permittedIcon" in queryInfo.keys():
                if slide["Icon"] != queryInfo["permittedIcon"]:
                    # Constraints not met. No Similarity.
                    continue

            if "permittedImage" in queryInfo.keys():
                if slide["Image"] != queryInfo["permittedImage"]:
                    # Constraints not met. No Similarity.
                    continue

            if "permittedLayout" in queryInfo.keys():
                if slide["Layout"] not in queryInfo["permittedLayouts"]:
                    # Constraints not met. No Similarity.
                    continue

            if "permittedStyle" in queryInfo.keys():
                if slide["Style"] not in queryInfo["permittedStyle"]:
                    # Constraints not met. No Similarity.
                    continue

            if "permittedVisualStyle" in queryInfo.keys():
                if slide["VisualStyle"] not in queryInfo["permittedVisualStyle"]:
                    # Constraints not met. No Similarity.
                    continue
            yield slide

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
        permittedSlides = list(self.permittedSlides(queryInfo))

        # Compute scores of remaining slides.
        slideScores = self.slideSimilarity(queryInfo, permittedSlides)

        # Start building resultList
        resultList = list(enumerate(permittedSlides))

        # Drop slides with negative score.
        # resultList = [(index, slide) for (index, slide) in resultList if slideScores[index] > 0]

        # Sort remaining permitted slides according to score.
        resultList.sort(key = lambda tuple : -slideScores[tuple[0]])

        # Append scores with items in resultList.
        resultList = [(slideScores[index], slide) for (index, slide) in resultList]

        return resultList

def getPath(slide):
    return (slide.parent.name,
            slide.parent.parent.name,
            slide.parent.parent.parent.name)