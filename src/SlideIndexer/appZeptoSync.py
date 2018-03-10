"""
Slide Indexer periodically wakes up and downloads latest slide hierarchy from LisaZepto.
All modified slides are then uploaded into ZenCentral SlideDB service.
"""

import threading, time
from LibLisa import lisaConfig

from SlideIndexer.LisaZeptoClient import LisaZeptoClient
from SlideIndexer.SlideDbClient import SlideDbClient

# Instantiate REST clients.
slideDbClient = SlideDbClient()
lisaZeptoClient = LisaZeptoClient()

def syncFromLisaZepto():
    """
    Downloads data from Lisa Zepto.
    Uploads the same into ZenClient SlideDB REST API.
    Removes any entries from ZenClient SlideDB REST API which are not found in downloaded
    Lisa Zepto.
    """
    # Login into REST clients.
    lisaZeptoClient.login()
    slideDbClient.login()

    # Main loop.
    while True:
        # Get all changes made since last update.
        zeptoData = lisaZeptoClient.getLatestData()

        # Repair faulty zepto data.
        zeptoDataRepaired = lisaZeptoClient.repairZeptoData(zeptoData)

        # Prepare zepto data to index.
        zeptoDataTransformed = lisaZeptoClient.transformZeptoData(zeptoDataRepaired)

        # Download att data.
        attoData = slideDbClient.getSlideHierarchy()

        # Apply all changes into Slide Search Engine.
        slideDbClient.syncWithZepto(zeptoDataTransformed, attoData)

        # Sleep for iteration period, before trying again.
        time.sleep(lisaConfig.slideIndexer.IterationPeriod)

syncFromLisaZepto()
