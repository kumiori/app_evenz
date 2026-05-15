from __future__ import annotations

import gettext
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import streamlit as st


DOMAIN = "evenz-i18n"
DEFAULT_LOCALE = "fr"
PARTICIPANT_LANGUAGES: List[Tuple[str, str]] = [
    ("fr", "🇫🇷 Français"),
    ("en", "🇬🇧 English"),
    ("it", "🇮🇹 Italiano"),
]


def locales_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "locales"


def available_languages() -> List[str]:
    root = locales_dir()
    languages = ["en"]
    if not root.exists():
        return languages
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        mo_file = child / "LC_MESSAGES" / f"{DOMAIN}.mo"
        if mo_file.exists():
            languages.append(child.name)
    seen: List[str] = []
    for language in languages:
        if language not in seen:
            seen.append(language)
    return seen


def translation_info(language: str) -> Dict[str, str | bool]:
    root = locales_dir()
    mo_file = root / language / "LC_MESSAGES" / f"{DOMAIN}.mo"
    po_file = root / language / "LC_MESSAGES" / f"{DOMAIN}.po"
    return {
        "language": language,
        "domain": DOMAIN,
        "localedir": str(root),
        "mo_exists": mo_file.exists(),
        "po_exists": po_file.exists(),
        "mo_path": str(mo_file),
        "po_path": str(po_file),
    }


def setup_translation(language: str) -> Callable[[str], str]:
    translator = gettext.translation(
        DOMAIN,
        localedir=str(locales_dir()),
        languages=[language],
        fallback=True,
    )
    return translator.gettext


def set_locale(language: str) -> str:
    st.session_state["evenz_active_locale"] = language
    return language


def get_locale() -> str:
    language = str(st.session_state.get("evenz_active_locale", DEFAULT_LOCALE))
    if language not in [item[0] for item in PARTICIPANT_LANGUAGES]:
        return DEFAULT_LOCALE
    return language


def get_translator() -> Callable[[str], str]:
    return setup_translation(get_locale())
