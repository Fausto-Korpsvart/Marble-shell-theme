from argparse import Namespace
from unittest import TestCase

from scripts.utils.remove_files import selected_color_names

COLOR_KEYS = ["blue", "orange", "green"]


def make_args(**overrides):
    base = dict(blue=False, orange=False, green=False, name=None, hue=None)
    base.update(overrides)
    return Namespace(**base)


class SelectedColorNamesTestCase(TestCase):
    def test_predefined_color_flag(self):
        self.assertEqual(selected_color_names(make_args(blue=True), COLOR_KEYS), ["blue"])

    def test_custom_name(self):  # #61
        self.assertEqual(selected_color_names(make_args(name="mytheme"), COLOR_KEYS), ["mytheme"])

    def test_custom_hue(self):  # #61
        self.assertEqual(selected_color_names(make_args(hue=15), COLOR_KEYS), ["hue15"])

    def test_hue_zero_is_handled(self):  # 0 is falsy but a valid hue
        self.assertEqual(selected_color_names(make_args(hue=0), COLOR_KEYS), ["hue0"])

    def test_name_takes_precedence_over_hue(self):
        self.assertEqual(selected_color_names(make_args(name="cold", hue=200), COLOR_KEYS), ["cold"])

    def test_custom_name_not_duplicated_when_predefined(self):
        self.assertEqual(selected_color_names(make_args(orange=True, name="orange"), COLOR_KEYS), ["orange"])

    def test_no_selection(self):
        self.assertEqual(selected_color_names(make_args(), COLOR_KEYS), [])
