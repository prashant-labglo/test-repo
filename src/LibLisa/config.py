"""
File which builds configuration object for all services in the solution.
"""
from socket import gethostname
from attrdict import AttrDict
from enum import Enum
from LibLisa.behaviors import Behavior

class DeploymentStage(Enum):
    """
    Enum representing the stage of deployment where the current service is running.
    """
    Dev = 0

def LisaConfig():
    """
    Function which builds the configuration object.
    """
    retval = AttrDict({
            "behaviorVersion" : Behavior(0),
            "IterationPeriod" : 60,
        })

    retval.hostname = gethostname().lower()

    retval.deploymentStage = DeploymentStage.Dev
    # Build and set LisaPhp client config.
    lisaPhpConfig = AttrDict()
    lisaPhpConfig.BaseUrl = "http://www.prezentium.com/tools/"
    lisaPhpConfig.Username = "admin"
    lisaPhpConfig.Password = "$kpres!A@417"
    retval.lisaPhp = lisaPhpConfig

    # Build and set SlideDbClient config.
    slideDbConfig = AttrDict()
    slideDbConfig.BaseUrl = "http://localhost:8000/"
    slideDbConfig.Username = "test"
    slideDbConfig.Password = "test"
    retval.slideDb = slideDbConfig

    # Build and set SlideSearch config.
    slideSearchConfig = AttrDict()
    slideSearchConfig.BaseUrl = "http://localhost:8000/"
    slideSearchConfig.Username = "test"
    slideSearchConfig.Password = "test"
    slideSearchConfig.isDjangoModel = True
    retval.slideSearch = slideSearchConfig

    # Build and set SlideIndexer config.
    slideIndexerConfig = AttrDict()
    slideIndexerConfig.IterationPeriod = 9000
    retval.slideIndexer = slideIndexerConfig

    # Build and set ZenCentral config.
    zenCentralConfig = AttrDict()
    zenCentralConfig.allowedHosts = ["localhost"]
    retval.zenCentral = zenCentralConfig

    if retval.hostname in ["preze-ntpc", "desktop-fk2ht4j"]:
        retval.word2vecModelPath = "C:/Users/NishantSharma/source/repos/word2vec-slim/GoogleNews-vectors-negative300-SLIM.bin"
        # retval.word2vecModelPath = "C:/Users/NishantSharma/source/repos/word2vec/GoogleNews-vectors-negative300.bin"
        retval.dataFolderPath = "C:/Users/NishantSharma/source/repos/lisa/data/"
        
    elif retval.hostname in ["lisa-dev"]:
        retval.word2vecModelPath = "~/repos/word2vec-slim/GoogleNews-vectors-negative300-SLIM.bin"
        # retval.word2vecModelPath = "~/repos/word2vec/GoogleNews-vectors-negative300.bin"
        retval.dataFolderPath = "~/repos/lisa/data/"
 
        zenCentralConfig["allowedHosts"].append("52.165.226.255")
    return retval

lisaConfig = LisaConfig()
