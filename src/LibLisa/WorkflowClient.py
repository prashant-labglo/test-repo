"""
Workflow client is a REST API client which can make queries to the Workflow REST API service.
"""

from LibLisa.behaviors import Behavior
from LibLisa.RestClient import RestClient

class WorkflowClient(RestClient):
    def __init__(self, behaviorVersion, deploymentStage):
        """
        Params:
            deploymentStage is the stage of deployment. It can be any of dev, int, test, ppe, prod etc.
        """
        if behavoirVersion == Behavior.LisaZeptoInitial:
            baseURL = "http://www.prezentium.com/tools/prezentiumadmin/prezentiumslide/slidelist_json"
        else:
            raise NotImplementedError("Behavior {0} not supported.".format(behaviorVersion))
        
        super().__init__(baseURL)