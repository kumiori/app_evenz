from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

import streamlit as st


PARTICIPANT_STEPS: List[str] = [
    "locale",
    "chapters",
    "identity",
    "availability",
    "capacity",
    "review",
    "done",
]


DEFAULT_DRAFT: Dict[str, Any] = {
    "locale": "fr",
    "chapters": [],
    "name": "",
    "emoji_signature": "",
    "availability_buckets": [],
    "capacities": [],
    "exact_slots": [],
    "access_key": "",
    "existing_player_id": "",
    "hydrated_from_query": False,
    "acknowledged_key": False,
    "submitted": False,
}


def init_participant_state() -> None:
    st.session_state.setdefault("evenz_step", PARTICIPANT_STEPS[0])
    st.session_state.setdefault("evenz_draft", deepcopy(DEFAULT_DRAFT))
    st.session_state.setdefault("evenz_debug_notes", [])


def reset_participant_state() -> None:
    st.session_state["evenz_step"] = PARTICIPANT_STEPS[0]
    st.session_state["evenz_draft"] = deepcopy(DEFAULT_DRAFT)
    for key in [
        "evenz_locale",
        "evenz_locale_choice",
        "evenz_active_locale",
        "evenz_chapter_pills",
        "evenz_availability_pills",
        "evenz_capacity_pills",
        "evenz_exact_slot_enabled",
        "evenz_exact_start_date",
        "evenz_exact_start_time",
        "evenz_exact_end_date",
        "evenz_exact_end_time",
    ]:
        if key in st.session_state:
            del st.session_state[key]


def current_step() -> str:
    return str(st.session_state.get("evenz_step", PARTICIPANT_STEPS[0]))


def set_step(step: str) -> None:
    if step in PARTICIPANT_STEPS:
        st.session_state["evenz_step"] = step


def next_step() -> None:
    step = current_step()
    index = PARTICIPANT_STEPS.index(step)
    if index < len(PARTICIPANT_STEPS) - 1:
        st.session_state["evenz_step"] = PARTICIPANT_STEPS[index + 1]


def previous_step() -> None:
    step = current_step()
    index = PARTICIPANT_STEPS.index(step)
    if index > 0:
        st.session_state["evenz_step"] = PARTICIPANT_STEPS[index - 1]


def get_draft() -> Dict[str, Any]:
    draft = st.session_state.get("evenz_draft")
    if not isinstance(draft, dict):
        draft = deepcopy(DEFAULT_DRAFT)
        st.session_state["evenz_draft"] = draft
    return draft


def update_draft(**values: Any) -> Dict[str, Any]:
    draft = dict(get_draft())
    draft.update(values)
    st.session_state["evenz_draft"] = draft
    return draft


def draft_value(key: str, default: Any = None) -> Any:
    return get_draft().get(key, default)


def add_exact_slot(start: str, end: str) -> None:
    draft = dict(get_draft())
    draft["exact_slots"] = [{"start": start, "end": end}]
    st.session_state["evenz_draft"] = draft


def clear_exact_slots() -> None:
    draft = dict(get_draft())
    draft["exact_slots"] = []
    st.session_state["evenz_draft"] = draft


def mark_submitted() -> None:
    update_draft(submitted=True)
    set_step("done")
