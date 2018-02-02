"""
SlideDB client is a REST API client which can make queries to the 
Django based REST API service to do CRUD operations of slide hierarchy.
"""

import requests, coreapi, time
from lxml import html

from LibLisa.behaviors import Behavior
from LibLisa.RestClient import RestClient
from LibLisa.config import lisaConfig

class SlideDbClient(object):
    """
        SlideDB client is a REST API client which can make queries to the 
        Django based REST API service to do CRUD operations of slide hierarchy.
    """
    def __init__(self):
        """
        Constructor
        """
        self.config = lisaConfig.slideDb
        self.baseURL = self.config.BaseUrl
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

    def syncWithZepto(self, zeptoData):
        """
        All Lisa PHP data can be pushed into ZenClient SlideDB using this call.
        """
        def getModelUrl(modelObj):
            if "parent" not in modelObj.keys():
                modelType = "Concept"
            elif "parent" not in modelObj["parent"].keys():
                modelType = "SubConcept"
            elif "parent" not in modelObj["parent"]["parent"].keys():
                modelType = "Construct"
            else:
                modelType = "Slide"

            return self.baseURL + "slidedb/" + modelType.lower() + "s/" + str(modelObj["id"]) + "/"
        for modelName in ["Concepts", "SubConcepts", "Constructs", "Slides"]:
            # Get all model instances on the Atto side.
            attoModels = self.client.action(self.schema, ['slidedb', modelName.lower(), 'list'])

            # Convert the read models into a dictionary mapping from model's zepto id to model instance.
            attoModels = {attoModel["zeptoId"] : attoModel for attoModel in attoModels}

            zeptoModelsDict = {zeptoModel["zeptoId"] : zeptoModel for zeptoModel in zeptoData[modelName] }

            # Update all model instances, that already exist on Atto side.
            for (attoModelZeptoId, attoModel) in attoModels.items():
                if attoModelZeptoId not in zeptoModelsDict.keys():
                    # Delete all atto model instances, which don't have a corresponding presence in Zepto.
                    retval = self.client.action(self.schema, ['slidedb', modelName.lower(), 'delete'], {"id" : attoModel["id"]})
                    zeptoModel["id"] = int(retval)
                else:
                    # This is an atto model instance with a matching entry in zeptoModels also.

                    # Update all DB slides with a presence in latestSlides, which changed.
                    zeptoModel = zeptoModelsDict[attoModelZeptoId]
                    zeptoModel["id"] = attoModel["id"]
                    zeptoModelCopy = dict(zeptoModel)
                    if modelName != "Concepts":
                        zeptoModelCopy["parent"] = getModelUrl(zeptoModel["parent"])
                    changes = {}
                    for (key, value) in zeptoModelCopy.items():
                        if key == "tags":
                            if set(value) != set(attoModel[key]):
                                changes[key] = value
                        else:
                            if value != attoModel[key]:
                                changes[key] = value

                    if changes:
                        changes["id"] = attoModel["id"]
                        self.client.action(self.schema, ['slidedb', modelName.lower(), 'partial_update'], changes)

            for (zeptoModelId, zeptoModel) in zeptoModelsDict.items():
                if zeptoModelId not in attoModels.keys():
                    zeptoModelCopy = dict(zeptoModel)
                    if modelName != "Concepts":
                        zeptoModelCopy["parent"] = getModelUrl(zeptoModel["parent"])
                    retval = self.client.action(self.schema, ['slidedb', modelName.lower(), 'create'], zeptoModelCopy)
                    zeptoModel['id'] = retval['id']

        # Move training code invocation from searchIndex.py to here.
        # Train based on latest changes(Try to pass data entries directly).
        # Training information is kept in a file.
        # Dump training data into file type field.

        # In serchIndex.py, let it reload training from training file.