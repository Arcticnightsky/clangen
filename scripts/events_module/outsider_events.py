import random

from typing import TYPE_CHECKING

import i18n

from scripts.game_structure import constants
from scripts.cat.enums import CatGroup, CatSocial
from scripts.clan_package.settings import get_clan_setting
from scripts.event_class import Single_Event
from scripts.game_structure import game
from scripts.game_structure.localization import load_lang_resource

if TYPE_CHECKING:
    from scripts.cat.cats import Cat

# ---------------------------------------------------------------------------- #
#                               New Cat Event Class                              #
# ---------------------------------------------------------------------------- #


class OutsiderEvents:
    """All events with a connection to outsiders."""

    @staticmethod
    def killing_outsiders(cat: "Cat"):
        if info_dict := get_clan_setting("lead_den_outsider_event"):
            if cat.ID == info_dict["cat_ID"]:
                return

        deaths = load_lang_resource("events/death/outsider_deaths/outsider_deaths.json")

        # killing outside cats
        if random.getrandbits(6) == 1 and not cat.dead:
            death_history = i18n.t("events.death.outsider_deaths.history.default")

            if cat.status.is_exiled(CatGroup.PLAYER_CLAN_ID):
                text = random.choice(deaths["exiled"])
                death_history = i18n.t("events.death.outsider_deaths.history.exiled")
            elif cat.status.is_lost(CatGroup.PLAYER_CLAN_ID):
                text = random.choice(deaths["lost"])
                death_history = i18n.t("events.death.outsider_deaths.history.lost")
            elif cat.status.is_other_clancat or (
                cat.status.is_former_clancat
                and not cat.status.get_last_valid_group_id() == CatGroup.PLAYER_CLAN_ID
            ):
                group_id = cat.status.get_last_valid_group_id()
                if cat.status.is_exiled(group_id):
                    text = random.choice(deaths["other_clan_exiled"])
                    death_history = i18n.t(
                        "events.death.outsider_deaths.history.other_clan_exiled"
                    )
                elif cat.status.is_lost(group_id):
                    text = random.choice(deaths["other_clan_lost"])
                    death_history = i18n.t(
                        "events.death.outsider_deaths.history.other_clan_lost"
                    )
                else:
                    text = random.choice(deaths["other_clan"])
                    death_history = i18n.t(
                        "events.death.outsider_deaths.history.other_clan"
                    )

                clanname = [
                    c for c in game.clan.all_other_clans if c.group_ID == group_id
                ][0].name
                text = text.replace("o_c_n", clanname)
                death_history = death_history.replace("o_c_n", clanname)
            elif cat.status.is_outsider:
                text = random.choice(deaths[cat.status.social.value])
                death_history = i18n.t(
                    f"events.death.outsider_deaths.history.{cat.status.social.value}"
                )
            elif cat.moons >= 150 and not cat.dead and not (
                cat.status.is_exiled(CatGroup.PLAYER_CLAN) or cat.status.is_lost()
            ) and cat.status.is_outsider:

                age_start = constants.CONFIG["death_related"]["old_age_death_start"]
                death_curve_setting = constants.CONFIG["death_related"]["old_age_death_curve"]
                death_curve_value = 0.001 * death_curve_setting
                old_age_death_chance = ((1 + death_curve_value) ** (cat.moons - age_start)) - 1
                sterilized = any(cond in cat.permanent_condition for cond in ("neutered", "spayed"))
                if sterilized:
                    old_age_death_chance *= 0.7
                max_old_age = 324 if sterilized else 300

                social = i18n.t(f"general.{cat.status.social}", count=1)

                if random.random() <= old_age_death_chance:
                    text = (
                        f"Rumors reach your Clan that the {social}, "
                        f"{cat.name}, has died recently."
                    )
                    death_history = "m_c died of old age."

                elif cat.moons >= max_old_age:
                    text = (
                        f"Rumors reach your Clan that the {social}, "
                        f"{cat.name}, has died recently."
                    )
                    death_history = "m_c died of old age."

                else:
                    text = (
                        f"Rumors reach your Clan that the {social}, "
                        f"{cat.name}, has died recently."
                    )
                    death_history = "m_c died while roaming around."
            else:
                text = random.choice(deaths["default"])

            cat.history.add_death(death_text=death_history)
            cat.die(grief_allowed=False)
            if cat.status.is_other_clancat:
                game.cur_events_list.append(
                    Single_Event(
                        text, ["birth_death", "other_clans"], cat_dict={"m_c": cat}
                    )
                )
            else:
                game.cur_events_list.append(
                    Single_Event(text, "birth_death", cat_dict={"m_c": cat})
                )
