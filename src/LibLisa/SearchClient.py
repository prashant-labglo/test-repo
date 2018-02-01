"""
Slide search client is a REST API client which can make queries to ZenCentral REST API.
"""
from LibLisa.behaviors import Behavior
from LibLisa.RestClient import RestClient
from LibLisa.config import lisaConfig

class SearchClient(RestClient):
    def __init__(self):
        """
        Params:
            deploymentStage is the stage of deployment. It can be any of dev, int, test, ppe, prod etc.
        """
        if lisaConfig.behaviorVersion == Behavior.LisaZeptoInitial:
            baseURL = "http://www.prezentium.com/tools/prezentiumadmin/prezentiumslide/slidelist_json"
        else:
            raise NotImplementedError("Behavior {0} not supported.".format(lisaConfig.behaviorVersion))
        
        super().__init__(baseURL)