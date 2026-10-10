import json
import unittest
from collections import Counter
from unittest.mock import patch

from scripts.cat.names import Name


class TestOutsiderNames(unittest.TestCase):
    def test_gendered_outsider_name_lists_partition_the_legacy_lists(self):
        with open("resources/lang/en/names.json", encoding="utf-8") as file:
            legacy_names = json.load(file)
        with open("resources/lang/en/outsider_names.json", encoding="utf-8") as file:
            outsider_names = json.load(file)

        for name_type in ("silly", "human", "loner"):
            with self.subTest(name_type=name_type):
                categories = [
                    outsider_names[f"{gender}_{name_type}_names"]
                    for gender in ("male", "female", "unisex")
                ]
                self.assertEqual(
                    Counter(sum(categories, [])),
                    Counter(legacy_names[f"{name_type}_names"]),
                )
                self.assertEqual(
                    len(set().union(*map(set, categories))), len(sum(categories, []))
                )

    def test_binary_cats_choose_matching_or_unisex_names(self):
        name_dict = {
            "male_loner_names": ["Male name"],
            "female_loner_names": ["Female name"],
            "unisex_loner_names": ["Unisex name"],
        }
        with patch.object(Name, "names_dict", name_dict), patch.object(
            Name, "load_localized_names"
        ), patch(
            "scripts.cat.names.random.choice",
            side_effect=["male_loner_names", "Male name"],
        ):
            self.assertEqual(Name.get_outsider_name("loner_names", "male"), "Male name")
        with patch.object(Name, "names_dict", name_dict), patch.object(
            Name, "load_localized_names"
        ), patch(
            "scripts.cat.names.random.choice",
            side_effect=["unisex_loner_names", "Unisex name"],
        ):
            self.assertEqual(
                Name.get_outsider_name("loner_names", "trans male"), "Unisex name"
            )

    def test_nonbinary_cats_only_choose_unisex_names(self):
        name_dict = {
            "unisex_human_names": ["Unisex name"],
        }
        with patch.object(Name, "names_dict", name_dict), patch.object(
            Name, "load_localized_names"
        ), patch(
            "scripts.cat.names.random.choice",
            side_effect=["unisex_human_names", "Unisex name"],
        ):
            self.assertEqual(
                Name.get_outsider_name("human_names", "nonbinary"), "Unisex name"
            )
