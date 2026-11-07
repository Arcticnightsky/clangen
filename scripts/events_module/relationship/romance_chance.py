"""Shared chance gates for same-sex romance systems."""

import random

SAME_SEX_ROMANCE_CHANCE = 25000


def cats_are_same_sex(cat_from, cat_to) -> bool:
    """Return True when two cats have the same sex/gender value."""
    return bool(cat_from and cat_to and cat_from.gender == cat_to.gender)


def cat_is_sterilized(cat) -> bool:
    """Return True when a cat has a sterilization permanent condition."""
    return bool(
        cat
        and any(
            condition in getattr(cat, "permanent_condition", {})
            for condition in ("neutered", "spayed")
        )
    )


def cats_are_mixed_sterilization(cat_from, cat_to) -> bool:
    """Return True when only one cat in a pair is spayed/neutered."""
    return cat_is_sterilized(cat_from) != cat_is_sterilized(cat_to)


def passes_same_sex_romance_chance(cat_from, cat_to) -> bool:
    """Return whether a generated same-sex romance attempt is allowed."""
    if not cats_are_same_sex(cat_from, cat_to):
        return True

    return random.randint(1, SAME_SEX_ROMANCE_CHANCE) == 1
