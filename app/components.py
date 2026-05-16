from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

import streamlit as st


def inject_evenz_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --evenz-bg: #0b0f16;
            --evenz-fg: #f4f1e8;
            --evenz-muted: rgba(244, 241, 232, 0.72);
            --evenz-border: rgba(255, 255, 255, 0.14);
            --evenz-border-strong: rgba(255, 255, 255, 0.24);
            --evenz-panel: rgba(255, 255, 255, 0.05);
            --evenz-panel-strong: rgba(255, 255, 255, 0.08);
            --evenz-accent: #ff565c;
            --evenz-accent-soft: rgba(132, 38, 44, 0.26);
            --evenz-space-1: 0.875rem;
            --evenz-space-2: 1.25rem;
            --evenz-space-3: 1.75rem;
            --evenz-space-4: 2.5rem;
            --evenz-space-5: 3.5rem;
            --evenz-body-size: 1.0625rem;
            --evenz-body-line: 1.6;
            --evenz-heading-line: 1.08;
            --evenz-pill-size: clamp(1.8rem, 5.2vw, 2.5rem);
        }
        .stApp {
            background:
                radial-gradient(circle at top, rgba(54, 67, 92, 0.28), transparent 32%),
                linear-gradient(180deg, #11141a 0%, var(--evenz-bg) 100%);
            color: var(--evenz-fg);
        }
        .block-container {
            max-width: 720px;
            padding: var(--evenz-space-4) var(--evenz-space-3) var(--evenz-space-5);
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"] {
            background: rgba(12, 15, 20, 0.96);
        }
        h1, h2, h3, h4, h5, h6 {
            color: var(--evenz-fg);
            line-height: var(--evenz-heading-line);
            letter-spacing: -0.045em;
            margin: 0;
            text-wrap: balance;
        }
        h1 {
            font-size: clamp(3rem, 10vw, 5rem);
            margin-bottom: var(--evenz-space-2);
        }
        h1 a {
            display: none !important;
        }
        p, li, [data-testid="stMarkdownContainer"] p {
            font-size: var(--evenz-body-size);
            line-height: var(--evenz-body-line);
        }
        [data-testid="stVerticalBlock"] > div {
            margin-bottom: 0;
        }
        .evenz-soft {
            font-size: var(--evenz-body-size);
            opacity: 0.84;
            line-height: var(--evenz-body-line);
            margin: 0 0 var(--evenz-space-3) 0;
        }
        .evenz-note {
            padding: var(--evenz-space-2);
            border-radius: 18px;
            background: var(--evenz-panel);
            border: 1px solid rgba(255,255,255,.09);
        }
        .evenz-step {
            font-size: .84rem;
            letter-spacing: .08em;
            text-transform: uppercase;
            opacity: .6;
            margin-bottom: var(--evenz-space-2);
        }
        .evenz-summary {
            padding: var(--evenz-space-2);
            border-radius: 22px;
            background: var(--evenz-panel);
            border: 1px solid rgba(255,255,255,.10);
            margin-bottom: var(--evenz-space-2);
        }
        .stButton > button,
        .stDownloadButton > button {
            min-height: 4.25rem;
            border-radius: 22px;
            border: 1px solid var(--evenz-border);
            background: var(--evenz-panel);
            color: var(--evenz-fg);
            font-size: 1.02rem;
            font-weight: 500;
            line-height: 1.2;
            margin-top: var(--evenz-space-3);
            padding: 0 var(--evenz-space-2);
        }
        .stButton > button:hover {
            border-color: var(--evenz-border-strong);
            background: var(--evenz-panel-strong);
        }
        .stButton > button[kind="primary"] {
            width: 100%;
            min-width: 100%;
            border-radius: 22px;
            padding: 0 var(--evenz-space-2);
            background: var(--evenz-panel);
            border: 1px solid var(--evenz-border);
        }
        [data-testid="stPills"] [data-baseweb="button-group"],
        [data-testid="stSegmentedControl"] [data-baseweb="button-group"] {
            gap: var(--evenz-space-2) !important;
        }
        [data-testid="stPills"] button {
            min-height: 4.35rem !important;
            padding: 0.9rem 1.2rem !important;
            border-radius: 2rem !important;
            justify-content: center !important;
            text-align: center !important;
            background: rgba(14, 19, 28, 0.92) !important;
            border: 1px solid rgba(255, 255, 255, 0.16) !important;
        }
        [data-testid="stPills"] button p,
        [data-testid="stPills"] button span,
        [data-testid="stPills"] button div {
            font-size: 1.14rem !important;
            line-height: 1.24 !important;
            letter-spacing: -0.015em !important;
            white-space: normal !important;
        }
        [data-testid="stPills"] button[aria-pressed="true"] {
            background: var(--evenz-accent-soft) !important;
            border-color: var(--evenz-accent) !important;
            box-shadow: inset 0 0 0 1px rgba(255, 86, 92, 0.12);
        }
        [data-testid="stPills"] button[aria-pressed="true"] p,
        [data-testid="stPills"] button[aria-pressed="true"] span,
        [data-testid="stPills"] button[aria-pressed="true"] div {
            color: var(--evenz-accent) !important;
        }
        [data-testid="stSegmentedControl"] button {
            min-height: 3.75rem !important;
            padding: 0.9rem 1.15rem !important;
            border-radius: 1.3rem !important;
            background: rgba(18, 23, 32, 0.92) !important;
            border: 1px solid rgba(255, 255, 255, 0.14) !important;
        }
        [data-testid="stSegmentedControl"] button p,
        [data-testid="stSegmentedControl"] button span,
        [data-testid="stSegmentedControl"] button div {
            font-size: 1.06rem !important;
            line-height: 1.25 !important;
            letter-spacing: -0.01em !important;
        }
        .stTextInput input, .stTextArea textarea, .stDateInput input, .stTimeInput input {
            min-height: 3.6rem;
            background: rgba(255,255,255,.05) !important;
            color: var(--evenz-fg) !important;
            border-radius: 18px !important;
            padding: 0.8rem 1rem !important;
        }
        .stCheckbox label, .stRadio label, .stSelectbox label {
            color: var(--evenz-fg) !important;
        }
        [data-testid="stExpander"] {
            margin-top: var(--evenz-space-3);
        }
        [data-testid="stExpander"] details {
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.12);
            background: rgba(255,255,255,.04);
            padding: 0.25rem 0.25rem 0.5rem;
        }
        [data-testid="stCaptionContainer"] {
            margin-top: var(--evenz-space-1);
        }
        @media (max-width: 640px) {
            .block-container {
                padding: var(--evenz-space-3) var(--evenz-space-2) var(--evenz-space-5);
            }
            h1 {
                font-size: clamp(2.75rem, 13vw, 4.4rem);
                margin-bottom: var(--evenz-space-2);
            }
            .evenz-step {
                margin-bottom: var(--evenz-space-1);
            }
            [data-testid="stPills"] [data-baseweb="button-group"],
            [data-testid="stSegmentedControl"] [data-baseweb="button-group"] {
                gap: var(--evenz-space-1) !important;
            }
            [data-testid="stPills"] button {
                min-height: 4rem !important;
                padding: 0.8rem 1rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def soft_header(title: str, body: str, step: str = "") -> None:
    if step:
        st.markdown(f'<div class="evenz-step">{step}</div>', unsafe_allow_html=True)
    st.title(title)
    if body:
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


def rhythm_gap(multiplier: float = 1.0) -> None:
    height_rem = 1.25 * max(multiplier, 0)
    st.markdown(f"<div style='height:{height_rem:.3f}rem'></div>", unsafe_allow_html=True)


def editorial_paragraph(text: str) -> None:
    st.markdown(
        f"<div class='evenz-soft' style='width:100%; margin-bottom:1.25rem;'>{text}</div>",
        unsafe_allow_html=True,
    )


def gesture_cloud(text: str) -> None:
    st.markdown(
        f"""
        <div
            class="evenz-soft"
            style="
                width: 100%;
                opacity: .72;
                line-height: 1.78;
                font-size: .98rem;
                letter-spacing: -0.01em;
                margin-bottom: 1.35rem;
            "
        >
            {text}
        </div>
        """,
        unsafe_allow_html=True,
    )
