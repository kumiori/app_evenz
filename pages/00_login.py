from __future__ import annotations

from typing import Dict, List, Optional

import streamlit as st

from app.components import inject_evenz_styles, native_single_segmented, soft_header, summary_block
from app.flow import get_draft, init_participant_state, update_draft
from app.i18n import PARTICIPANT_LANGUAGES, get_translator, set_locale
from app.key_codec import hex_to_emoji, split_emoji_symbols
from app.notion_client import init_repo
from app.config import load_settings


@st.cache_resource(show_spinner=False)
def get_repo():
    return init_repo(load_settings())


def _find_player_by_short_emoji(repo, short_emoji: str) -> Optional[Dict[str, str]]:
    matches: List[Dict[str, str]] = []
    for player in repo.list_players(limit=500):
        access_key = str(player.get("access_key") or "")
        if not access_key:
            continue
        emoji_key = hex_to_emoji(access_key)
        suffix = "".join(split_emoji_symbols(emoji_key)[-4:])
        if suffix == short_emoji:
            matches.append(player)
    if len(matches) == 1:
        return matches[0]
    return None


def main() -> None:
    st.set_page_config(
        page_title="Login",
        page_icon="🔑",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    inject_evenz_styles()
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

    soft_header(_("Login"), _("Paste the four-emoji helper key you stored earlier."), step="1 / 1")
    short_emoji = st.text_input(
        _("Four-emoji key"),
        key="evenz_login_short_emoji",
        placeholder="🪐🎈🟨⚡",
    ).strip()

    summary_block(
        _("Need"),
        _("Enter exactly the last four emoji symbols from your helper key screenshot."),
    )

    if st.button(_("Enter"), use_container_width=True):
        symbols = split_emoji_symbols(short_emoji)
        if len(symbols) != 4:
            st.error(_("Please enter exactly four emojis."))
            return
        player = _find_player_by_short_emoji(repo, "".join(symbols))
        if not player:
            st.error(_("I could not find a helper with that short key."))
            return
        access_key = str(player.get("access_key") or "")
        st.session_state["evenz_login_access_key"] = access_key
        update_draft(
            locale=selected_locale,
            access_key=access_key,
            name=str(player.get("display_name") or player.get("name") or ""),
            existing_player_id=str(player.get("id") or ""),
            hydrated_from_query=False,
        )
        st.switch_page("pages/01_participant.py")


if __name__ == "__main__":
    main()
