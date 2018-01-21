from LibLisa.SlideSearchClient import SlideSearchClient
from LibLisa.WorkflowClient import WorkflowClient
from LibLisa.config import LisaConfig
from LibLisa.behaviors import Behavior
import time

lisaConfig = LisaConfig()

def textCleanUp(jsonObject, badStrings=None, allStrings=None):
    """
    Removes unnecessary whitespace and makes everything lowercase for an arbitrary JSON.
    """
    if (isinstance(jsonObject, str)):
        if badStrings is not None and (" " in jsonObject or "," in jsonObject):
            badStrings.add(jsonObject)
        retval = jsonObject.lower().strip().replace(" ", "_")
        if allStrings is not None:
            allStrings.add(retval)
    elif (isinstance(jsonObject, list)):
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
            jsonObject = set(jsonObject)
            if allStrings is not None:
                allStrings = allStrings.update(jsonObject)
            jsonObject = list(jsonObject)
        retval = jsonObject
    elif (isinstance(jsonObject, dict)):
        retval = {key:textCleanUp(value, badStrings) for (key, value) in jsonObject.items()}
    else:
        retval = jsonObject
        
    return retval

profilingData = [{"Label":"Root", "BreakUp":[]}]

def lastCallProfile():
    return profilingData[-1]["BreakUp"][-1]

def methodProfiler(method):
    """
    Decorator to profile each call of a method.
    """
    def wrapper(*args, **kw):
        with blockProfiler(method.__name__):
            result = method(*args, **kw)
        return result
    return wrapper

class blockProfiler(object):
    def __init__(self, label):
        self.curNode = { "BreakUp":[], "Label": label}

    def __enter__(self):
        # Append cur node
        profilingData.append(self.curNode)
        # Start the timer.
        self.start = time.time()

    def __exit__(self, exception_type, exception_value, traceback):
        # Stop the timer.
        end = time.time()

        # Record time measurement.
        self.curNode["TotalTime"] = int((end - self.start) * 1000)

        # Curnode building complete. Now remove from stack and insert it under the calling last node.
        profilingData.pop()
        profilingData[-1]["BreakUp"].append(self.curNode)
