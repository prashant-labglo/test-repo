from jsonfield import JSONField
from django.utils import timezone
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth import get_user_model
from SlideDB.models import Slide

UserModel = get_user_model()

class SearchResultRating(models.Model):
    rating = models.IntegerField(
        default=0,
        validators=[MaxValueValidator(3), MinValueValidator(-3)]
     )

    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    result = models.ForeignKey("SearchResult", on_delete=models.CASCADE)
    class Meta:
        unique_together = ('user', 'result',)

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
    index = models.ForeignKey("SearchIndex", related_name="queries", on_delete=models.CASCADE)

    # Query definition.
    queryJson = JSONField()

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

class SearchIndex(models.Model):
    created = models.DateTimeField(editable=False)

    searchAlgo = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        """
        On save, we may update timestamps.
        """
        if not self.id:
            self.created = timezone.now()
        return super().save(*args, **kwargs)
