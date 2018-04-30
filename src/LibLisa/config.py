"""
File which builds configuration object for all services in the solution.
"""
import os, ssl, getpass
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
            "behaviorVersion": Behavior(0),
            "IterationPeriod": 60,
        })

    retval.hostname = gethostname().lower()

    # Build config useful in generating Apache configuration.
    apacheConfig = AttrDict()
    apacheConfig.enableSSL = True
    if retval.hostname in ["lisa-dev", "lisa-ppe", "lisa-prod"]:
        apacheConfig.http_host = retval.hostname + ".prezentium.com"
        if getpass.getuser() == "nishant":
            apacheConfig.http_port = 8080
        else:
            apacheConfig.http_port = 443
    else:
        apacheConfig.http_host = "localhost"
        apacheConfig.http_port = 8000

    retval.apacheConfig = apacheConfig

    apacheConfig.service_url = (
                 "http" + ("s" if apacheConfig.enableSSL else "") 
                 + "://" + apacheConfig.http_host
                 + ":" + str(apacheConfig.http_port) + "/")

    retval.deploymentStage = DeploymentStage.Dev
    # Build and set LisaZepto client config.
    lisaZeptoConfig = AttrDict()
    lisaZeptoConfig.BaseUrl = "http://www.prezentium.com/tools/"
    lisaZeptoConfig.Username = "admin"
    lisaZeptoConfig.Password = "$kpres!A@417"
    retval.lisaZepto = lisaZeptoConfig

    # Build and set SlideDbClient config.
    slideDbConfig = AttrDict()
    slideDbConfig.BaseUrl = apacheConfig.service_url
    slideDbConfig.appName = "slidedb"
    slideDbConfig.Username = "test"
    slideDbConfig.Password = "test"
    retval.slideDb = slideDbConfig

    # Build and set SlideSearch config.
    slideSearchConfig = AttrDict()
    slideSearchConfig.BaseUrl = apacheConfig.service_url
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
    zenCentralConfig.allowedHosts = ["localhost", "lisa-dev.prezentium.com", "lisa-prod.prezentium.com"]
    retval.zenCentral = zenCentralConfig

    if retval.hostname in ["preze-ntpc", "desktop-fk2ht4j"]:
        if os.name == "nt":
            repoRoot = "C:/Users/NishantSharma/source/repos/"
        elif os.name == "posix":
            repoRoot = "/mnt/c/Users/NishantSharma/source/repos/"
    elif retval.hostname in ["lisa-dev", "lisa-prod"]:
        if getpass.getuser() == "nishant":
            repoRoot = "/home/nishant/repos/"
        else:
            repoRoot = "/srv/"
    elif retval.hostname in ["labglo-pc"]:
        repoRoot = "/projects/sources/"

    retval.angularAppRootFolder = repoRoot + "lisa-ng/src/LisaTools/containers/"

    if os.name == "nt":
        retval.globalApacheModulesRoot = "C:/Apache2/modules/"
    elif os.name == "posix":
        retval.globalApacheModulesRoot = "/usr/lib/apache2/modules/"

    retval.ssl_verify = retval.hostname in ["lisa-dev", "lisa-ppe", "lisa-prod"]

    retval.appRoot = repoRoot + "lisa-api/"
    retval.uploadsFolder = retval.appRoot + "src/ZenCentral/uploads/"

    retval.word2vecModelPath = repoRoot + "word2vec-slim/GoogleNews-vectors-negative300-SLIM.bin"
    # retval.word2vecModelPath = repoRoot + "word2vec/GoogleNews-vectors-negative300.bin"
    retval.dataFolderPath = retval.appRoot + "data/"
    if not os.path.exists(retval.dataFolderPath):
        os.makedirs(retval.dataFolderPath)

    # Set these file paths to save/cache results.
    retval.slideRatingsDataFilePath = retval.dataFolderPath + "slideRatings.json"
    if retval.hostname in ["lisa-dev"]:
        # Don't cache any results in production.
        retval.simulatedSlideRatingsDataFilePath = None
    else:
        retval.simulatedSlideRatingsDataFilePath = retval.dataFolderPath + "simulatedSlideRatings.json"

    # Database configurations
    if retval.hostname in ["labglo-pc"]:
        dbconf = AttrDict()
        dbconf.ENGINE = "django.db.backends.postgresql_psycopg2"
        dbconf.NAME = "lisadevdb"
        dbconf.USER = "postgres"
        dbconf.PASSWORD = "password"
        dbconf.HOST = "localhost"
        dbconf.PORT = ""
    elif retval.hostname in ["lisa-dev", "lisa-prod"]:
        dbconf = AttrDict()
        dbconf.ENGINE = "django.db.backends.postgresql_psycopg2"
        dbconf.NAME = "lisadb"
        dbconf.USER = "postgres"
        dbconf.PASSWORD = "Pass@lisa2018"
        dbconf.HOST = "localhost"
        dbconf.PORT = ""
    else:
        dbconf = AttrDict()
        dbconf.ENGINE = 'django.db.backends.sqlite3'
        dbconf.NAME = retval.appRoot + "src/ZenCentral/db.sqlite3"
    retval.zenDbConf = dbconf

    if apacheConfig.http_port == 443 and retval.hostname in ["lisa-dev"]:
        apacheConfig.ssl_crt = '/srv/ssl-docs/lisa-dev_220ff5a21b448215.crt'
        apacheConfig.ssl_key = '/srv/ssl-docs/lisa-dev_220ff5a21b448215.key'
    elif apacheConfig.http_port == 443 and retval.hostname in ["lisa-prod"]:
        apacheConfig.ssl_crt = '/srv/ssl-docs/lisa-prod_1bcc62fad2ba9bec.crt'
        apacheConfig.ssl_key = '/srv/ssl-docs/lisa-prod_1bcc62fad2ba9bec.key'
    else:
        apacheConfig.ssl_crt = retval.appRoot + 'src/ZenCentral/apache/zenCentral.crt'
        apacheConfig.ssl_key = retval.appRoot + 'src/ZenCentral/apache/zenCentral.key'

    return retval

lisaConfig = LisaConfig()
