from attrdict import AttrDict
from enum import Enum

class Behavior(Enum):
    LisaZeptoInitial = 0

class DeploymentStage(Enum):
    Dev = 0

def LisaConfig():
    retval = {
            "behaviorVersion" : 0,
            "deploymentStage" : DeploymentStage.Dev,
            "IterationPeriod" : 60,
        }

    retval = AttrDict(retval)

    return retval