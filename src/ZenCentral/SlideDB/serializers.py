from rest_framework import serializers
from SlideDB.models import Concept, SubConcept, Construct, Slide, LayoutChoices, StyleChoices, VisualStyleChoices
from taggit_serializer.serializers import TagListSerializerField, TaggitSerializer
from ZenCentral import fields

class ConceptSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    constructs = serializers.ReadOnlyField(source='grand_children')

    class Meta:
        model = Concept
        fields = ('id', 'name', 'enabled', 'zeptoId', 'constructs')

class SubConceptSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    class Meta:
        model = SubConcept
        fields = ('id', 'name', 'parent', 'enabled', 'zeptoId')

class ConstructSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    class Meta:
        model = Construct
        fields = ('id', 'name', 'parent', 'enabled', 'zeptoId')

class SlideSerializer(TaggitSerializer, serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    tags = TagListSerializerField()
    layout = fields.EnumSerializerField(LayoutChoices)
    style = fields.EnumSerializerField(StyleChoices)
    visualStyle = fields.EnumSerializerField(VisualStyleChoices, read_only=True)

    class Meta:
        model = Slide
        fields = (
            'id', 'parent', 'pptxFile', 'pptFile', 'tags', 'enabled', 'imageFile', 'thumbnailFile', 'hasIcon',
            'hasImage', 'layout', 'style', 'visualStyle', 'zeptoId', 'zeptoDownloads'
        )
