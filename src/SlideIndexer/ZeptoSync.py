"""
Slide Indexer periodically wakes up and downloads latest slide hierarchy from LisaPHP.
All modified slides are then uploaded into ZenCentral SlideDB service.
"""

import threading, time
from LibLisa import lisaConfig, LisaPhpClient, SlideDbClient, SearchClient

# Instantiate REST clients.
slideDbClient = SlideDbClient()
lisaPhpClient = LisaPhpClient()

def syncFromLisaPhp():
    """
    Downloads data from Lisa PHP.
    Uploads the same into ZenClient SlideDB REST API.
    Removes any entries from ZenClient SlideDB REST API which are not found in downloaded
    Lisa PHP.
    """
    # Login into REST clients.
    lisaPhpClient.login()
    slideDbClient.login()

    # Main loop.
    while True:
        # Get all changes made since last update.
        latestData = lisaPhpClient.getLatestData()

        # Repair faulty zepto data.
        latestDataRepaired = lisaPhpClient.repairZeptoData(latestData)

        # Prepare data to index
        latestDataTransformed = lisaPhpClient.transformZeptoData(latestDataRepaired)

        # Apply all changes into Slide Search Engine.
        slideDbClient.syncWithZepto(latestDataTransformed)

        # Sleep for iteration period, before trying again.
        time.sleep(lisaConfig.slideIndexer.IterationPeriod)

syncFromLisaPhp()
