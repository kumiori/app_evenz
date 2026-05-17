from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import streamlit as st
from app.components import (
    inject_evenz_styles,
    native_single_segmented,
    soft_header,
    summary_block,
)
from app.flow import get_draft, init_participant_state, update_draft
from app.i18n import PARTICIPANT_LANGUAGES, get_translator, set_locale
from app.key_codec import key_to_emoji_suffix, normalize_access_key, split_emoji_symbols
from app.config import load_settings
from app.notion_client import init_repo


@st.cache_resource(show_spinner=False)
def get_repo():
    return init_repo(load_settings())


def _inject_login_key_styles() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stTextInput"] {
            margin-bottom: 0.4rem !important;
        }
        [data-testid="stTextInput"] > div,
        [data-testid="stTextInput"] > div > div,
        [data-baseweb="base-input"],
        [data-baseweb="input"] {
            min-height: 6.5rem !important;
            height: 6.5rem !important;
            display: flex !important;
            align-items: center !important;
            background: rgba(226, 228, 235, 0.18) !important;
            border-radius: 22px !important;
            overflow: hidden !important;
        }
        [data-baseweb="input"] input,
        [data-baseweb="base-input"] input,
        [data-testid="stTextInput"] input[data-testid="stTextInputField"] {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif !important;
            font-size: 2.4rem !important;
            line-height: 1.35 !important;
            min-height: 100% !important;
            height: 100% !important;
            letter-spacing: 0.04em !important;
            text-align: center !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            overflow: visible !important;
            background: transparent !important;
        }
        @media (max-width: 640px) {
            [data-testid="stTextInput"] > div,
            [data-testid="stTextInput"] > div > div,
            [data-baseweb="base-input"],
            [data-baseweb="input"] {
                min-height: 5.6rem !important;
                height: 5.6rem !important;
            }
            [data-baseweb="input"] input,
            [data-baseweb="base-input"] input,
            [data-testid="stTextInput"] input[data-testid="stTextInputField"] {
                font-size: 2rem !important;
                line-height: 1.3 !important;
                letter-spacing: 0.03em !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _short_emoji_from_access_key(raw_key: str) -> str:
    try:
        return key_to_emoji_suffix(raw_key, 4)
    except ValueError:
        return ""


def _find_players_by_emoji_suffix(
    repo, emoji_suffix: str, length: int
) -> List[Dict[str, str]]:
    matches: List[Dict[str, str]] = []
    for player in repo.list_players(limit=500):
        access_key = str(player.get("access_key") or "")
        if not access_key:
            continue
        try:
            suffix = key_to_emoji_suffix(access_key, length)
        except ValueError:
            continue
        if suffix == emoji_suffix:
            matches.append(player)
    return matches


def _resolve_player_from_login_input(
    repo, raw_input: str
) -> Tuple[Optional[Dict[str, str]], str]:
    candidate = str(raw_input or "").strip()
    if not candidate:
        return None, _("Please enter an access key.")

    try:
        canonical = normalize_access_key(candidate)
    except ValueError:
        canonical = ""

    if canonical:
        player = repo.get_player_by_access_key(canonical)
        if player:
            return player, ""
        return None, _("I could not find a helper with that key.")

    symbols = split_emoji_symbols(candidate)
    if not symbols:
        return None, _("Access key format not recognised.")
    if len(symbols) < 4:
        return None, _("Add at least four emoji symbols to continue.")

    suffix4 = "".join(symbols[-4:])
    matches = _find_players_by_emoji_suffix(repo, suffix4, 4)
    if len(matches) == 1:
        return matches[0], ""
    if len(matches) > 1 and len(symbols) < 6:
        return None, _("Multiple matches. Add two more emojis.")
    if len(symbols) >= 6:
        suffix6 = "".join(symbols[-6:])
        matches = _find_players_by_emoji_suffix(repo, suffix6, 6)
        if len(matches) == 1:
            return matches[0], ""
    return None, _("Key invalid or ambiguous. Try the full emoji key or the ASCII access key.")


def _prefill_login_input(draft: Dict[str, str]) -> None:
    prefill = (
        str(st.session_state.get("evenz_login_short_emoji_prefill") or "").strip()
        or _short_emoji_from_access_key(str(draft.get("access_key") or ""))
    )
    if prefill and not str(st.session_state.get("evenz_login_short_emoji") or "").strip():
        st.session_state["evenz_login_short_emoji"] = prefill


def _store_authenticated_player(
    player: Dict[str, str], selected_locale: str
) -> None:
    access_key = str(player.get("access_key") or "")
    st.session_state["evenz_login_access_key"] = access_key
    st.session_state["evenz_authenticated_access_key"] = access_key
    st.session_state["evenz_login_short_emoji_prefill"] = _short_emoji_from_access_key(
        access_key
    )
    update_draft(
        locale=selected_locale,
        access_key=access_key,
        name=str(player.get("display_name") or player.get("name") or ""),
        existing_player_id=str(player.get("id") or ""),
        hydrated_from_query=False,
    )


def _disconnect(selected_locale: str) -> None:
    st.session_state.pop("evenz_login_access_key", None)
    st.session_state.pop("evenz_authenticated_access_key", None)
    st.session_state.pop("evenz_login_short_emoji_prefill", None)
    st.session_state.pop("evenz_login_short_emoji", None)
    update_draft(
        locale=selected_locale,
        access_key="",
        existing_player_id="",
        hydrated_from_query=False,
    )


def main() -> None:
    st.set_page_config(
        page_title="Login",
        page_icon="🔑",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    inject_evenz_styles()
    _inject_login_key_styles()
    init_participant_state()
    draft = get_draft()

    preview_locale = str(st.session_state.get("evenz_login_locale_choice", draft.get("locale") or "fr"))
    set_locale(preview_locale)
    _ = get_translator()

    soft_header("Evenz", _("Return with your four emojis."), step="login")
    selected_locale = native_single_segmented(
        "",
        PARTICIPANT_LANGUAGES,
        "evenz_login_locale_choice",
        default=str(draft.get("locale") or "fr"),
    )
    if selected_locale != draft.get("locale"):
        update_draft(locale=selected_locale)
        draft = get_draft()
    set_locale(selected_locale)
    _ = get_translator()

    repo = get_repo()
    if not repo.is_ready():
        st.error(repo.unavailable_reason or _("Evenz is not configured."))
        return

    if st.session_state.get("evenz_authenticated_access_key") and draft.get(
        "existing_player_id"
    ):
        soft_header(_("Login"), _("You are already connected."), step="1 / 1")
        summary_block(
            _("Welcome"),
            _("Welcome, {name}.").format(
                name=str(draft.get("name") or "").strip() or _("friend")
            ),
        )
        if st.button(_("Disconnect"), use_container_width=True):
            _disconnect(selected_locale)
            st.rerun()
        return

    _prefill_login_input(draft)

    soft_header(
        _("Login"), _("Paste your emoji key or full access key."), step="1 / 1"
    )
    key_input = st.text_input(
        _("Emoji or access key"),
        key="evenz_login_short_emoji",
        placeholder="🪐🎈🟨⚡  or  59D4…",
    ).strip()

    summary_block(
        _("Need"),
        _("You can enter four emojis, six emojis, the full emoji string, or the full ASCII access key."),
    )

    if st.button(_("Enter"), use_container_width=True):
        player, error_message = _resolve_player_from_login_input(repo, key_input)
        if not player:
            st.error(error_message)
            return
        _store_authenticated_player(player, selected_locale)
        target = str(st.session_state.pop("evenz_post_login_target", "pages/05_library.py"))
        st.switch_page(target)


if __name__ == "__main__":
    main()
