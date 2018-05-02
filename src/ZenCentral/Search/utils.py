
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
    keywords = []
    for word in queryJson["Keywords"]:
        if word[0] == "+":
            filter_in_keywords.append(word[1:])
        elif word[0] == "-":
            filter_out_keywords.append(word[1:])
        else:
            keywords.append(word)
    if filter_in_keywords:
        queryJson["FilterInKeywords"] = [word.lower() for word in filter_in_keywords]
    if filter_out_keywords:
        queryJson["FilterOutKeywords"] = [word.lower() for word in filter_out_keywords]
    if keywords:
        queryJson["Keywords"] = [word.lower() for word in keywords]

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
