import json
from attrdict import AttrDict
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
    def getPermittedSlides(self, queryInfo):
        """
            ********** IMPORTANT *********
            Any change here MUST be reflected in method getPermittedSlidesDbOptimized(file ZenCentral/Search/utils.py)
            *********** IMPORTANT *********

            queryJson contains filters, which are applied on slides in self.dataForIndexing["Slides"]. Remaining slides are returned.
            queryJson schema can be as below.
            {
                # Mandatory
                "Keywords" : ["keyword1", "keyword2", "keyword3", ...]

                # Optional
                "Constructs" : [permittedConstructId1, permittedConstructId2, ...],

                # Optional
                "HasIcon"  : True | False,

                # Optional
                "HasImage"  : True | False,

                # Optional
                "Layout"  : ["permittedLayout1", ...],

                # Optional
                "Style"  : ["permittedStyle1", ...],

                # Optional
                "VisualStyle"  : ["permittedVisualStyle1", ...],
            }
        """
        for slide in self.dataForIndexing["Slides"]:
            tags_list = self.getTags(slide)
            doRejectSlide = False
            if "FilterInKeywords" in queryInfo.keys():
                for word in queryInfo["FilterInKeywords"]:
                    if word not in tags_list:
                        doRejectSlide = True
                        break

            if "FilterOutKeywords" in queryInfo.keys():
                for word in queryInfo["FilterOutKeywords"]:
                    if word in tags_list:
                        doRejectSlide = True
                        break
            if doRejectSlide:
                continue

            if "Constructs" in queryInfo.keys():
                slideConstruct = self.getAttr(slide, "parent")
                if self.getAttr(slideConstruct, "id") not in queryInfo["Constructs"]:
                    continue

            if "HasIcon" in queryInfo.keys():
                if self.getAttr(slide, "hasIcon") != queryInfo["HasIcon"]:
                    # Constraints not met. No Similarity.
                    continue

            if "HasImage" in queryInfo.keys():
                if self.getAttr(slide, "hasImage") != queryInfo["HasImage"]:
                    # Constraints not met. No Similarity.
                    continue

            if "Layout" in queryInfo.keys():
                if self.getAttr(slide, "layout") not in queryInfo["Layout"]:
                    # Constraints not met. No Similarity.
                    continue

            if "Style" in queryInfo.keys():
                if self.getAttr(slide, "Style") not in queryInfo["Style"]:
                    # Constraints not met. No Similarity.
                    continue

            if "Content" in queryInfo.keys():
                if self.getAttr(slide, "content") not in queryInfo["Content"]:
                    # Constraints not met. No Similarity.
                    continue

            if "VisualStyle" in queryInfo.keys():
                if str(self.getAttr(slide, "visualStyle")).lower() not in queryInfo["VisualStyle"]:
                    # Constraints not met. No Similarity.
                    continue

            if queryInfo.get("IsEnabled", True):
                if not (self.getAttr(slide, "enabled")):
                    # Constraints not met. No Similarity.
                    continue

            if not (queryInfo.get("IncludeDisabledHierarchy", False)):
                construct = self.getAttr(slide, "parent")
                subConcept = self.getAttr(construct, "parent")
                concept = self.getAttr(subConcept, "parent")
                if not (self.getAttr(concept, "enabled")) or not (self.getAttr(subConcept, "enabled")) or not \
                        (self.getAttr(construct, "enabled")):
                    continue

            yield slide

    def slideSimilarity(self, queryInfo, permittedSlides):
        raise NotImplementedError("Derived classes must define this function.")

    @methodProfiler
    def slideSearch(self, queryInfo, permittedSlideList, getIDs=False):
        """
        Gets a query JSON as input. Computes similarity of the query JSON with all indexed slides and 
        returns all of them sorted in the order of best match.
        """
        queryInfo = textCleanUp(queryInfo)

        # Compute scores of remaining slides.
        slideScores = self.slideSimilarity(queryInfo, permittedSlideList)

        # Start building resultList
        resultList = list(enumerate(permittedSlideList))

        # Drop slides with negative score.
        # resultList = [(index, slide) for (index, slide) in resultList if slideScores[index] > 0]

        # Sort remaining permitted slides according to score.
        resultList.sort(key = lambda tuple : -slideScores[tuple[0]])

        # Append scores with items in resultList.
        if getIDs:
            resultList = [(slideScores[index], self.getAttr(slide, "id")) for (index, slide) in resultList]
        else:
            resultList = [(slideScores[index], slide) for (index, slide) in resultList]

        return resultList

    def getParent(self, slide):
        if self.config["isDjangoModel"]:
            return slide.parent
        else:
            return slide["parent"]

    def getPath(self, slide):
        if self.config["isDjangoModel"]:
            return (slide.parent.name,
                    slide.parent.parent.name,
                    slide.parent.parent.parent.name)
        else:
            return (slide["parent"]["name"],
                    slide["parent"]["parent"]["name"],
                    slide["parent"]["parent"]["parent"]["name"])

    def getTags(self, slide):
        if self.config["isDjangoModel"]:

            return slide.tags.names()
        else:
            return slide["tags"]

    def getAttr(self, slide, attr):
        if self.config["isDjangoModel"]:
            return getattr(slide, attr)
        else:
            return slide[attr]
