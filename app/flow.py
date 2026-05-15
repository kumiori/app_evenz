from __future__ import annotations

from typing import Dict, List

import streamlit as st


def init_participant_state() -> None:
    defaults = {
        "evenz_player_id": "",
        "evenz_access_key": "",
        "evenz_name": "",
        "evenz_emoji_signature": "",
        "evenz_existing_access_key": "",
        "evenz_chapters": [],
        "evenz_rank_1": "",
        "evenz_rank_2": "",
        "evenz_availability": [],
        "evenz_exact_start": None,
        "evenz_exact_end": None,
        "evenz_capacities": [],
        "evenz_notes": "",
        "evenz_followups": {},
        "evenz_saved": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def set_followup_selection(chapter_slug: str, selections: List[str]) -> None:
    current = dict(st.session_state.get("evenz_followups", {}))
    current[chapter_slug] = selections
    st.session_state["evenz_followups"] = current


def followup_selection(chapter_slug: str) -> List[str]:
    mapping: Dict[str, List[str]] = st.session_state.get("evenz_followups", {})
    return list(mapping.get(chapter_slug, []))
