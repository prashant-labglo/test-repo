"""
Implements CoreApiRestClient base class. Acts as a base class to any client which
needs to talk to Django ZenClient.
"""
import coreapi, os, json
from attrdict import AttrDict
from LibLisa.RestClient import RestClient
from LibLisa import lisaConfig, check_ssl_certs

class CoreApiRestClient(RestClient):
    """
    CoreApiRestClient class acts as base class to any application client which
    needs to talk to Django ZenClient.
    """
    def __init__(self, config):
        super().__init__(config.BaseUrl)
        self.config = config
        self.schemaURL = self.baseURL + "schema"

    def login(self):
        """
        Logs into SlideDB backed. 
        It is required to be called, before we download any data.
        """
        #self.auth = coreapi.auth.BasicAuthentication(
        #    username=self.config.Username,
        #    password=self.config.Password
        #)
        #self.client = coreapi.Client(auth=self.auth)
        with check_ssl_certs(lisaConfig.ssl_verify):
            self.client = coreapi.Client()
            self.schema = self.client.get(self.schemaURL)

    def getModelInstances(self, modelName):
        """
        Given the model name, it downloads all instances of the model, served by
        the REST API.
        """
        fileName = modelName + ".json"

        attoModels = []
        pageSize = 1000
        while True:
            paramsDict = {'offset': len(attoModels), 'limit': pageSize}
            response = self.client.action(self.schema, [self.config.appName, modelName.lower(), 'list'], params=paramsDict)
            if response["results"]:
                attoModels.extend(response["results"])
            else:
                break

        with open(fileName, "w") as fp:
            json.dump(attoModels, fp, indent=4)

        return attoModels

