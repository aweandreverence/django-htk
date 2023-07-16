# Django Imports
from django.db import models

# HTK Imports
from htk.models.classes import HtkBaseModel


class Course(HtkBaseModel):
    """Courses are the root object for a course"""

    name = models.CharField(max_length=256)


class CourseModule(HtkBaseModel):
    """CourseModules are an optional grouping for lessons within a course.

    CourseModules are analogous to "Acts" in creative works such as films, plays, and novels.

    Courses that are larger might be organized into separate CourseModules

    Alternate names considered:
    - CourseSection
    """

    name = models.CharField(max_length=256)


class Lesson(HtkBaseModel):
    """Lessons are the main component within the Courses app
    that hold the bulk of the content.

    Naturally, a Course is a collection of many Lessons.
    """

    course = models.ForeignKey(
        Course, default=None, on_delete=models.SET_DEFAULT
    )
    course_module = models.ForeignKey(
        CourseModule, default=None, on_delete=models.SET_DEFAULT
    )
    order = models.PositiveIntegerField(default=0)


class Assessment(HtkBaseModel):
    """Assessments are quizzes, exams, etc"""

    pass
