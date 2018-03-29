from django.db import models
from enumfields import Enum, EnumField
from taggit.managers import TaggableManager

# Create your models here.
class Concept(models.Model):
    name = models.CharField(max_length=64)
    enabled = models.BooleanField()

    # Zepto ID is used to cross reference with corresponding entry in Lisa-Zepto.
    zeptoId = models.IntegerField(unique=True)

    def grand_children(self):
        """ Method to get all constructs related to concept. """

        queryset = Construct.objects.filter(parent__parent=self.id).values('id', 'name')
        result = [item for item in queryset]
        return result

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
    @property
    def visualStyle(self):
        """
        Visual style is a derived attribute of a slide.
        Defined as a property, so that it is availble to serializers.
        """
        if   self.style == StyleChoices.Basic and self.layout == LayoutChoices.Basic:
            return VisualStyleChoices.Basic
        elif self.style == StyleChoices.Basic and self.layout == LayoutChoices.Enhanced:
            return VisualStyleChoices.Edgy
        elif self.style == StyleChoices.Enhanced and self.layout == LayoutChoices.Basic:
            return VisualStyleChoices.Slick
        elif self.style == StyleChoices.Enhanced and self.layout == LayoutChoices.Enhanced:
            return VisualStyleChoices.Fancy

    # Zepto ID is used to cross reference with corresponding entry in Lisa-Zepto.
    zeptoId = models.IntegerField(unique=True)

    # Number of downloads of this slide made on Zepto site.
    zeptoDownloads = models.IntegerField()
