import abc
import random
from typing import Tuple

from abc import ABC, abstractmethod
from scripts.cat import save_load
from scripts.cat.cats import Cat, BACKSTORIES
from scripts.cat.enums import CatAge, CatRank, CatSocial
from scripts.cat.factories.base_factory import BaseCatFactory
from scripts.cat.factories.typed_dicts import (
    MentorshipDict,
    CatTogglesDict,
    InheritanceDict,
    AfterlifeAffinityDict,
)
from scripts.cat.names import Name
from scripts.cat.pelts import Pelt
from scripts.cat.personality import Personality
from scripts.cat.skills import CatSkills
from scripts.cat.status import Status
from scripts.game_structure import game, constants

BASE_RNG = random.Random


class NewCatFactory(BaseCatFactory, ABC):
    rng = BASE_RNG()

    @classmethod
    def create_cat(cls, **overrides):
        """
        Create a new cat with randomness. Override any elements of the creation with keyword arguments
        :param overrides: Any desired overrides to the random generation
        :return: Cat object
        """
        # remove all values that are empty
        overrides = {k: v for k, v in overrides.items() if v is not None}

        status_dict = overrides.get("status_dict", {})
        if "rank" in overrides:
            status_dict["rank"] = overrides.get("rank")

        # the worst combined dependency ever
        age, moons, status = cls._determine_age_moons_and_status(
            moons=overrides.get("moons"), status_dict=status_dict
        )

        gender_dict = cls._get_random_gender_and_genderalign(age)
        # if specified, override the randomizer
        gender_dict["sex"] = overrides.get("gender", gender_dict["sex"])
        gender_dict["genderalign"] = overrides.get(
            "genderalign", gender_dict["genderalign"]
        )

        if pelt := overrides.get("pelt"):
            pelt = Pelt(pelt)
        else:
            pelt = cls._get_random_pelt(
                gender_dict["sex"],
                (overrides.get("parent1"), overrides.get("parent2")),
                age,
                no_disabling_scars=overrides.get("no_disabling_scars", False),
            )

        skills = overrides.get(
            "skill_dict", cls._get_random_skills_dict(status.rank, age)
        )
        if not isinstance(skills, CatSkills):
            skills = CatSkills(skill_dict=skills)

        mate = overrides.get("mate", [])
        if isinstance(mate, str):
            mate = [mate]

        cat_params = {
            "ID": cls.get_free_id(),
            "gender_dict": gender_dict,
            "pelt": pelt,
            "moons": moons,
            "status": status,
            "backstory": overrides.get(
                "backstory",
                cls._get_random_backstory_from_status(status, age),
            ),
            "skills": skills,
            "personality": cls._get_random_personality(age),
            "mentorship": MentorshipDict(
                mentor=None,
                former_mentor=[],
                patrol_with_mentor=0,
                apprentice=[],
                former_apprentices=[],
            ),
            "inheritance": InheritanceDict(
                parent1=overrides.get("parent1"),
                parent2=overrides.get("parent2"),
                adoptive_parents=overrides.get("adoptive_parents", []),
                faded_offspring=[],
                mate=mate,
                previous_mates=[],
            ),
            "affinity": AfterlifeAffinityDict(starclan=0, dark_forest=0),
            "toggles": CatTogglesDict(
                no_kits=False,
                no_mates=False,
                no_retire=False,
                prevent_fading=False,
                favourite=False,
            ),
            "experience": overrides.get(
                "experience", cls._get_random_experience(age, moons)
            ),
            "birth_cooldown": overrides.get("birth_cooldown", 0),
            "faded": False,
            "specsuffix_hidden": False,
        }

        cat = Cat(**cat_params)

        cat.name = Name(
            prefix=overrides.get("prefix"),
            suffix=overrides.get("suffix"),
            specsuffix_hidden=overrides.get("specsuffix_hidden", False),
            load_existing_name=True,
            cat=cat,
        )

        Cat.all_cats[cat.ID] = cat

        return cat

    @classmethod
    @abstractmethod
    def _get_random_age(cls) -> CatAge:
        return cls.rng.choice([*CatAge])

    @classmethod
    @abstractmethod
    def _get_random_age_from_rank(cls, rank) -> CatAge:
        """
        :param rank: Provided cat's rank
        :return: Random CatAge appropriate for the cat's rank
        """
        if not isinstance(rank, CatRank):
            rank = CatRank(rank)

        if rank == CatRank.NEWBORN:
            return CatAge.NEWBORN
        if rank == CatRank.KITTEN:
            return CatAge.KITTEN
        if rank == CatRank.ELDER:
            return CatAge.SENIOR
        if rank.is_any_apprentice_rank():
            return CatAge.ADOLESCENT

        return cls.rng.choice(
            [
                CatAge.YOUNG_ADULT,
                CatAge.ADULT,
                CatAge.ADULT,
                CatAge.SENIOR_ADULT,
            ]
        )

    @classmethod
    @abstractmethod
    def _get_random_status_from_age(cls, age) -> Status:
        status = Status()
        status.generate_new_status(age)

        return status

    @staticmethod
    @abstractmethod
    def _get_random_backstory_from_status(status: Status, age: CatAge):
        if status.social == CatSocial.CLANCAT:
            return "clanborn"

        social_category = str(status.rank) + "_backstories"

        if age.is_baby():
            social_category = f"baby_{social_category}"
        possible_backstories = BACKSTORIES["backstory_categories"][social_category]

        return random.choice(possible_backstories)

    @classmethod
    @abstractmethod
    def _get_random_moons(cls, age: CatAge) -> int:
        """
        Generate random moons appropriate for the given age
        :param age: CatAge
        :return: Appropriate moons
        """
        return cls.rng.randint(Cat.age_moons[age][0], Cat.age_moons[age][1])

    @classmethod
    def _determine_age_moons_and_status(
        cls, moons, status_dict
    ) -> Tuple[CatAge, int, Status]:
        """
        Figure out the age, moons and status of a cat depending on what's provided

        :param moons: Moons of the cat
        :param status_dict: Status dict describing the cat
        :return: CatAge, moons and Status that all agree with one another
        """
        age = None
        if status_dict and moons is not None:
            return CatAge.get_from_moons(moons), moons, Status(**status_dict)
        if not status_dict and moons is None:
            age = cls._get_random_age()
            status = cls._get_random_status_from_age(age)
            moons = cls._get_random_moons(age)
        elif not status_dict and moons is not None:
            age = CatAge.get_from_moons(moons)
            status = cls._get_random_status_from_age(age)
        elif status_dict and moons is None:
            if "rank" in status_dict:
                age = cls._get_random_age_from_rank(status_dict["rank"])
            elif (
                "group_history" in status_dict
                and "rank" in status_dict["group_history"][-1]
            ):
                age = cls._get_random_age_from_rank(
                    status_dict["group_history"][-1]["rank"]
                )
            else:
                age = cls._get_random_age()
            status = Status(**status_dict)
            moons = cls._get_random_moons(age)
        else:
            status = None

        if not isinstance(moons, int) or not status or not age:
            raise Exception("Something went wrong generating age, moons or status_dict")

        return age, moons, status

    @classmethod
    @abstractmethod
    def _get_random_gender_and_genderalign(cls, age) -> dict:
        gender = {
            "sex": cls.rng.choice(("male", "female")),
        }
        gender["genderalign"] = gender["sex"]

        return gender

    @staticmethod
    def _get_random_pelt(gender, parents, age, no_disabling_scars: bool):
        pelt = Pelt.generate_new_pelt(
            gender,
            tuple(Cat.fetch_cat(i) for i in parents if i),
            age,
        )

        # ================================
        #  GENETICS ENFORCEMENT (REALISM)
        # ================================

        # --- Male tortie rarity enforcement (KITS ONLY) ---
        if (
            self.age in (CatAge.NEWBORN, CatAge.KITTEN)
            and self.pelt.name in Pelt.torties
            and self.gender == "male"
        ):
            # 1 / 3000 chance to keep male tortie, slightly increased as per what pelts.py should've done - increased tortie chance if the mom's a tortie herself
            if random_module.randint(1, 2800) != 1:
                self.gender = "female"
                self.genderalign = "female"
                print("Regular female tortie :)")
            self.no_kits = False
            if self.gender == "male":
                print("RARE MALE TORTIE GENERATED")
                self.no_kits = True

        # --- Female ginger rarity ---
        if (
            self.pelt.colour in Pelt.ginger_colours
            and self.gender == "female"
            and self.pelt.name not in Pelt.torties
        ):
            allow_female_ginger = False
            allow_tortie_instead = False

            mother = Cat.fetch_cat(self.parent1) if self.parent1 else None
            father = Cat.fetch_cat(self.parent2) if self.parent2 else None

            mother_has_orange = mother and (
                mother.pelt.colour in Pelt.ginger_colours
                or mother.pelt.tortie_colour in Pelt.ginger_colours
            )
            father_is_ginger = father and father.pelt.colour in Pelt.ginger_colours
            mother_is_dark = mother and (
                mother.pelt.colour
                in list(Pelt.black_colours)
                + list(Pelt.brown_colours)
                + ["SILVER", "PALEGREY"]
            )
            father_is_dark = father and (
                father.pelt.colour
                in list(Pelt.black_colours)
                + list(Pelt.brown_colours)
                + ["SILVER", "PALEGREY"]
            )

            if self.age in (CatAge.NEWBORN, CatAge.KITTEN) and mother and father:
                if mother_has_orange and father_is_ginger:
                    allow_female_ginger = True
                    print("Uncommon ginger she-cat generated thanks to her genetics!!!")
                elif mother_is_dark and father_is_ginger:
                    allow_tortie_instead = True
                elif mother_has_orange and father_is_dark:
                    allow_tortie_instead = True
                elif (
                    father_is_dark
                    and mother_is_dark
                    and mother.pelt.name not in ["Tortie", "Calico"]
                ):
                    # preventing ginger she-cats from being birthed by 2 non-ginger pelted parents, because yes, this has happened before...
                    self.pelt.colour = mother.pelt.colour
                    return

            if not allow_female_ginger:
                if allow_tortie_instead:
                    # Tortie construction time!
                    if self.pelt.white_patches in (
                        Pelt.high_white + Pelt.mostly_white + ["FULLWHITE"]
                    ):
                        self.pelt.name = "Calico"
                    else:
                        self.pelt.name = "Tortie"

                    #  assigning the base color
                    if mother_is_dark:
                        self.pelt.colour = mother.pelt.colour
                    elif father_is_dark:
                        self.pelt.colour = father.pelt.colour

                    # assigning the base pelt pattern
                    if mother.pelt.name not in ["Tortie", "Calico"]:
                        self.pelt.tortie_base = choice(
                            [mother.pelt.name, father.pelt.name]
                        ).lower()
                        if mother.pelt.name in [
                            "SingleColour",
                            "TwoColour",
                        ] or father.pelt.name in ["SingleColour", "TwoColour"]:
                            self.pelt.tortie_base = "single"
                    elif mother.pelt.name in ["Tortie", "Calico"]:
                        self.pelt.tortie_base = choice(
                            [mother.pelt.tortie_base, father.pelt.name]
                        ).lower()
                        if father.pelt.name in ["SingleColour", "TwoColour"]:
                            self.pelt.tortie_base = "single"

                    # --- ensure tortie data is fully assigned ---
                    if not self.pelt.tortie_colour:
                        if mother.pelt.colour in Pelt.ginger_colours:
                            self.pelt.tortie_colour = mother.pelt.colour
                        elif mother.pelt.tortie_colour in Pelt.ginger_colours:
                            self.pelt.tortie_colour = mother.pelt.tortie_colour
                        else:
                            self.pelt.tortie_colour = father.pelt.colour

                    if not self.pelt.tortie_pattern:
                        self.pelt.tortie_pattern = self.pelt.tortie_base

                    if not self.pelt.tortie_marking:
                        self.pelt.tortie_marking = choice(Pelt.tortie_patches)

                    print("Tortie kit generated thanks to her genetics!!!")

            if not allow_female_ginger and not allow_tortie_instead:
                # If this is a ginger she-cat spawned randomly out of the wild, apply 20% rule - only 20% of ginger cats are female
                if self.skip_female_rarity_roll:
                    print("Event can_birth cat keeps female rarity-restricted pelt")
                elif random_module.randint(1, 5) != 1:
                    self.gender = "male"
                    self.genderalign = "male"
                    print("Regular orange tomcat :)")
                else:
                    print("Uncommon ginger she-cat generated!!!")

        # Male ginger cat genetic realism
        if self.pelt.colour in Pelt.ginger_colours and self.gender == "male":
            copy_mothers_pelt = False

            mother = Cat.fetch_cat(self.parent1) if self.parent1 else None
            father = Cat.fetch_cat(self.parent2) if self.parent2 else None

            mother_has_orange = mother and (
                mother.pelt.colour in Pelt.ginger_colours
                or mother.pelt.tortie_colour in Pelt.ginger_colours
            )
            father_is_ginger = father and father.pelt.colour in Pelt.ginger_colours

            if self.age in (CatAge.NEWBORN, CatAge.KITTEN) and mother and father:
                if not mother_has_orange and father_is_ginger:
                    copy_mothers_pelt = True
                elif mother_has_orange and not father_is_ginger:
                    copy_mothers_pelt = True
                elif not mother_has_orange and not father_is_ginger:
                    copy_mothers_pelt = True

                if copy_mothers_pelt:
                    if mother.pelt.tortie_colour in Pelt.ginger_colours:
                        self.pelt.colour = mother.pelt.tortie_colour
                    else:
                        self.pelt.colour = mother.pelt.colour

        # Male dark cat genetic realism
        if (
            self.pelt.colour
            in (
                list(Pelt.black_colours)
                + list(Pelt.brown_colours)
                + ["SILVER", "PALEGREY"]
            )
            and self.gender == "male"
        ):
            copy_mothers_pelt = False
            copy_tortie_color = False

            mother = Cat.fetch_cat(self.parent1) if self.parent1 else None
            father = Cat.fetch_cat(self.parent2) if self.parent2 else None
            dark_colours = (
                list(Pelt.black_colours)
                + list(Pelt.brown_colours)
                + ["SILVER", "PALEGREY"]
            )
            mother_is_dark = mother and mother.pelt.colour in dark_colours
            father_is_dark = father and father.pelt.colour in dark_colours
            mother_is_tortie = (
                mother and mother.pelt.tortie_colour in Pelt.ginger_colours
            )

            if self.age in (CatAge.NEWBORN, CatAge.KITTEN) and mother and father:
                if not mother_is_dark and father_is_dark:
                    copy_mothers_pelt = True
                elif mother_is_dark and not father_is_dark:
                    if mother_is_tortie:
                        if random_module.randint(0, 1) == 0:
                            copy_tortie_color = True
                        else:
                            copy_mothers_pelt = True
                    else:
                        copy_mothers_pelt = True

                if copy_mothers_pelt:
                    self.pelt.colour = mother.pelt.colour
                elif copy_tortie_color:
                    if father.pelt.colour in Pelt.ginger_colours:
                        if random_module.randint(0, 1) == 0:
                            self.pelt.colour = father.pelt.colour
                        else:
                            self.pelt.colour = mother.pelt.tortie_colour
        # --- Female dark cat rarity ---
        if (
            self.pelt.colour
            in (
                list(Pelt.black_colours)
                + list(Pelt.brown_colours)
                + ["SILVER", "PALEGREY"]
            )
            and self.gender == "female"
            and self.pelt.name not in Pelt.torties
        ):
            allow_female_dark = False
            allow_tortie_instead = False

            mother = Cat.fetch_cat(self.parent1) if self.parent1 else None
            father = Cat.fetch_cat(self.parent2) if self.parent2 else None

            dark_colours = (
                list(Pelt.black_colours)
                + list(Pelt.brown_colours)
                + ["SILVER", "PALEGREY"]
            )
            mother_is_dark = mother and mother.pelt.colour in dark_colours
            father_is_dark = father and father.pelt.colour in dark_colours
            mother_has_orange = mother and (
                mother.pelt.colour in Pelt.ginger_colours
                or mother.pelt.name in Pelt.torties
            )
            father_is_ginger = father and father.pelt.colour in Pelt.ginger_colours

            if self.age in (CatAge.NEWBORN, CatAge.KITTEN) and mother and father:
                if mother_is_dark and father_is_dark:
                    allow_female_dark = True
                elif mother_is_dark and father_is_ginger:
                    allow_tortie_instead = True
                elif mother_has_orange and father_is_dark:
                    allow_tortie_instead = True
                elif (
                    father_is_ginger
                    and mother_has_orange
                    and mother.pelt.name not in ["Tortie", "Calico"]
                ):
                    # preventing dark she-cats from being birthed by 2 ginger pelted parents, because yes, this has happened before...
                    self.pelt.colour = mother.pelt.colour
                    return

            if not allow_female_dark:
                if allow_tortie_instead:
                    # Tortie construction time!
                    if self.pelt.white_patches in (
                        Pelt.high_white + Pelt.mostly_white + ["FULLWHITE"]
                    ):
                        self.pelt.name = "Calico"
                    else:
                        self.pelt.name = "Tortie"

                    #  assigning the base color
                    if mother_is_dark:
                        self.pelt.colour = mother.pelt.colour
                    elif father_is_dark:
                        self.pelt.colour = father.pelt.colour

                    # assigning the base pelt pattern
                    if mother.pelt.name not in ["Tortie", "Calico"]:
                        self.pelt.tortie_base = choice(
                            [mother.pelt.name, father.pelt.name]
                        ).lower()
                        if mother.pelt.name in [
                            "SingleColour",
                            "TwoColour",
                        ] or father.pelt.name in ["SingleColour", "TwoColour"]:
                            self.pelt.tortie_base = "single"
                    elif mother.pelt.name in ["Tortie", "Calico"]:
                        self.pelt.tortie_base = choice(
                            [mother.pelt.tortie_base, father.pelt.name]
                        ).lower()
                        if father.pelt.name in ["SingleColour", "TwoColour"]:
                            self.pelt.tortie_base = "single"

                    # Ensuring that the tortie data is fully assigned
                    if not self.pelt.tortie_colour:
                        if mother.pelt.colour in Pelt.ginger_colours:
                            self.pelt.tortie_colour = mother.pelt.colour
                        elif mother.pelt.tortie_colour in Pelt.ginger_colours:
                            self.pelt.tortie_colour = mother.pelt.tortie_colour
                        else:
                            self.pelt.tortie_colour = father.pelt.colour

                    if not self.pelt.tortie_pattern:
                        self.pelt.tortie_pattern = self.pelt.tortie_base

                    if not self.pelt.tortie_marking:
                        self.pelt.tortie_marking = choice(Pelt.tortie_patches)

                    print("Tortie kit generated thanks to her genetics!!!")

            if (
                not allow_female_dark
                and not allow_tortie_instead
                and self.pelt.colour in ("BLACK", "GHOST")
            ):
                # If this is a black she-cat spawned randomly out of the wild, apply 25% rule - Roughly 70-75% of black cats are female
                if self.skip_female_rarity_roll:
                    print("Event can_birth cat keeps female rarity-restricted pelt")
                elif random_module.randint(1, 4) != 1:
                    self.gender = "male"
                    self.genderalign = "male"
                    print("Regular black tomcat :)")
                else:
                    print("Uncommon black she-cat generated!!!")

        # Making sure if older "male" torties are infertile, as they're really just intersex cats and therefore sterile
        if (
            self.age not in (CatAge.NEWBORN, CatAge.KITTEN)
            and self.pelt.name in Pelt.torties
            and self.gender == "male"
        ):
            self.no_kits = True
            print("RARE MALE TORTIE GENERATED!!!")
        
        if no_disabling_scars:
            # code copied from removed create_cat function
            # used for generating new cats for a fresh Clan
            not_allowed_scars = (
                "NOPAW",
                "NOTAIL",
                "HALFTAIL",
                "NOEAR",
                "BOTHBLIND",
                "RIGHTBLIND",
                "LEFTBLIND",
                "BRIGHTHEART",
                "NOLEFTEAR",
                "NORIGHTEAR",
                "MANLEG",
                "BLIND",
            )

            pelt.scars = tuple(
                scar for scar in pelt.scars if scar not in not_allowed_scars
            )
        return pelt

    @classmethod
    @abstractmethod
    def _get_random_personality(cls, age: CatAge):
        return Personality(kit_trait=age.is_baby())

    @classmethod
    @abstractmethod
    def _get_random_experience(cls, age, moons: int) -> int:
        if age.is_baby():
            return 0

        if age == CatAge.ADOLESCENT:
            experience = 0
            ran = constants.CONFIG["graduation"]["base_app_timeskip_ex"]
            for i in range(Cat.age_moons[CatAge.ADOLESCENT][0], moons, -1):
                exp = cls.rng.choice(
                    list(range(ran[0][0], ran[0][1] + 1))
                    + list(range(ran[1][0], ran[1][1] + 1))
                )
                experience += exp + 3
            return experience
        elif age in (CatAge.YOUNG_ADULT, CatAge.ADULT):
            return cls.rng.randint(
                Cat.experience_levels_range["prepared"][0],
                Cat.experience_levels_range["proficient"][1],
            )
        elif age == CatAge.SENIOR_ADULT:
            return cls.rng.randint(
                Cat.experience_levels_range["proficient"][0],
                Cat.experience_levels_range["adept"][1],
            )
        elif age == CatAge.SENIOR:
            return cls.rng.randint(
                Cat.experience_levels_range["adept"][0],
                Cat.experience_levels_range["masterful"][1],
            )
        else:
            return 0

    @classmethod
    @abstractmethod
    def _get_random_skills_dict(cls, rank, age):
        skills = CatSkills.generate_new_catskills(rank, age, rng=cls.rng)
        return skills

    @staticmethod
    def get_free_id():
        potential_id = str(next(Cat.id_iter))

        if game.clan:
            faded_cats = save_load.get_faded_ids()
        else:
            faded_cats = []

        while potential_id in Cat.all_cats or potential_id in faded_cats:
            potential_id = str(next(Cat.id_iter))
        return potential_id
