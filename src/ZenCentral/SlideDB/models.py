from django.db import models
from enumfields import Enum, EnumField
from taggit.managers import TaggableManager

# Create your models here.
class Concept(models.Model):
    name = models.CharField(max_length=64)
    enabled = models.BooleanField()

class SubConcept(models.Model):
    name = models.CharField(max_length=64)
    parent = models.ForeignKey(Concept, related_name="subConcepts", on_delete=models.CASCADE)
    enabled = models.BooleanField()

class Construct(models.Model):
    name = models.CharField(max_length=64)
    parent = models.ForeignKey(SubConcept, related_name="constructs", on_delete=models.CASCADE)
    enabled = models.BooleanField()

class LayoutChoices(Enum):
    Basic = 0
    Enhanced = 1

class StyleChoices(Enum):
    Basic = 0
    Enhanced = 1

class VisualStyleChoices(Enum):
    Basic = 0
    Enhanced = 1

class Slide(models.Model):
    parent = models.ForeignKey(Construct, related_name="slides", on_delete=models.CASCADE)
    pptFile = models.FileField(upload_to='uploads/')
    tags = TaggableManager()

    # Derived attributes.
    thumbnailFile = models.ImageField(upload_to='uploads/')
    hasIcon = models.BooleanField()
    hasImage = models.BooleanField()
    layout = EnumField(LayoutChoices, default=LayoutChoices.Basic)
    style = EnumField(StyleChoices, default=StyleChoices.Basic)
    visualStyle = EnumField(VisualStyleChoices, default=VisualStyleChoices.Basic)
