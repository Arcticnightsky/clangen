"""Compatibility helpers for cat condition operations.

These functions keep Cat's public condition API connected to the current
condition data/classes.
"""

from scripts.cat.conditions.gain_conditions import (
    gain_permanent_condition,
    gain_temporary_condition,
)


def get_ill(cat, illness_name, event_triggered=False, lethal=True, severity="default"):
    """Apply an illness using the current temporary-condition system."""
    if severity == "default":
        severity = None
    gain_temporary_condition(
        cat,
        illness_name,
        omit_moonskip=event_triggered,
        prevent_death=not lethal,
        severity=severity,
    )


def get_injured(
    cat,
    name,
    event_triggered=False,
    lethal=True,
    potential_scars=None,
    severity="default",
):
    """Apply an injury using the current temporary-condition system."""
    if severity == "default":
        severity = None
    gain_temporary_condition(
        cat,
        name,
        omit_moonskip=event_triggered,
        prevent_death=not lethal,
        severity=severity,
        scar_pool_override=potential_scars,
    )


def get_permanent_condition(cat, name, born_with=False, event_triggered=False):
    """Apply a permanent condition using the current condition system."""
    gain_permanent_condition(
        cat,
        name,
        is_congenital=born_with,
        omit_moonskip=event_triggered,
    )


def get_sterilization_condition_name(cat):
    """Return the permanent condition matching the cat's sex."""
    return "spayed" if cat.gender == "female" else "neutered"


def apply_sterilization_condition(
    cat, from_twolegs: bool = False, adjust_personality: bool = False
) -> bool:
    """Give a cat its spayed/neutered condition, avoiding duplicates."""
    condition_name = get_sterilization_condition_name(cat)
    if condition_name in cat.permanent_conditions:
        cat.pending_neuter = False
        if from_twolegs:
            cat.tnr_victim = True
        return False

    before = len(cat.permanent_conditions)
    get_permanent_condition(cat, condition_name, event_triggered=True)
    applied = len(cat.permanent_conditions) > before
    if applied:
        cat.pending_neuter = False
        if from_twolegs:
            cat.tnr_victim = True
    return applied


def handle_pending_neuter(cat):
    """Finish a scheduled neuter/spay at the next moon skip."""
    if cat.pending_neuter and not cat.dead:
        apply_sterilization_condition(cat)


def backdate_sterilization_history(cat, social_group):
    """Keep the sterilization condition's acquisition date from predating the cat."""
    condition_name = get_sterilization_condition_name(cat)
    for condition in cat.permanent_conditions:
        if condition.name == condition_name:
            # Existing sterilization is treated as having occurred no later than
            # the cat's current age; condition.moon_gained uses clan moons.
            if condition.moon_gained is None:
                condition.moon_gained = 0
            return
