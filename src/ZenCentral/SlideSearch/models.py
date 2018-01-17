from django.db import models
from django.contrib.auth import get_user_model
from jsonfield import JSONField
from SlideDB.models import Slide

# Create your models here.
class SearchResult(models.Model):
    slide = models.ForeignKey(Slide, on_delete=models.CASCADE)
    rank = models.IntegerField()
    upVoters = models.ManyToManyField(get_user_model())
    downVoters = models.ManyToManyField(get_user_model())

class SearchQuery(models.Model):
    # Session linking.
    session = models.ForeignKey("SearchSession", related_name="queries", on_delete=models.CASCADE)

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
        return super(User, self).save(*args, **kwargs)

class SearchSession(models.Model):
    pass