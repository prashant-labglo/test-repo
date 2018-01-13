from attrdict import AttrDict
from enum import Enum

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