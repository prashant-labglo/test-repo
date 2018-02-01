"""
Slide Indexer periodically wakes up and downloads all fresh or modified slides. All modified slides are then uploaded into ZenCentral service.
"""

import threading, time
from LibLisa import lisaConfig, LisaPhpClient, SlideDbClient, SearchClient

# Instantiate refresh timestamps.
lisaPhpClient = LisaPhpClient()
slideDbClient = SlideDbClient()
searchClient = SearchClient()

def syncFromLisaPhp():
    """
    Sync data from Lisa PHP.
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
        time.sleep(lisaConfig.IterationPeriod)

syncFromLisaPhp()