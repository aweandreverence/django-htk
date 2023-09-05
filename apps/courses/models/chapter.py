# Django Imports
from django.db import models

# HTK Imports
from htk.apps.courses.models.fk_fields import fk_course
from htk.models.classes import HtkBaseModel


DEFAULT_RELATED_NAME = 'chapters'


class Chapter(HtkBaseModel):
    """Chapters are an optional grouping for lessons within a course.

    Chapters are analogous to "Acts" in creative works such as films, plays, and novels.

    Courses that are larger might be organized into separate Chapters

    Alternate names considered:
    - CourseModule
    - CourseSection
    """

    name = models.CharField(max_length=256)
    order = models.PositiveIntegerField(default=0)

    # Relations
    course = fk_course(DEFAULT_RELATED_NAME, required=True)
