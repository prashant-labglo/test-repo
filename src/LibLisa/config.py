"""
File which builds configuration object for all services in the solution.
"""
import os
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
    # Build and set LisaZepto client config.
    lisaZeptoConfig = AttrDict()
    lisaZeptoConfig.BaseUrl = "http://www.prezentium.com/tools/"
    lisaZeptoConfig.Username = "admin"
    lisaZeptoConfig.Password = "$kpres!A@417"
    retval.lisaZepto = lisaZeptoConfig

    # Build and set SlideDbClient config.
    slideDbConfig = AttrDict()
    slideDbConfig.BaseUrl = "http://localhost:8000/"
    slideDbConfig.appName = "slidedb"
    slideDbConfig.Username = "test"
    slideDbConfig.Password = "test"
    retval.slideDb = slideDbConfig

    # Build and set SlideSearch config.
    slideSearchConfig = AttrDict()
    slideSearchConfig.BaseUrl = "http://localhost:8000/"
    slideSearchConfig.appName = "search"
    slideSearchConfig.Username = "test"
    slideSearchConfig.Password = "test"
    slideSearchConfig.isDjangoModel = True
    retval.slideSearch = slideSearchConfig

    # Build and set SlideIndexer config.
    slideIndexerConfig = AttrDict()
    slideIndexerConfig.isDjangoModel = False
    slideIndexerConfig.IterationPeriod = 9000
    retval.slideIndexer = slideIndexerConfig

    # Build and set ZenCentral config.
    zenCentralConfig = AttrDict()
    zenCentralConfig.allowedHosts = ["localhost"]
    retval.zenCentral = zenCentralConfig

    if retval.hostname in ["preze-ntpc", "desktop-fk2ht4j"]:
        if os.name == "nt":
            repoRoot = "C:/Users/NishantSharma/source/repos/"
        elif os.name == "posix":
            repoRoot = "/mnt/c/Users/NishantSharma/source/repos/"
    elif retval.hostname in ["lisa-dev"]:
        repoRoot = "/home/nishant/repos/"

    if os.name == "nt":
        retval.globalApacheModulesRoot = "C:/Apache2/modules/"
    elif os.name == "posix":
        retval.globalApacheModulesRoot = "/usr/lib/apache2/modules/"
        
    retval.appRoot = repoRoot + "lisa/"
    retval.word2vecModelPath = repoRoot + "word2vec-slim/GoogleNews-vectors-negative300-SLIM.bin"
    # retval.word2vecModelPath = repoRoot + "word2vec/GoogleNews-vectors-negative300.bin"
    retval.dataFolderPath = retval.appRoot + "data/"

    if retval.hostname in ["lisa-dev"]:
        zenCentralConfig["allowedHosts"].append("52.165.226.255")

    # Set these file paths to save/cache results.
    retval.slideRatingsDataFilePath = retval.dataFolderPath + "slideRatings.json"
    if retval.hostname in ["lisa-dev"]:
        # Don't cache any results in production.
        retval.simulatedSlideRatingsDataFilePath = None
    else:
        retval.simulatedSlideRatingsDataFilePath = retval.dataFolderPath + "simulatedSlideRatings.json"

    return retval

lisaConfig = LisaConfig()
