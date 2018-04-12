
def normalizeQueryJson(query_json):
    """
    Function to remove the key which having default values i.e ("Keywords", "IsEnabled", "IncludeDisabledHierarchy")
    """

    if type(query_json) != dict:
        raise TypeError("Input must be a dictionary.")

    # Delete if keys having default values
    if "IsEnabled" in list(query_json.keys()):
        if query_json["IsEnabled"]:
            del query_json["IsEnabled"]
    if "IncludeDisabledHierarchy" in list(query_json.keys()):
        if not query_json["IncludeDisabledHierarchy"]:
            del query_json["IncludeDisabledHierarchy"]

    return query_json
