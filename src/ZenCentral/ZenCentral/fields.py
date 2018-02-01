from django import forms
from rest_framework import serializers

class IntegerListField(forms.CharField):
    def prepare_value(self, value):
        return ','.join(value)

    def to_python(self, value):
        if not value:
            return []
        return [item.strip() for item in value.split(',')]

class EnumSerializerField(serializers.ChoiceField):
    def __init__(self, enum, **kwargs):
        self.enum = enum
        kwargs['choices'] = [(e.name, e.name) for e in enum]
        super().__init__(**kwargs)

    def to_representation(self, obj):
        return obj.name

    def to_internal_value(self, data):
        try:
            return self.enum[data]
        except KeyError:
            self.fail('invalid_choice', input=data)