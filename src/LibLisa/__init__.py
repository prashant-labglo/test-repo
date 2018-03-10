"""
Init file for LibLisa module.
This module contains code which is useful to all Python projects within the solution scope..
"""
import time, contextlib, requests, functools, warnings
from collections import OrderedDict

from LibLisa.config import lisaConfig
from LibLisa.behaviors import Behavior

# When profiling function calls for performance, this object stores the timing information
# for later retrieval.
profilingData = [OrderedDict({ "Label": "Root", "BreakUp":[] })]

def lastCallProfile(doPop=False):
    """
    This method returns the profiling information of last profiler call made.
    """
    retval = profilingData[-1]["BreakUp"][-1]
    if doPop:
        profilingData[-1]["BreakUp"].pop()

    return retval

def methodProfiler(method):
    """
    Decorator to profile each call of a method.
    To use this profiler, annotate the function with this decorator.
    Then, every call to that method will get profiled and data stored in profilingData
    variable above. The data can be retrieved by using lastCallProfile() function.

    @methodProfiler
    def funcToProfile():
        pass

    """
    def wrapper(*args, **kw):
        with blockProfiler(method.__qualname__):
            result = method(*args, **kw)
        return result
    return wrapper

class blockProfiler(object):
    """
    Any code block can be profiled by using blockProfiler class.
    Use it as follows.

    with blockProfiler("labelOfBlock"):
        CodeBeingProfiled1()
        CodeBeingProfiled2()
    """
    def __init__(self, label):
        """
        Initialization.
        """
        self.curNode = OrderedDict({ "Label": label, "BreakUp":[] })

    def __enter__(self):
        """
        When we enter the with block, this code is executed.
        """
        # Append cur node
        profilingData.append(self.curNode)
        # Start the timer.
        self.start = time.time()

    def __exit__(self, exception_type, exception_value, traceback):
        """
        When we exit the with block, this code is executed.
        """
        # Stop the timer.
        end = time.time()

        # Record time measurement.
        self.curNode["MilliSeconds"] = int((end - self.start) * 1000)
        self.curNode.move_to_end("BreakUp")

        # Curnode building complete. Now remove from stack and insert it under the calling last node.
        profilingData.pop()
        profilingData[-1]["BreakUp"].append(self.curNode)

class no_ssl_verification_session(requests.sessions.Session):
    """
    This class overrides send method of requests.sessions.Session class.
    It inserts argument verify=False in the send method of the said class.

    Useful in skipping certificate check when required.
    """
    def send(self, request, **kwargs):
        kwargs["verify"] = False
        return super().send(request, **kwargs)

@contextlib.contextmanager
def check_ssl_certs(enabled):
    """
    Sometimes we want to make https requests without certificate verification.
    This function does that.
    """
    if enabled:
        # Override request method in module requests.Session to pass verify=False.
        old_request = requests.Session.request
        requests.Session.request = functools.partialmethod(old_request, verify=False)

        # Override Session class in module requests and requests.sessions to pass
        # verify=False when needed.
        old_session_class = requests.sessions.Session
        requests.sessions.Session = no_ssl_verification_session
        requests.Session = no_ssl_verification_session
        warnings.filterwarnings('ignore', 'Unverified HTTPS request')
        
    yield

    if enabled:
        warnings.resetwarnings()

        # Undo override request method in module requests.Session.
        requests.Session.request = old_request

        # Undo override Session class in module requests and requests.sessions.
        requests.Session = old_session_class
        requests.sessions.Session = old_session_class
    
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
            if badStrings is not None:
                for item in jsonObject:
                    if "," in item:
                        badStrings.add(item)
            jsonObject = ",".join(jsonObject).split(",")
        else:
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
