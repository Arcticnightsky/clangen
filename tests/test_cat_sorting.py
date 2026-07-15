from types import SimpleNamespace

from scripts.cat.cats import Cat
from scripts.game_structure.game.switches import Switch, switch_get_value, switch_set_value


def make_cat(prefix):
    return SimpleNamespace(name=SimpleNamespace(prefix=prefix))


def test_insert_cat_sorts_names_alphabetically():
    original_cats = Cat.all_cats_list
    original_sort_type = switch_get_value(Switch.sort_type)
    Cat.all_cats_list = [make_cat("Bramble"), make_cat("Dawn")]
    switch_set_value(Switch.sort_type, "name")

    try:
        Cat.insert_cat(make_cat("Crested"))

        assert [cat.name.prefix for cat in Cat.all_cats_list] == [
            "Bramble",
            "Crested",
            "Dawn",
        ]
    finally:
        Cat.all_cats_list = original_cats
        switch_set_value(Switch.sort_type, original_sort_type)


def test_insert_cat_sorts_names_reverse_alphabetically():
    original_cats = Cat.all_cats_list
    original_sort_type = switch_get_value(Switch.sort_type)
    Cat.all_cats_list = [make_cat("Dawn"), make_cat("Crest"), make_cat("Bramble")]
    switch_set_value(Switch.sort_type, "reverse_name")

    try:
        Cat.insert_cat(make_cat("Crested"))

        assert [cat.name.prefix for cat in Cat.all_cats_list] == [
            "Dawn",
            "Crested",
            "Crest",
            "Bramble",
        ]
    finally:
        Cat.all_cats_list = original_cats
        switch_set_value(Switch.sort_type, original_sort_type)
