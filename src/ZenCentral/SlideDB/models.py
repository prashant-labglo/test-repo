from django.db import models
from enumfields import Enum, EnumField
from taggit.managers import TaggableManager

# Create your models here.
class Concept(models.Model):
    name = models.CharField(max_length=64)
    enabled = models.BooleanField()

    # Zepto ID is used to cross reference with corresponding entry in Lisa-Zepto.
    zeptoId = models.IntegerField(unique=True)

class SubConcept(models.Model):
    name = models.CharField(max_length=64)
    parent = models.ForeignKey(Concept, related_name="subConcepts", on_delete=models.CASCADE)
    enabled = models.BooleanField()

    # Zepto ID is used to cross reference with corresponding entry in Lisa-Zepto.
    zeptoId = models.IntegerField(unique=True)

class Construct(models.Model):
    name = models.CharField(max_length=64)
    parent = models.ForeignKey(SubConcept, related_name="constructs", on_delete=models.CASCADE)
    enabled = models.BooleanField()

    # Zepto ID is used to cross reference with corresponding entry in Lisa-Zepto.
    zeptoId = models.IntegerField(unique=True)

class LayoutChoices(Enum):
    Basic = 0
    Enhanced = 1

class StyleChoices(Enum):
    Basic = 0
    Enhanced = 1
    Extensive = 2

class VisualStyleChoices(Enum):
    Basic = 0
    Edgy = 1
    Slick = 2
    Fancy = 3

class SlideContentChoices(Enum):
    Limited = 0
    Medium = 1
    Extensive = 2

class Slide(models.Model):
    parent = models.ForeignKey(Construct, related_name="slides", on_delete=models.CASCADE)
    #pptFile = models.FileField(upload_to='uploads/')
    pptFile = models.URLField()
    tags = TaggableManager()
    enabled = models.BooleanField()

    # Attributes derived from PPT file.
    # thumbnailFile = models.ImageField(upload_to='uploads/')
    thumbnailFile = models.URLField()
    hasIcon = models.BooleanField()
    hasImage = models.BooleanField()
    layout = EnumField(LayoutChoices, default=LayoutChoices.Basic)
    style = EnumField(StyleChoices, default=StyleChoices.Basic)
    visualStyle = EnumField(VisualStyleChoices, default=VisualStyleChoices.Basic)

    # Zepto ID is used to cross reference with corresponding entry in Lisa-Zepto.
    zeptoId = models.IntegerField(unique=True)

    # Number of downloads of this slide made on Zepto site.
    zeptoDownloads = models.IntegerField()
