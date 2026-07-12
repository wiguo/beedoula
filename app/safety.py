"""Deterministic safety routing before the BeeDoula agent loop.

This module deliberately handles only high-signal emergency and urgent patterns. It
does not diagnose, select treatment, or replace clinical judgment. Rules and their
sources are documented in ``docs/safety-contract.md``.
"""

from __future__ import annotations

import re
import statistics
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any, Literal

from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph import END, START, MessagesState, StateGraph

SafetyRoute = Literal["emergency", "urgent", "routine"]

EMERGENCY_FIRST_LINE = (
    "EMERGENCY — Call your local emergency number now. Do not wait for BeeDoula."
)
EMERGENCY_RESPONSE = (
    f"{EMERGENCY_FIRST_LINE}\n\n"
    "Follow the emergency dispatcher's instructions."
)
URGENT_FIRST_LINE = (
    "URGENT — Contact the baby's pediatrician or an urgent medical service now. "
    "Do not wait for BeeDoula."
)
URGENT_RESPONSE = (
    f"{URGENT_FIRST_LINE}\n\n"
    "If the baby has trouble breathing, turns blue or grey, becomes unresponsive, "
    "or has a seizure, call your local emergency number immediately."
)


@dataclass(frozen=True)
class SafetyDecision:
    route: SafetyRoute
    matched_rule_ids: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()

    def as_metadata(self) -> dict[str, Any]:
        return asdict(self)


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    normalized = normalized.replace("’", "'")
    replacements = {
        r"\b(?:can't|cant|can not)\b": "cannot",
        r"\b(?:won't|wont)\b": "will not",
        r"\b(?:doesn't|doesnt)\b": "does not",
        r"\b(?:isn't|isnt)\b": "is not",
    }
    for pattern, replacement in replacements.items():
        normalized = re.sub(pattern, replacement, normalized)
    normalized = re.sub(r"[^a-z0-9.°']+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _is_educational_or_hypothetical(text: str) -> bool:
    return bool(
        re.search(
            r"\b(?:what (?:should|do) i do|what happens|how (?:do|can) i help) "
            r"(?:if|when)\b|\bhow (?:can|do) i prevent\b|\bfor training\b|"
            r"\bcan you explain\b|\bwhat does .{0,30} mean\b",
            text,
        )
    )


def _temperature_celsius(text: str) -> float | None:
    matches = re.findall(
        r"\b(\d{2,3}(?:\.\d+)?)\s*(?:°|degrees?\s*)?"
        r"(c|f|celsius|fahrenheit)\b",
        text,
    )
    if matches:
        value, unit = matches[-1]
        temperature = float(value)
        if unit in {"f", "fahrenheit"}:
            return (temperature - 32) * 5 / 9
        return temperature

    # Caregivers often omit "C" while typing under pressure. Treat a plausible
    # two-digit value adjacent to fever/temperature wording as Celsius.
    bare_matches = re.findall(
        r"\b(?:fever|temp(?:erature)?)\s*(?:of|is|at)?\s*"
        r"(3[5-9](?:\.\d+)?)\b",
        text,
    )
    return float(bare_matches[-1]) if bare_matches else None


def _age_under_three_months(text: str) -> bool:
    if re.search(r"\b(?:newborn|neonate)\b", text):
        return True
    if re.search(r"\b(?:under|younger than|less than) (?:three|3) months?\b", text):
        return True
    match = re.search(
        r"\b(\d{1,2})\s*(day|days|week|weeks|wk|wks|month|months|mo|mos)"
        r"(?:\s*old)?\b",
        text,
    )
    if not match:
        return False
    value = int(match.group(1))
    unit = match.group(2)
    if unit.startswith("day"):
        return value < 90
    if unit.startswith("week") or unit in {"wk", "wks"}:
        return value < 13
    return value < 3


def _add_match(
    matches: list[tuple[str, str]], rule_id: str, category: str, condition: bool
) -> None:
    if condition:
        matches.append((rule_id, category))


def classify_safety(text: str) -> SafetyDecision:
    """Classify the latest caregiver message without calling a model or network."""

    normalized = _normalize(text)
    educational = _is_educational_or_hypothetical(normalized) and not bool(
        re.search(r"\b(?:now|right now|currently|happening now)\b", normalized)
    )
    emergency: list[tuple[str, str]] = []
    urgent: list[tuple[str, str]] = []

    breathing = bool(
        re.search(
            r"\b(?:baby|infant|child|he|she|they)\b.{0,30}"
            r"\b(?:not breath(?:ing|in)|cannot breath(?:e)?|struggling to breathe|"
            r"having trouble breathing|difficulty breathing|gasping)\b",
            normalized,
        )
        or re.search(
            r"\b(?:cannot breath(?:e)?|stopped breath(?:ing|in))\b", normalized
        )
    )
    _add_match(emergency, "EMS_BREATHING_001", "breathing", breathing)

    blue_or_grey = bool(
        re.search(
            r"\b(?:lips?|tongue|face|skin)\b.{0,20}\b(?:blue|grey|gray|purple)\b",
            normalized,
        )
        or re.search(r"\bturn(?:ed|ing)? (?:blue|grey|gray|purple)\b", normalized)
        or re.search(
            r"\b(?:baby|infant|child|he|she|they) (?:is )?"
            r"(?:blue|grey|gray|purple)\b",
            normalized,
        )
    ) and not bool(re.search(r"\bblue eyes?\b|\bblue eyed\b", normalized))
    _add_match(emergency, "EMS_COLOR_001", "blue_or_grey", blue_or_grey)

    unresponsive = bool(
        re.search(r"\b(?:unresponsive|not responsive)\b", normalized)
        or re.search(r"\b(?:cannot|can not) wake (?:up )?(?:the )?baby\b", normalized)
        or re.search(
            r"\b(?:baby|infant|he|she|they)\b.{0,30}"
            r"\b(?:will not wake|not waking|hard to wake|limp|floppy)\b",
            normalized,
        )
    ) and not educational
    _add_match(emergency, "EMS_RESPONSE_001", "unresponsive", unresponsive)

    seizure = bool(
        re.search(r"\b(?:seizing|convulsing)\b", normalized)
        or re.search(r"\bseizure (?:now|rn)\b", normalized)
        or normalized in {"seizure", "seizure now", "seizure rn"}
        or re.search(
            r"\b(?:baby|infant|child|he|she|they)\b.{0,30}"
            r"\b(?:having|has|in) (?:a )?(?:seizure|fit)\b",
            normalized,
        )
    ) and not educational
    _add_match(emergency, "EMS_SEIZURE_001", "seizure", seizure)

    severe_choking = bool(
        re.search(
            r"\b(?:baby|infant|child|he|she|they)\b.{0,25}"
            r"\b(?:choking|chocking)\b",
            normalized,
        )
        or re.search(r"\bchoking (?:now|right now)\b", normalized)
        or re.search(r"\bairway (?:is )?blocked\b", normalized)
        or re.search(r"\bcannot (?:cry|cough)\b", normalized)
        or re.search(
            r"\b(?:baby|infant|child|he|she|they)\b.{0,25}"
            r"\bcannot make (?:a )?sound\b",
            normalized,
        )
    ) and not educational
    _add_match(emergency, "EMS_CHOKING_001", "choking", severe_choking)

    severe_bleeding = bool(
        re.search(r"\b(?:heavy|severe) bleeding\b", normalized)
        or re.search(r"\bbleeding (?:will not|does not) stop\b", normalized)
        or re.search(r"\bblood (?:is )?(?:pouring|spurting)\b", normalized)
    )
    _add_match(emergency, "EMS_BLEEDING_001", "severe_bleeding", severe_bleeding)

    # Fever alone usually needs prompt clinical assessment rather than an ambulance.
    temperature = _temperature_celsius(normalized)
    young_infant_fever = _age_under_three_months(normalized) and (
        (temperature is not None and temperature >= 38.0)
        or (temperature is None and bool(re.search(r"\bfever\b", normalized)))
    )
    _add_match(urgent, "URGENT_FEVER_001", "young_infant_fever", young_infant_fever)

    head_injury = bool(
        re.search(r"\b(?:fell|fall|head bump|head injury|hit (?:his|her|their) head)\b", normalized)
    )
    concerning_after_injury = bool(
        re.search(
            r"\b(?:vomit(?:ed|ing)?|unusually sleepy|very drowsy|acting strange|"
            r"not acting (?:normal|normally)|unequal pupils?)\b",
            normalized,
        )
    )
    _add_match(
        urgent,
        "URGENT_HEAD_001",
        "concerning_head_injury",
        head_injury and concerning_after_injury,
    )

    if emergency:
        return SafetyDecision(
            route="emergency",
            matched_rule_ids=tuple(rule_id for rule_id, _ in emergency),
            categories=tuple(dict.fromkeys(category for _, category in emergency)),
        )
    if urgent:
        return SafetyDecision(
            route="urgent",
            matched_rule_ids=tuple(rule_id for rule_id, _ in urgent),
            categories=tuple(dict.fromkeys(category for _, category in urgent)),
        )
    return SafetyDecision(route="routine")


def _message_text(message: Any) -> str:
    if isinstance(message, BaseMessage):
        content = message.content
    elif isinstance(message, dict):
        content = message.get("content", "")
    elif isinstance(message, (tuple, list)) and len(message) >= 2:
        content = message[1]
    else:
        content = ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            str(block.get("text", "")) if isinstance(block, dict) else str(block)
            for block in content
        )
    return str(content)


def latest_user_text(state: dict[str, Any]) -> str:
    for message in reversed(state.get("messages", [])):
        if isinstance(message, BaseMessage):
            if message.type in {"human", "user"}:
                return _message_text(message)
        elif isinstance(message, dict):
            if message.get("role") in {"human", "user"}:
                return _message_text(message)
        elif isinstance(message, (tuple, list)) and message:
            if message[0] in {"human", "user"}:
                return _message_text(message)
    return ""


def safety_route_for_state(state: dict[str, Any]) -> SafetyRoute:
    return classify_safety(latest_user_text(state)).route


def _fixed_response_node(state: dict[str, Any]) -> dict[str, list[AIMessage]]:
    decision = classify_safety(latest_user_text(state))
    content = EMERGENCY_RESPONSE if decision.route == "emergency" else URGENT_RESPONSE
    return {
        "messages": [
            AIMessage(
                content=content,
                additional_kwargs={"beedoula_safety": decision.as_metadata()},
            )
        ]
    }


def build_safety_gated_graph(agent_graph: Any):
    """Put a deterministic emergency/urgent route in front of an agent graph."""

    builder = StateGraph(MessagesState)
    builder.add_node("emergency_response", _fixed_response_node)
    builder.add_node("urgent_response", _fixed_response_node)
    builder.add_node("agent", agent_graph)
    builder.add_conditional_edges(
        START,
        safety_route_for_state,
        {
            "emergency": "emergency_response",
            "urgent": "urgent_response",
            "routine": "agent",
        },
    )
    builder.add_edge("emergency_response", END)
    builder.add_edge("urgent_response", END)
    builder.add_edge("agent", END)
    return builder.compile()


def response_for_decision(decision: SafetyDecision) -> str:
    if decision.route == "emergency":
        return EMERGENCY_RESPONSE
    if decision.route == "urgent":
        return URGENT_RESPONSE
    return ""


def percentile_95(values: list[float]) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    return statistics.quantiles(values, n=20, method="inclusive")[18]
