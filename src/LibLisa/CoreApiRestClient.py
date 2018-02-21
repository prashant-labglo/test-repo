import coreapi, os, json
from attrdict import AttrDict
from LibLisa.RestClient import RestClient

class CoreApiRestClient(RestClient):
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
        self.client = coreapi.Client()
        self.schema = self.client.get(self.schemaURL)

    def getModelInstances(self, modelName):
        fileName = modelName + ".json"

        attoModels = []
        curOffset = 0
        while True:
            paramsDict = {'offset': curOffset, 'limit': 100}
            response = self.client.action(self.schema, [self.config.appName, modelName.lower(), 'list'], params=paramsDict)
            if response["results"]:
                attoModels.extend(response["results"])
                curOffset += 100
            else:
                break

        with open(fileName, "w") as fp:
            json.dump(attoModels, fp, indent=4)

        return attoModels

