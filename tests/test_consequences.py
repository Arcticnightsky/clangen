import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from scripts.events_module.consequences import (
    can_be_biological_parent,
    gather_cat_objects,
    is_eligible_existing_outsider,
    should_reuse_existing_outsider,
)
from scripts.cat.microservices.conditions import handle_pending_neuter
from scripts.cat.enums import CatGroup, CatStanding


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


class TestExistingOutsiderReuse(unittest.TestCase):
    def test_exists_tag_always_reuses_existing_outsider(self):
        self.assertTrue(should_reuse_existing_outsider(["exists"], False))

    def test_non_patrol_new_cats_do_not_receive_patrol_reuse_roll(self):
        self.assertFalse(should_reuse_existing_outsider(["loner"], False))

    def test_empty_patrol_block_always_creates_new_cat(self):
        self.assertFalse(should_reuse_existing_outsider([], True))

    @patch("scripts.events_module.consequences.randrange", return_value=0)
    def test_patrol_reuses_existing_outsider_one_third_of_the_time(self, _randrange):
        self.assertTrue(should_reuse_existing_outsider(["loner"], True))

    @patch("scripts.events_module.consequences.randrange", return_value=1)
    def test_patrol_creates_new_cat_for_other_two_rolls(self, _randrange):
        self.assertFalse(should_reuse_existing_outsider(["loner"], True))

    def test_exiled_or_driven_away_outsiders_cannot_be_reused(self):
        for standing, near in ((CatStanding.EXILED, True), (CatStanding.KNOWN, False)):
            with self.subTest(standing=standing, near=near):
                status = SimpleNamespace(
                    is_outsider=True,
                    standing_history=[
                        {
                            "group": CatGroup.PLAYER_CLAN_ID,
                            "standing": [standing],
                            "near": near,
                        }
                    ],
                    get_standing_with_group=lambda _group: [standing],
                    is_lost=lambda _group: False,
                )
                cat = SimpleNamespace(status=status, dead=False)

                self.assertFalse(is_eligible_existing_outsider(cat, {}))

    def test_sterilized_outsider_cannot_be_reused_as_biological_parent(self):
        status = SimpleNamespace(
            is_outsider=True,
            standing_history=[
                {
                    "group": CatGroup.PLAYER_CLAN_ID,
                    "standing": [CatStanding.KNOWN],
                    "near": True,
                }
            ],
            get_standing_with_group=lambda _group: [CatStanding.KNOWN],
            is_lost=lambda _group: False,
        )
        cat = SimpleNamespace(
            status=status,
            dead=False,
            no_kits=True,
            permanent_condition={"spayed": {}},
        )

        self.assertTrue(is_eligible_existing_outsider(cat, {}))
        self.assertFalse(
            is_eligible_existing_outsider(cat, {}, requires_biological_parent=True)
        )


class TestPendingNeuter(unittest.TestCase):
    def test_captured_cat_is_sterilized_when_pending_neuter_resolves(self):
        cat = SimpleNamespace(pending_neuter=True)
        cat.apply_sterilization_condition = Mock()

        handle_pending_neuter(cat)

        self.assertFalse(cat.pending_neuter)
        cat.apply_sterilization_condition.assert_called_once_with(
            from_twolegs=True, adjust_personality=True
        )
