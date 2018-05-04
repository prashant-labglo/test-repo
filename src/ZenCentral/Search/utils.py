from SlideDB.models import Slide
from SlideSearch.SlideSearchBase import SlideSearchBase


def normalizeQueryJson(queryJson):
    """
    Function to transform query_json such that equivalent query_json map into the same object. Transformations include
    removing keys which have default values e.g.("IsEnabled", "IncludeDisabledHierarchy").
    """

    if type(queryJson) != dict:
        raise TypeError("Input must be a dictionary.")

    if "Keywords" not in queryJson or not queryJson["Keywords"]:
        queryJson["Keywords"] = []
    elif isinstance(queryJson["Keywords"], str):
        queryJson["Keywords"] = [queryJson["Keywords"]]

    filter_in_keywords = []
    filter_out_keywords = []
    score_keywords = []
    for word in queryJson["Keywords"]:
        if word[0] == "+":
            filter_in_keywords.append(word[1:])
        elif word[0] == "-":
            filter_out_keywords.append(word[1:])
        else:
            score_keywords.append(word)
    if filter_in_keywords:
        queryJson["FilterInKeywords"] = [word.lower() for word in filter_in_keywords]
    if filter_out_keywords:
        queryJson["FilterOutKeywords"] = [word.lower() for word in filter_out_keywords]
    if score_keywords:
        queryJson["ScoreKeywords"] = [word.lower() for word in score_keywords]

    del queryJson["Keywords"]

    if "HasIcon" in queryJson:
        queryJson["HasIcon"] = True if queryJson["HasIcon"] else False

    if "HasImage" in queryJson:
        queryJson["HasImage"] = True if queryJson["HasImage"] else False

    if "IsEnabled" in queryJson:
        if queryJson["IsEnabled"]:
            del (queryJson["IsEnabled"])
        else:
            queryJson["IsEnabled"] = False

    if "IncludeDisabledHierarchy" in queryJson:
        if queryJson["IncludeDisabledHierarchy"]:
            queryJson["IncludeDisabledHierarchy"] = True
        else:
            del (queryJson["IncludeDisabledHierarchy"])

    return queryJson


def getPermittedSlides(queryInfo):
    """ Method to return only permitted slide after filtering with all keys values. """

    slides_qset = Slide.objects.all().distinct()

    if queryInfo.get("IsEnabled", True):
        slides_qset = slides_qset.filter(enabled=True)

    if "FilterInKeywords" in queryInfo.keys():
        slides_qset = slides_qset.filter(tags__name__in=queryInfo["FilterInKeywords"])

    if "FilterOutKeywords" in queryInfo.keys():
        slides_qset = slides_qset.exclude(tags__name__in=queryInfo["FilterOutKeywords"])

    if "Constructs" in queryInfo.keys():
        slides_qset = slides_qset.filter(parent__id__in=queryInfo["Constructs"])

    if "HasIcon" in queryInfo.keys():
        slides_qset = slides_qset.filter(hasIcon=queryInfo["HasIcon"])

    if "HasImage" in queryInfo.keys():
        slides_qset = slides_qset.filter(hasImage=queryInfo["HasImage"])

    permitted_slides = []
    for slide in slides_qset:
        if "Layout" in queryInfo.keys():
            if getattr(slide, "layout") not in queryInfo["Layout"]:
                # Constraints not met. No Similarity.
                continue

        if "Style" in queryInfo.keys():
            if getattr(slide, "Style") not in queryInfo["Style"]:
                # Constraints not met. No Similarity.
                continue

        if "VisualStyle" in queryInfo.keys():
            if str(getattr(slide, "visualStyle")).lower() not in queryInfo["VisualStyle"]:
                # Constraints not met. No Similarity.
                continue

        if not (queryInfo.get("IncludeDisabledHierarchy", False)):
            construct = getattr(slide, "parent")
            subConcept = getattr(construct, "parent")
            concept = getattr(subConcept, "parent")
            if not (getattr(concept, "enabled")) or not \
                    (getattr(subConcept, "enabled")) or not \
                    (getattr(construct, "enabled")):
                continue

        permitted_slides.append(slide)

    return permitted_slides
