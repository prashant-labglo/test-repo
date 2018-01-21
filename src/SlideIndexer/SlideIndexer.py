"""
Slide Indexer periodically wakes up and downloads all fresh or modified slides. All modified slides are then uploaded into ZenCentral service.
"""

from LibLisa import lisaConfig, WorkflowClient, ZenCentralClient

# Instantiate refresh timestamps.
workflowClient = WorkflowClient(lisaConfig.behaviorVersion, lisaConfig.deploymentStage)
zenCentralClient = ZenCentralClient(lisaConfig.behaviorVersion, lisaConfig.deploymentStage)

while True:
    # Read the time stamp of last refresh made.
    lastRefreshTimeStamp = zenCentralClient.LastRefreshTimeStamp()

    # Get all changes made since last update.
    slideTypeChanges = workflowClient.getChanges(lastRefreshTimeStamp)

    # Apply all changes into Slide Search Engine.
    zenCentralClient.updateIndex(slideTypeChanges)

    # Sleep for iteration period, before trying again.
    sleep(lisaConfig.IterationPeriod)