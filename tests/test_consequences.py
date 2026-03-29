import unittest
from types import SimpleNamespace
from unittest.mock import patch

from scripts.events_module.consequences import (
    gather_cat_objects,
    ensure_parent_is_not_sterilized,
)


class TestGatherCatObjects(unittest.TestCase):
    def setUp(self):
        self.low_lawful_cat = SimpleNamespace(
            status=SimpleNamespace(alive_in_player_clan=True),
            personality=SimpleNamespace(
                lawfulness=3, sociability=3, stability=3, aggression=3
            ),
        )
        self.cat_class = SimpleNamespace(all_cats_list=[self.low_lawful_cat])
        self.event = SimpleNamespace(
            main_cat=None,
            random_cat=None,
            patrol_leader=None,
            patrol_apprentices=[],
            patrol_cats=[],
            new_cats=[],
        )

    def test_supported_facet_abbreviation_with_no_matches_does_not_warn(self):
        with patch("builtins.print") as mock_print:
            gathered = gather_cat_objects(
                self.cat_class, ["clan", "high_lawful"], self.event
            )

        self.assertEqual(gathered, [])
        mock_print.assert_not_called()

    def test_unknown_abbreviation_still_warns(self):
        with patch("builtins.print") as mock_print:
            gather_cat_objects(self.cat_class, ["clan", "unknown"], self.event)

        mock_print.assert_called_once_with("WARNING: Unsupported abbreviation unknown")


class TestEnsureParentIsNotSterilized(unittest.TestCase):
    def test_removes_sterilization_flags_from_parent(self):
        parent = SimpleNamespace(
            permanent_condition={"spayed": {"severity": "minor"}, "blind": {}},
            no_kits=True,
        )

        ensure_parent_is_not_sterilized(parent)

        self.assertNotIn("spayed", parent.permanent_condition)
        self.assertIn("blind", parent.permanent_condition)
        self.assertFalse(parent.no_kits)

    def test_no_changes_when_parent_not_sterilized(self):
        parent = SimpleNamespace(permanent_condition={"blind": {}}, no_kits=True)

        ensure_parent_is_not_sterilized(parent)

        self.assertEqual({"blind": {}}, parent.permanent_condition)
        self.assertTrue(parent.no_kits)
