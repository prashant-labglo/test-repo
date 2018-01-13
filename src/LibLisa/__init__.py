from SlideSearchClient import SlideSearchClient
from WorkflowClient import WorkflowClient
from config import LisaConfig
from behaviors import Behavior

lisaConfig = LisaConfig()

def textCleanUp(jsonObject, badStrings=None):
    """
    Removes unnecessary whitespace and makes everything lowercase for an arbitrary JSON.
    """
    if (isinstance(jsonObject, str)):
        if badStrings is not None and (" " in jsonObject or "," in jsonObject):
            badStrings.add(jsonObject)
        return jsonObject.lower().strip().replace(" ", "_")
    if (isinstance(jsonObject, list)):
        # Some of the strings are of kind "a, b". They should be flattened into list.
        if any([isinstance(item, str) and "," in item for item in jsonObject]):
            badStrings.add(jsonObject[0])
            jsonObject = ",".join(jsonObject).split(",")

        # If we are not dealing with list of strings, then we need to clean them up, recursively.
        jsonObject = [textCleanUp(item, badStrings) for item in jsonObject]

        # Remove empty string
        jsonObject = [item for item in jsonObject if item]

        # Remove duplicates if we are dealing with list of strings.
        if all([isinstance(item, str) for item in jsonObject]):
            jsonObject = list(set(jsonObject))
        return jsonObject

    if (isinstance(jsonObject, dict)):
        return {key:textCleanUp(value, badStrings) for (key, value) in jsonObject.items()}
    return jsonObject

