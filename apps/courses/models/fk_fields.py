# Django Imports
from django.db import models

# HTK Imports
from htk.models.fk_fields import build_kwargs
from htk.utils import htk_setting


def fk_course(related_name: str, required: bool = False) -> models.ForeignKey:
    field = models.ForeignKey(
        htk_setting('HTK_APPS_COURSES_MODELS_COURSE'),
        related_name=related_name,
        **build_kwargs(required=required),
    )
    return field


def fk_chapter(related_name: str, required: bool = False) -> models.ForeignKey:
    field = models.ForeignKey(
        htk_setting('HTK_APPS_COURSES_MODELS_CHAPTER'),
        related_name=related_name,
        **build_kwargs(required=required),
    )
    return field
