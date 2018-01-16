from socket import gethostname
from attrdict import AttrDict
from enum import Enum

class DeploymentStage(Enum):
    Dev = 0

def LisaConfig():
    retval = AttrDict({
            "behaviorVersion" : 0,
            "IterationPeriod" : 60,
        })

    retval.hostname = gethostname().lower()

    if retval.hostname in ["preze-ntpc", "desktop-tgju8ar"]:
        retval.deploymentStage = DeploymentStage.Dev
        retval.word2vecModelPath = "C:/Users/NishantSharma/source/repos/word2vec-slim/GoogleNews-vectors-negative300-SLIM.bin"
        # retval.word2vecModelPath = "C:/Users/NishantSharma/source/repos/word2vec/GoogleNews-vectors-negative300.bin"

    return retval