import shutil
import tempfile

from django.test import override_settings


class TempMediaMixin:
    @classmethod
    def setUpClass(cls):
        cls._media_dir = tempfile.mkdtemp()
        cls._media_override = override_settings(MEDIA_ROOT=cls._media_dir)
        cls._media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._media_override.disable()
        shutil.rmtree(cls._media_dir, ignore_errors=True)
