from django.utils import timezone
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from jsonfield import JSONField
from SlideDB.models import Slide

# Create your models here.
class SearchResult(models.Model):
    slide = models.ForeignKey(Slide, on_delete=models.CASCADE)
    rank = models.IntegerField()

    # Add rating.
    rating = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)])

class SearchQuery(models.Model):
    # Session linking.
    session = models.ForeignKey("SearchSession", related_name="queries", on_delete=models.CASCADE)

    # Query definition.
    queryJson = JSONField()

    searchAlgo = models.TextField()

    # TimeStamps
    created = models.DateTimeField(editable=False)
    results = models.ManyToManyField(SearchResult)

    def save(self, *args, **kwargs):
        """
        On save, we may update timestamps.
        """
        if not self.id:
            self.created = timezone.now()
        return super().save(*args, **kwargs)

class SearchSession(models.Model):
    created = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        """
        On save, we may update timestamps.
        """
        if not self.id:
            self.created = timezone.now()
        return super().save(*args, **kwargs)

class SearchIndex(models.Model):
    created = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        """
        On save, we may update timestamps.
        """
        if not self.id:
            self.created = timezone.now()
        return super().save(*args, **kwargs)
