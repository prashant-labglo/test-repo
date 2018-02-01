from LibLisa.SearchClient import SearchClient
from LibLisa.SlideDbClient import SlideDbClient
from LibLisa.LisaPhpClient import LisaPhpClient, textCleanUp
from LibLisa.config import lisaConfig
from LibLisa.behaviors import Behavior
import time


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
