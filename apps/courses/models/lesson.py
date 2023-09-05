# Django Imports
from django.db import models

# HTK Imports
from htk.apps.courses.models.fk_fields import (
    fk_chapter,
    fk_course,
)
from htk.models.classes import HtkBaseModel


DEFAULT_RELATED_NAME = 'lessons'


class Lesson(HtkBaseModel):
    """Lessons are the main component within the Courses app
    that hold the bulk of the content.

    Naturally, a Course is a collection of many Lessons.
    """

    name = models.CharField(max_length=256)
    order = models.PositiveIntegerField(default=0)

    # Relations
    course = fk_course(DEFAULT_RELATED_NAME, required=True)
    chapter = fk_chapter(DEFAULT_RELATED_NAME, required=False)
