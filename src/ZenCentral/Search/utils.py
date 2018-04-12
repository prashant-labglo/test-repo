
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

    queryJson["Keywords"] = [word.lower() for word in queryJson["Keywords"]]

    return queryJson
