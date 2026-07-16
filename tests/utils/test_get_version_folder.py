import os
import shutil
import tempfile
from unittest import TestCase

from scripts.utils.get_version_folder import get_version_folders, _folder_bounds


class FolderBoundsTestCase(TestCase):
    def test_open_upper_bound(self):
        self.assertEqual(_folder_bounds("47.."), (47, float("inf")))

    def test_open_lower_bound(self):
        self.assertEqual(_folder_bounds("..46"), (float("-inf"), 46))

    def test_closed_range(self):
        self.assertEqual(_folder_bounds("47..48"), (47, 48))

    def test_exact_version(self):
        self.assertEqual(_folder_bounds("49"), (49, 49))

    def test_non_version_folder_is_ignored(self):
        self.assertIsNone(_folder_bounds(".DS_Store"))
        self.assertIsNone(_folder_bounds("readme"))

    def test_malformed_range_is_ignored(self):
        self.assertIsNone(_folder_bounds("a..b"))


class GetVersionFoldersTestCase(TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp()
        for name in ["..46", "..47", "47..", "48..", "49", "not-a-version"]:
            os.makedirs(os.path.join(self.base, name), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def test_missing_base_path_returns_empty(self):
        self.assertEqual(get_version_folders("48", "/nonexistent/path"), [])

    def test_matches_and_orders_ascending_by_lower_bound(self):
        # GNOME 49 matches 47.., 48.. and exact 49 — higher bounds come last so
        # their styles override lower ones in the combined stylesheet.
        self.assertEqual(get_version_folders("49", self.base), ["47..", "48..", "49"])

    def test_uses_major_version_only(self):
        self.assertEqual(get_version_folders("49.2", self.base), ["47..", "48..", "49"])

    def test_lower_version_matches_open_lower_bounds(self):
        # GNOME 46 matches only the "up to" folders, ordered by upper bound.
        self.assertEqual(get_version_folders("46", self.base), ["..46", "..47"])

    def test_ignores_non_version_folders(self):
        self.assertNotIn("not-a-version", get_version_folders("49", self.base))
