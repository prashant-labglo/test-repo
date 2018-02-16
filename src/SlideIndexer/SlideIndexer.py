"""
Slide Indexer periodically wakes up and downloads latest slide hierarchy from LisaPHP.
All modified slides are then uploaded into ZenCentral SlideDB service.
"""

import threading, time
from LibLisa import lisaConfig, LisaPhpClient, SlideDbClient, SearchClient

# Instantiate REST clients.
slideDbClient = SlideDbClient()
searchClient = SearchClient()

def searchIndexCreatorThreadFunc():
    """
    Downloads data from Lisa PHP.
    Uploads the same into ZenClient SlideDB REST API.
    Removes any entries from ZenClient SlideDB REST API which are not found in downloaded
    Lisa PHP.
    """
    # Login into REST clients.
    slideDbClient.login()
    searchClient.login()

    # Main loop.
    while True:
        # Get all changes made since last update.
        slideHierarchy = slideDbClient.getLatestData()

        # Repair faulty zepto data.
        trainingData = slideDbClient.getTrainingData()

        # Prepare data to index
        latestDataTransformed = lisaPhpClient.transformZeptoData(latestDataRepaired)

        # Apply all changes into Slide Search Engine.
        slideDbClient.syncWithZepto(latestDataTransformed)

        # Sleep for iteration period, before trying again.
        time.sleep(lisaConfig.slideIndexer.IterationPeriod)

searchIndexCreatorThreadFunc()