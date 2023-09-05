# Django Imports
from django.db import models

# HTK Imports
from htk.models.classes import HtkBaseModel


class Course(HtkBaseModel):
    """Courses are the root object for a course"""

    name = models.CharField(max_length=256)
