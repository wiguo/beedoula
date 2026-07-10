from __future__ import annotations

from typing import Annotated

from langchain_core.tools import tool
from langgraph.config import get_store

# Single-family prototype: one shared profile namespace. Multi-family support
# (namespace per authenticated user) is a Demo Day upgrade, not needed here.
PROFILE_NAMESPACE = ("beedoula", "baby_profile")


@tool
def save_baby_fact(
    field: Annotated[
        str,
        "short snake_case key for the fact, e.g. 'allergies', 'nap_schedule', "
        "'date_of_birth', 'pediatrician', 'feeding_amounts'",
    ],
    value: Annotated[str, "the fact to remember, stated plainly"],
) -> str:
    """Save a lasting fact about the baby (allergy, schedule, milestone, preference, house rule) to the baby's profile so it is remembered in every future conversation. Use whenever the caregiver shares durable information about the baby. Overwrites any previous value for the same field."""
    store = get_store()
    store.put(PROFILE_NAMESPACE, field, {"value": value})
    return f"Saved to baby profile: {field} = {value}"


@tool
def get_baby_profile() -> str:
    """Read everything known about this baby (age, allergies, feeding amounts, nap schedule, preferences, house rules, pediatrician contact). Call this before answering any question where the right answer depends on the specific baby."""
    store = get_store()
    items = store.search(PROFILE_NAMESPACE)
    if not items:
        return (
            "No baby profile saved yet. Ask the caregiver for basics (age, "
            "allergies) when relevant, and save what they tell you."
        )
    return "\n".join(f"- {item.key}: {item.value.get('value', item.value)}" for item in items)
