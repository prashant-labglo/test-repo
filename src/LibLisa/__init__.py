"""
Init file for LibLisa module.
This module contains code which is useful to all Python projects within the solution scope..
"""
import time

from LibLisa.SearchClient import SearchClient
from LibLisa.SlideDbClient import SlideDbClient
from LibLisa.LisaZeptoClient import LisaZeptoClient, textCleanUp
from LibLisa.config import lisaConfig
from LibLisa.behaviors import Behavior

# When profiling function calls for performance, this object stores the timing information
# for later retrieval.
profilingData = [{"Label":"Root", "BreakUp":[]}]

def lastCallProfile():
    """
    This method returns the profiling information of last profiler call made.
    """
    return profilingData[-1]["BreakUp"][-1]

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
        with blockProfiler(method.__name__):
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
        self.curNode = { "BreakUp":[], "Label": label}

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
        self.curNode["TotalTime"] = int((end - self.start) * 1000)

        # Curnode building complete. Now remove from stack and insert it under the calling last node.
        profilingData.pop()
        profilingData[-1]["BreakUp"].append(self.curNode)
