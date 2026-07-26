from unittest import TestCase
from unittest.mock import patch

from scripts import config
from scripts.utils.gnome import gnome_version


class GnomeVersionTestCase(TestCase):
    def setUp(self):
        self._saved_override = config.gnome_version_override
        config.gnome_version_override = None

    def tearDown(self):
        config.gnome_version_override = self._saved_override

    def test_override_takes_precedence_over_detection(self):
        config.gnome_version_override = "49"
        with patch("scripts.utils.gnome.subprocess.check_output") as check_output:
            self.assertEqual(gnome_version(), "49")
            check_output.assert_not_called()  # never shells out when overridden

    def test_falls_back_to_detection_when_no_override(self):
        with patch("scripts.utils.gnome.subprocess.check_output",
                   return_value="GNOME Shell 47.2\n") as check_output:
            self.assertEqual(gnome_version(), "47.2")
            check_output.assert_called_once()

    def test_returns_none_when_no_override_and_no_gnome_shell(self):
        with patch("scripts.utils.gnome.subprocess.check_output", side_effect=FileNotFoundError):
            self.assertIsNone(gnome_version())
