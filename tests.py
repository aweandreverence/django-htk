# Django Imports
from django.db import models
from django.test import TestCase

# HTK Imports
from htk.constants import *
from htk.lib.tests import *
from htk.models.classes import HtkBaseModel
from htk.scripts.tests import *
from htk.test_scaffold.models import TestScaffold
from htk.test_scaffold.tests import (
    BaseTestCase,
    BaseWebTestCase,
)
from htk.utils.tests import *


class HtkUrlModel(HtkBaseModel):
    name = models.CharField(max_length=32, blank=True)

    class Meta:
        app_label = 'test_scaffold'

    def get_absolute_url(self):
        return '/test-model/%s/' % self.id


class HtkBaseModelTestCase(TestCase):
    def test_get_full_url_builds_absolute_url_from_absolute_path(self):
        obj = HtkUrlModel(id=42)

        self.assertEqual(
            'https://hacktoolkit.com/test-model/42/',
            obj.get_full_url(),
        )


class HtkWebViewsTestCase(BaseWebTestCase):
    def test_error_pages(self):
        view_names = (
            'error_403',
            'error_404',
            'error_500',
        )
        for view_name in view_names:
            self._check_view_is_okay(view_name)
