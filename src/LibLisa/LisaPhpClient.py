"""
This is a REST API client which talks with the Lisa-PHP web-service.
"""
import requests, json
from lxml import html
from functools import reduce
import urllib.parse
from LibLisa.behaviors import Behavior
from LibLisa.RestClient import RestClient
from LibLisa.config import lisaConfig

class LisaPhpClient(RestClient):
    """
    Lisa-PHP is the legacy Lisa service. This client connects with Lisa-PHP and can download
    all its data.
    """
    def __init__(self):
        """
        Constructor
        """
        self.config = lisaConfig.lisaPhp
        self.baseURL = self.config.BaseUrl
        self.loginURL = self.baseURL + "prezentiumadmin/"
        self.jsonURL = self.baseURL + "prezentiumadmin/prezentiumslide/slidelist_json"
        super().__init__(self.baseURL)

    def login(self):
        """
        Logs into Lisa-PHP. Required, before we download any data.
        """
        self.session = requests.session()

        # Lie about the user agent because Lisa PHP doesn't work without it.
        self.session.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0"

        loginPayload = {"admin_user" : self.config.Username, "admin_password" : self.config.Password}
        loginResult = self.session.post(self.loginURL, data=loginPayload)

        if loginResult.status_code != 200:
            raise ConnectionError("Unable to login.")

    def getLatestData(self):
        """
        Call this to get the latest data on Lisa-PHP.
        Returns a single JSON.
        """
        jsonText = self.session.get(self.jsonURL).text

        # Somehow, the output I am getting has some garbage at the beginning.
        # So, skipping all text before first instance of "{".
        jsonText = jsonText[jsonText.find("{"):]
        latestData = json.loads(jsonText)
        return latestData

    def repairZeptoData(self, zeptoData):
        """
        There are lots of inconsistencies in the Zepto data. This function call
        finds and logs these inconsistencies. It also repairs some of the issues.
        """
        # Check for duplicate slide records, for the same slide file.
        slidePaths = set([slide["Slide"] for slide in zeptoData["Slides"]])
        pathToSlideIds = {slidePath:[] for slidePath in slidePaths}
        for slide in zeptoData["Slides"]:
            pathToSlideIds[slide["Slide"]].append(slide["NumId"])

        duplicateSlideIds = [(k, v) for (k, v) in pathToSlideIds.items() if len(v) != 1]
        json.dump(duplicateSlideIds, open(lisaConfig.dataFolderPath + "debugDuplicateSlideIDs.json", "w"), indent=2)

        # Slides with "enhaced" style.
        slidesWithEnhaced = [slide["NumId"] for slide in zeptoData["Slides"] if slide["Style"] == "Enhaced"]
        json.dump(slidesWithEnhaced, open(lisaConfig.dataFolderPath + "slidesWithEnhacedStyle.json", "w"), indent=2)

        for slide in zeptoData["Slides"]:
            # Style has Enhanced mis-spelled as Enhaced for some slides.
            if slide["Style"] == "Enhaced":
                slide["Style"] = "Enhanced"

            # Parts of tag data are corrupted. Fixing.
            slideTagLists = []
            for tag in slide["Tags"]:
                tag = tag.strip().lower()
                if tag.count(",") >= 3:
                    slideTagLists.append(tag.split(","))
                elif tag.count(" ") >= 3:
                    slideTagLists.append(tag.split(" "))
                else:
                    slideTagLists.append([tag])

            # Force unqiueness.
            slideTagsSet = set()
            for tagList in slideTagLists:
                for tag in tagList:
                    if tag:
                        slideTagsSet.add(tag)

            # Keep the list in canonical form.
            slide["Tags"] = sorted([tag.strip() for tag in slideTagsSet])
        return zeptoData

    def transformZeptoData(self, zeptoData):
        """
        The data from Lisa PHP is not directly compatible with new Django based ZenCentral
        slidedb backend.

        This function transforms the LisaPHP data to make it compatible.
        """
        retval = {}
        # Make all the latest concepts compatible with SlideDB system.
        transformedConcepts = []
        conceptsDict = {}
        for latestConcept in zeptoData["Concepts"]:
            transformedConcept = {}

            # ID at the server can be obtained from zeptoId attribute.
            # transformedSlide["parent"] = self.baseURL + "slidedb/constructs/" + str(latestSlide["ConstructId"]) + "/"
            # zeptoSlideForAtto["enabled"] = slide["Enabled"]
            transformedConcept["enabled"] = True if latestConcept["Enabled"] == "Y" else False
            transformedConcept["name"] = latestConcept["Name"].strip()
            transformedConcept["zeptoId"] = latestConcept["NumId"]

            conceptsDict[transformedConcept["zeptoId"]] = transformedConcept
            transformedConcepts.append(transformedConcept)
        retval["Concepts"] = transformedConcepts

        # Make all the latest subConcepts compatible with SlideDB system.
        transformedSubConcepts = []
        subConceptsDict = {}
        for latestSubConcept in zeptoData["SubConcepts"]:
            transformedSubConcept = {}
            # ID at the server can be obtained from zeptoId attribute.
            transformedSubConcept["parent"] = conceptsDict[int(latestSubConcept["Parent"])]
            transformedSubConcept["enabled"] = True if latestSubConcept["Enabled"] == "Y" else False
            transformedSubConcept["name"] = latestSubConcept["Name"].strip()
            transformedSubConcept["zeptoId"] = latestSubConcept["NumId"]

            subConceptsDict[transformedSubConcept["zeptoId"]] = transformedSubConcept
            transformedSubConcepts.append(transformedSubConcept)

        retval["SubConcepts"] = transformedSubConcepts

        # Make all the latest subConcepts compatible with SlideDB system.
        transformedConstructs = []
        constructsDict = {}
        for latestConstruct in zeptoData["Constructs"]:
            transformedConstruct = {}

            # ID at the server can be obtained from zeptoId attribute.
            transformedConstruct["parent"] = subConceptsDict[int(latestConstruct["Parent"])]
            transformedConstruct["enabled"] = True if latestConstruct["Enabled"] == "Y" else False
            transformedConstruct["name"] = latestConstruct["Name"].strip()
            transformedConstruct["zeptoId"] = latestConstruct["NumId"]

            constructsDict[transformedConstruct["zeptoId"]] = transformedConstruct
            transformedConstructs.append(transformedConstruct)
        retval["Constructs"] = transformedConstructs

        # Make all the latest slides compatible with SlideDB system.
        transformedSlides = []
        for latestSlide in zeptoData["Slides"]:
            transformedSlide = {}

            # ID at the server can be obtained from zeptoId attribute.
            transformedSlide["parent"] = constructsDict[int(latestSlide["Parent"])]
            transformedSlide["tags"] = latestSlide["Tags"]

            # zeptoSlideForAtto["enabled"] = slide["Enabled"]
            transformedSlide["enabled"] = True
            transformedSlide["pptFile"] = urllib.parse.quote(latestSlide["Slide"], "/:")
            transformedSlide["thumbnailFile"] = urllib.parse.quote(latestSlide["Thumbnail"], "/:")
            transformedSlide["hasIcon"] = True if latestSlide["Icon"].lower() == "yes" else False
            transformedSlide["hasImage"] = True if latestSlide["Image"].lower() == "yes" else False
            transformedSlide["layout"] = latestSlide["Layout"]
            transformedSlide["style"] = latestSlide["Style"]
            transformedSlide["visualStyle"] = latestSlide["VisualStyle"]
            transformedSlide["zeptoId"] = latestSlide["NumId"]
            transformedSlides.append(transformedSlide)
        retval["Slides"] = transformedSlides

        return retval

def textCleanUp(jsonObject, badStrings=None, allStrings=None):
    """
    Removes unnecessary whitespace and makes everything lowercase for an arbitrary JSON.
    """
    if (isinstance(jsonObject, str)):
        if badStrings is not None and (" " in jsonObject or "," in jsonObject):
            badStrings.add(jsonObject)
        retval = jsonObject.lower().strip().replace(" ", "_")
        if allStrings is not None:
            allStrings.add(retval)
    elif (isinstance(jsonObject, list)):
        # Some of the strings are of kind "a, b". They should be flattened into list.
        if any([isinstance(item, str) and "," in item for item in jsonObject]):
            for item in jsonObject:
                if "," in item:
                    badStrings.add(item)
            jsonObject = ",".join(jsonObject).split(",")
        else:
            # If we are not dealing with list of strings, then we need to clean them up, recursively.
            jsonObject = [textCleanUp(item, badStrings) for item in jsonObject]

        # Remove empty string
        jsonObject = [item for item in jsonObject if item]

        # Remove duplicates if we are dealing with list of strings.
        if all([isinstance(item, str) for item in jsonObject]):
            jsonObject = set(jsonObject)
            if allStrings is not None:
                allStrings = allStrings.update(jsonObject)
            jsonObject = list(jsonObject)
        retval = jsonObject
    elif (isinstance(jsonObject, dict)):
        retval = {key:textCleanUp(value, badStrings) for (key, value) in jsonObject.items()}
    else:
        retval = jsonObject
        
    return retval