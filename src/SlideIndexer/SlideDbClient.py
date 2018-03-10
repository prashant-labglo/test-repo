"""
SlideDB client is a REST API client which can make queries to the 
Django based REST API service to do CRUD operations of slide hierarchy.
"""

import requests, coreapi, time, os
from lxml import html

from LibLisa.behaviors import Behavior
from LibLisa.CoreApiRestClient import CoreApiRestClient
from LibLisa.config import lisaConfig

class SlideDbClient(CoreApiRestClient):
    """
        SlideDB client is a REST API client which can make queries to the 
        Django based REST API service to do CRUD operations of slide hierarchy.
    """
    def __init__(self):
        """
        Constructor
        """
        super().__init__(lisaConfig.slideDb)

    def getModelUrl(self, modelObj):
        """
        Gets URL of an atto model object.
        """
        if "parent" not in modelObj.keys():
            modelType = "Concept"
        elif "parent" not in modelObj["parent"].keys():
            modelType = "SubConcept"
        elif "parent" not in modelObj["parent"]["parent"].keys():
            modelType = "Construct"
        else:
            modelType = "Slide"

        return self.baseURL + "slidedb/" + modelType.lower() + "s/" + str(modelObj["id"]) + "/"

    def getSlideHierarchy(self):
        slideHierarchy = {}
        parentFinderDict = None
        for modelName in ["Concepts", "SubConcepts", "Constructs", "Slides"]:
            # Get all model instances on the Atto side.
            slideHierarchy[modelName] = self.getModelInstances(modelName)

            # Use parentFinderDict to find parents of all model instances.
            if parentFinderDict is not None:
                for modelInstance in slideHierarchy[modelName]:
                    parentId = int(os.path.basename(modelInstance["parent"].strip("/")))
                    modelInstance["parent"] = parentFinderDict[parentId]

            # Update parentFinderDict for next iteration.
            parentFinderDict = {}
            for modelInstance in slideHierarchy[modelName]:
                parentFinderDict[modelInstance["id"]] = modelInstance

        return slideHierarchy

    def syncWithZepto(self, zeptoData, attoData):
        """
        All Lisa Zepto data can be pushed into ZenClient SlideDB using this call.
        """
        for modelName in ["Concepts", "SubConcepts", "Constructs", "Slides"]:
            # Get all model instances on the Atto side.
            attoModels = attoData[modelName]

            # Convert the read models into a dictionary mapping from model's zepto id to model instance.
            attoModels = {attoModel["zeptoId"] : attoModel for attoModel in attoModels}
            zeptoModelsDict = {zeptoModel["zeptoId"] : zeptoModel for zeptoModel in zeptoData[modelName] }

            # Update all model instances, that already exist on Atto side.
            for (attoModelZeptoId, attoModel) in attoModels.items():
                if attoModelZeptoId not in zeptoModelsDict.keys():
                    # Delete all atto model instances, which don't have a corresponding presence in Zepto.
                    retval = self.client.action(self.schema, [self.config.appName, modelName.lower(), 'delete'], {"id" : attoModel["id"]})
                else:
                    # This is an atto model instance with a matching entry in zeptoModels also.
                    # We need to update the attoModel with info from zeptoModel.
                    zeptoModel = zeptoModelsDict[attoModelZeptoId]
                    zeptoModel["id"] = attoModel["id"]
                    changes = {}
                    for (key, value) in zeptoModel.items():
                        if key == "tags":
                            if set(value) != set(attoModel[key]):
                                changes[key] = value
                        elif key == "parent":
                            if value["id"] != attoModel[key]["id"]:
                                changes[key] = self.getModelUrl(value)
                        else:
                            if value != attoModel[key]:
                                changes[key] = value

                    if changes:
                        # Apply all changes into the atto server's copy.
                        changes["id"] = attoModel["id"]
                        print("Applying changes {0} to {1}", changes, self.getModelUrl(attoModel))
                        self.client.action(self.schema, [self.config.appName, modelName.lower(), 'partial_update'], changes)

            # Iterate over zeptoModelsDict to find newly created entries on the zepto side.
            for (zeptoModelId, zeptoModel) in zeptoModelsDict.items():
                if zeptoModelId not in attoModels.keys():
                    zeptoModelCopy = dict(zeptoModel)
                    if modelName != "Concepts":
                        zeptoModelCopy["parent"] = self.getModelUrl(zeptoModel["parent"])
                    retval = self.client.action(self.schema, [self.config.appName, modelName.lower(), 'create'], zeptoModelCopy)
                    zeptoModel['id'] = retval['id']
