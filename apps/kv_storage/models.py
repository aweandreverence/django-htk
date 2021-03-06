# Third Party (PyPI) Imports
import jsonfield

# Django Imports
from django.db import models


class AbstractKVStorage(models.Model):
    """AbstractKVStorage is a simple key-value storage on top of your Django app's default data storage (i.e. most likely MySQL)

    It is not meant to be performant or high-volume; just convenient and accurate.
    """
    key = models.CharField(max_length=255, unique=True)
    value = jsonfield.JSONField()
    created_on = models.DateTimeField(auto_now_add=True)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        verbose_name = 'KV Storage'
