from __future__ import annotations

from typing import Dict, Iterable, List

import streamlit as st


def inject_evenz_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {max-width: 900px; padding-top: 2rem; padding-bottom: 4rem;}
        .base-soft {font-size: 1.05rem; opacity: 0.82; line-height: 1.55;}
        .base-card {
            padding: 1rem 1.1rem;
            border: 1px solid rgba(120,120,120,.25);
            border-radius: 18px;
            background: rgba(250,247,241,.65);
            min-height: 138px;
        }
        .base-note {
            padding: .9rem 1rem;
            border-left: 3px solid rgba(80, 95, 70, .55);
            background: rgba(250,247,241,.55);
            border-radius: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def soft_header(title: str, body: str) -> None:
    st.title(title)
    st.markdown(f'<div class="base-soft">{body}</div>', unsafe_allow_html=True)


def card_grid(options: List[Dict[str, str]], state_key: str, columns: int = 3) -> List[str]:
    selected = set(st.session_state.get(state_key, []))
    cols = st.columns(columns)
    for index, option in enumerate(options):
        label = option["label"]
        value = option["value"]
        active = value in selected
        button_label = f"✓ {label}" if active else label
        with cols[index % columns]:
            if st.button(button_label, key=f"{state_key}-{value}", use_container_width=True):
                if active:
                    selected.remove(value)
                else:
                    selected.add(value)
    st.session_state[state_key] = list(selected)
    return list(selected)


def chapter_grid(chapters: Iterable[Dict[str, str]], state_key: str) -> List[str]:
    options = [
        {
            "value": str(chapter.get("slug", "")),
            "label": f'{chapter.get("emoji", "")} {chapter.get("name", "")}'.strip(),
        }
        for chapter in chapters
    ]
    return card_grid(options, state_key=state_key, columns=2)


def metric_card(title: str, body: str, accent: str = "") -> None:
    label = f"{accent} {title}".strip()
    st.markdown(
        f"""
        <div class="base-card">
            <div style="font-size:1rem; font-weight:600; margin-bottom:.35rem;">{label}</div>
            <div class="base-soft">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
