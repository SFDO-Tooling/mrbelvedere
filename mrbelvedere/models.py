from django.db import models

class Repository(models.Model):
    name = models.SlugField()
    url = models.URLField()
    active = models.BooleanField(default=True)
