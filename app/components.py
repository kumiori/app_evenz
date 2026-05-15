from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

import streamlit as st


def inject_evenz_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top, rgba(54, 67, 92, 0.28), transparent 32%),
                linear-gradient(180deg, #11141a 0%, #0a0d11 100%);
            color: #f4f1e8;
        }
        .block-container {
            max-width: 560px;
            padding-top: 1.3rem;
            padding-bottom: 3rem;
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"] {
            background: rgba(12, 15, 20, 0.96);
        }
        .evenz-soft {
            font-size: 1.02rem;
            opacity: 0.84;
            line-height: 1.55;
        }
        .evenz-note {
            padding: .95rem 1rem;
            border-radius: 18px;
            background: rgba(255,255,255,.05);
            border: 1px solid rgba(255,255,255,.09);
        }
        .evenz-step {
            font-size: .82rem;
            letter-spacing: .08em;
            text-transform: uppercase;
            opacity: .6;
            margin-bottom: .45rem;
        }
        .evenz-summary {
            padding: 1rem 1.1rem;
            border-radius: 18px;
            background: rgba(255,255,255,.05);
            border: 1px solid rgba(255,255,255,.10);
            margin-bottom: .75rem;
        }
        .stButton > button,
        .stDownloadButton > button {
            min-height: 3.5rem;
            border-radius: 18px;
            border: 1px solid rgba(255,255,255,.14);
            background: rgba(255,255,255,.05);
            color: #f4f1e8;
            font-size: 1rem;
            font-weight: 500;
        }
        .stButton > button:hover {
            border-color: rgba(255,255,255,.32);
            background: rgba(255,255,255,.08);
        }
        .stTextInput input, .stTextArea textarea, .stDateInput input, .stTimeInput input {
            background: rgba(255,255,255,.05) !important;
            color: #f4f1e8 !important;
            border-radius: 14px !important;
        }
        .stCheckbox label, .stRadio label, .stSelectbox label {
            color: #f4f1e8 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def soft_header(title: str, body: str, step: str = "") -> None:
    if step:
        st.markdown(f'<div class="evenz-step">{step}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="evenz-soft">{body}</div>', unsafe_allow_html=True)


def summary_block(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="evenz-summary">
            <div style="font-size:.9rem; opacity:.65; margin-bottom:.35rem;">{title}</div>
            <div style="font-size:1.02rem;">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(title: str, body: str, accent: str = "") -> None:
    label = f"{accent} {title}".strip()
    st.markdown(
        f"""
        <div class="evenz-summary">
            <div style="font-size:.96rem; font-weight:600; margin-bottom:.35rem;">{label}</div>
            <div class="evenz-soft">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def native_multiselect_pills(
    label: str,
    options: Sequence[Dict[str, str]],
    state_key: str,
) -> List[str]:
    values = [item["value"] for item in options]
    labels = {item["value"]: item["label"] for item in options}
    current = list(st.session_state.get(state_key, []))
    selected = st.pills(
        label,
        values,
        selection_mode="multi",
        default=current,
        key=state_key,
        format_func=lambda value: labels.get(value, str(value)),
        label_visibility="collapsed",
    )
    return list(selected or [])


def native_single_segmented(
    label: str,
    options: Sequence[Tuple[str, str]],
    state_key: str,
    default: str,
) -> str:
    values = [item[0] for item in options]
    labels = {item[0]: item[1] for item in options}
    current = str(st.session_state.get(state_key, default))
    selected = st.segmented_control(
        label,
        values,
        default=current if current in values else default,
        key=state_key,
        format_func=lambda value: labels.get(value, str(value)),
        label_visibility="collapsed",
    )
    return str(selected or default)


def review_line(label: str, value: str) -> None:
    summary_block(label, value or "—")
