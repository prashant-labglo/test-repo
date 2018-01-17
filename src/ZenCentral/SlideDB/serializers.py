from rest_framework import serializers
from SlideDB.models import Concept, SubConcept, Construct, Slide
from taggit_serializer.serializers import TagListSerializerField, TaggitSerializer

class ConceptSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Concept
        fields = ('name', 'enabled')

class SubConceptSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SubConcept
        fields = ('name', 'parent', 'enabled')

class ConstructSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Construct
        fields = ('name', 'parent', 'enabled')

class SlideSerializer(TaggitSerializer, serializers.HyperlinkedModelSerializer):
    tags = TagListSerializerField()
    class Meta:
        model = Slide
        fields = ('parent', 'pptFile', 'thumbnailFile', 'tags', 'hasIcon', 'hasImage', 'layout', 'style', 'visualStyle')
