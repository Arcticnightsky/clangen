import os
import unittest
from unittest.mock import patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from scripts.cat.cats import Cat, Relationship
from scripts.events_module.relationship.relation_events import Relation_Events
from scripts.events_module.relationship.romantic_events import RomanticEvents


class RelationshipConditions(unittest.TestCase):
    def test_main_cat_status_one(self):
        # given
        cat1 = Cat(disable_random=True)
        cat2 = Cat(disable_random=True)

        condition = {
            "romance": 0,
            "like": 0,
            "respect": 0,
            "comfort": 15,
            "trust": 20,
        }

        # when
        rel_fulfill = Relationship(cat1, cat2)
        rel_fulfill.romance = 50
        rel_fulfill.like = 50
        rel_fulfill.comfort = 50
        rel_fulfill.respect = 50
        rel_fulfill.trust = 50

        # then
        self.assertTrue(
            RomanticEvents.relationship_fulfill_condition(rel_fulfill, condition)
        )


class RomanticEventSelection(unittest.TestCase):
    @patch("scripts.events_module.relationship.relation_events.RomanticEvents.handle_mating_and_breakup")
    @patch("scripts.events_module.relationship.relation_events.Relation_Events.romantic_events")
    @patch("scripts.events_module.relationship.relation_events.Relation_Events.same_age_events")
    @patch("scripts.events_module.relationship.relation_events.Relation_Events.group_events")
    @patch("scripts.events_module.relationship.relation_events.random_module.random")
    @patch("scripts.events_module.relationship.relation_events.random.getrandbits")
    def test_high_romance_boosts_monthly_interaction_chance(
        self,
        mock_getrandbits,
        mock_random,
        mock_group_events,
        mock_same_age_events,
        mock_romantic_events,
        mock_handle_mating,
    ):
        cat_1 = Cat(gender="female", moons=30, disable_random=True)
        cat_2 = Cat(gender="male", moons=30, disable_random=True)
        relationship = Relationship(cat_1, cat_2)
        relationship.romance = 30
        cat_1.relationships[cat_2.ID] = relationship

        mock_getrandbits.return_value = 1
        mock_random.return_value = 0.1

        Relation_Events.handle_relationships(cat_1)

        mock_romantic_events.assert_called_once_with(cat_1)

    @patch("scripts.events_module.relationship.relation_events.Relation_Events.can_trigger_events", return_value=True)
    @patch("scripts.events_module.relationship.relation_events.RomanticEvents.start_interaction", return_value=False)
    @patch("scripts.events_module.relationship.relation_events.get_possible_mates")
    @patch("scripts.events_module.relationship.relation_events.random_module.randint", return_value=2)
    def test_same_sex_balance_falls_back_to_opposite_gender_candidate(
        self,
        mock_randint,
        mock_get_possible_mates,
        mock_start_interaction,
        mock_can_trigger,
    ):
        cat = Cat(gender="female", moons=30, disable_random=True)
        same_sex_cat = Cat(gender="female", moons=30, disable_random=True)
        opposite_sex_cat = Cat(gender="male", moons=30, disable_random=True)

        cat.relationships[same_sex_cat.ID] = Relationship(cat, same_sex_cat)
        same_sex_cat.relationships[cat.ID] = Relationship(same_sex_cat, cat)
        cat.relationships[opposite_sex_cat.ID] = Relationship(cat, opposite_sex_cat)
        opposite_sex_cat.relationships[cat.ID] = Relationship(opposite_sex_cat, cat)

        cat.relationships[same_sex_cat.ID].like = 50
        cat.relationships[same_sex_cat.ID].comfort = 50
        same_sex_cat.relationships[cat.ID].like = 50
        same_sex_cat.relationships[cat.ID].comfort = 50

        cat.relationships[opposite_sex_cat.ID].like = 50
        cat.relationships[opposite_sex_cat.ID].comfort = 50
        opposite_sex_cat.relationships[cat.ID].like = 50
        opposite_sex_cat.relationships[cat.ID].comfort = 50

        mock_get_possible_mates.return_value = ([same_sex_cat, opposite_sex_cat], [])

        Relation_Events.romantic_events(cat)

        self.assertTrue(mock_start_interaction.called)
        called_cat_to = mock_start_interaction.call_args.args[1]
        self.assertEqual(called_cat_to.gender, "male")
