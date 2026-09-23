import inspect
import os
import unittest
from types import SimpleNamespace

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from scripts import events
from scripts.clan_resources.herb.herb_supply import HerbSupply
from scripts.game_structure import game


class TestHerbGatheringFocus(unittest.TestCase):
    def test_focus_herbs_are_collected_for_med_den_stores(self):
        """The focus message should correspond to herbs actually added to stores."""
        herb_supply = HerbSupply()
        original_clan = game.clan
        original_get_found_herbs = herb_supply.get_found_herbs

        try:
            game.clan = SimpleNamespace(herb_supply=herb_supply)

            def fake_get_found_herbs(*_args, **_kwargs):
                herb_supply.add_herb("juniper", 3)
                return ["3 juniper bunches"], {"juniper": 3}

            herb_supply.get_found_herbs = fake_get_found_herbs

            herb_supply.handle_focus([object()], assistants=[object()])

            self.assertEqual(herb_supply.collected["juniper"], 3)
            self.assertEqual(herb_supply.total_of_herb("juniper"), 3)
        finally:
            herb_supply.get_found_herbs = original_get_found_herbs
            game.clan = original_clan

    def test_moonskip_handles_normal_herb_cycle_before_focus(self):
        """Focus herbs should not be spent by the same moon's treatment pass."""
        source = inspect.getsource(events.one_moon)

        self.assertLess(
            source.index("game.clan.herb_supply.handle_moon"),
            source.index("handle_focus()"),
        )
