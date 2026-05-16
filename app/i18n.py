from __future__ import annotations

import gettext
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import streamlit as st


DOMAIN = "messages"
DEFAULT_LOCALE = "fr"
PARTICIPANT_LANGUAGES: List[Tuple[str, str]] = [
    ("fr", "🇫🇷 Français"),
    ("en", "🇬🇧 English"),
    ("it", "🇮🇹 Italiano"),
]


def N_(text: str) -> str:
    return text


def locales_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "locales"


def _normalise_language(language: str) -> str:
    value = str(language or DEFAULT_LOCALE).strip().replace("-", "_")
    if not value:
        return DEFAULT_LOCALE
    short = value.split("_", 1)[0].lower()
    supported = {item[0] for item in PARTICIPANT_LANGUAGES}
    return short if short in supported else DEFAULT_LOCALE


def pot_file_path() -> Path:
    root = locales_dir()
    preferred = root / f"{DOMAIN}.pot"
    legacy = root / "evenz-i18n.pot"
    if preferred.exists():
        return preferred
    return legacy


def available_languages() -> List[str]:
    root = locales_dir()
    languages = ["en"]
    if not root.exists():
        return languages
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        mo_file = child / "LC_MESSAGES" / f"{DOMAIN}.mo"
        po_file = child / "LC_MESSAGES" / f"{DOMAIN}.po"
        if mo_file.exists() or po_file.exists():
            languages.append(child.name)
    seen: List[str] = []
    for language in languages:
        if language not in seen:
            seen.append(language)
    return seen


def translation_info(language: str) -> Dict[str, str | bool]:
    language = _normalise_language(language)
    root = locales_dir()
    mo_file = root / language / "LC_MESSAGES" / f"{DOMAIN}.mo"
    po_file = root / language / "LC_MESSAGES" / f"{DOMAIN}.po"
    pot_file = pot_file_path()
    return {
        "language": language,
        "domain": DOMAIN,
        "localedir": str(root),
        "mo_exists": mo_file.exists(),
        "po_exists": po_file.exists(),
        "mo_path": str(mo_file),
        "po_path": str(po_file),
        "pot_exists": pot_file.exists(),
        "pot_path": str(pot_file),
    }


def setup_translation(language: str) -> Callable[[str], str]:
    language = _normalise_language(language)
    if language == "en":
        # English is the source language in code. Loading an en catalog is
        # unnecessary and can mask drift if that file contains stale translations.
        return gettext.NullTranslations().gettext
    mo_file = locales_dir() / language / "LC_MESSAGES" / f"{DOMAIN}.mo"
    if mo_file.exists():
        with mo_file.open("rb") as handle:
            translator = gettext.GNUTranslations(handle)
        return translator.gettext
    return gettext.NullTranslations().gettext


def set_locale(language: str) -> str:
    normalised = _normalise_language(language)
    st.session_state["evenz_active_locale"] = normalised
    return normalised


def get_locale() -> str:
    language = str(st.session_state.get("evenz_active_locale", DEFAULT_LOCALE))
    return _normalise_language(language)


def get_translator() -> Callable[[str], str]:
    return setup_translation(get_locale())
