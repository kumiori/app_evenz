from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import tomllib


DEFAULT_NOTION_VERSION = "2025-09-03"
DEFAULT_EVENT_NAME = "The Base Moves Forward"
DEFAULT_EVENT_SLUG = "the-base-moves-forward"


@dataclass(frozen=True)
class DatabaseIds:
    players: str
    events: str
    chapters: str
    questions: str
    responses: str
    sessions: str
    event_log: str


@dataclass(frozen=True)
class AppSettings:
    notion_token: str
    notion_version: str
    debug: bool
    event_name: str
    event_slug: str
    dbs: DatabaseIds


DEFAULT_DB_IDS = DatabaseIds(
    players="36154516e9e180a9b30b000c370fcb5e",
    events="36154516e9e180c59402000c5727ed29",
    chapters="36154516e9e180ad880f000c3770d44a",
    questions="36154516e9e1808db93a000cc149f76a",
    responses="36154516e9e180d3b5a9000cb93a9ad8",
    sessions="36154516e9e180899e96000cafc697be",
    event_log="36154516e9e180c59402000c5727ed29",
)


def load_local_secrets() -> Dict[str, Any]:
    candidates = [
        Path.cwd() / ".streamlit" / "secrets.toml",
        Path(__file__).resolve().parents[1] / ".streamlit" / "secrets.toml",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            with path.open("rb") as handle:
                payload = tomllib.load(handle)
            if isinstance(payload, dict):
                return payload
        except Exception:
            return {}
    return {}


def _get_secret(name: str, *aliases: str, default: str = "") -> str:
    secrets = load_local_secrets().get("notion", {})
    if not isinstance(secrets, dict):
        secrets = {}

    env_value = os.getenv(name, "").strip()
    if env_value:
        return env_value

    for alias in aliases:
        env_alias = os.getenv(alias, "").strip()
        if env_alias:
            return env_alias
        secret_value = str(secrets.get(alias.lower(), "") or secrets.get(alias, "")).strip()
        if secret_value:
            return secret_value
    return default


def load_settings() -> AppSettings:
    notion_token = _get_secret("NOTION_TOKEN", "api_key", "token", default="")
    notion_version = _get_secret(
        "NOTION_VERSION",
        "notion_version",
        default=DEFAULT_NOTION_VERSION,
    )
    debug = _get_secret("EVENZ_DEBUG", "evenz_debug", "BASE_DEBUG", "base_debug", default="0") == "1"
    event_name = _get_secret(
        "EVENZ_EVENT_NAME",
        "evenz_event_name",
        "BASE_EVENT_NAME",
        "base_event_name",
        default=DEFAULT_EVENT_NAME,
    )
    event_slug = _get_secret(
        "EVENZ_EVENT_SLUG",
        "evenz_event_slug",
        "BASE_EVENT_SLUG",
        "base_event_slug",
        default=DEFAULT_EVENT_SLUG,
    )

    dbs = DatabaseIds(
        players=_get_secret(
            "EVENZ_PLAYERS_DB_ID",
            "evenz_players_db_id",
            "BASE_PLAYERS_DB_ID",
            "base_players_db_id",
            default=DEFAULT_DB_IDS.players,
        ),
        events=_get_secret(
            "EVENZ_EVENTS_DB_ID",
            "evenz_events_db_id",
            "BASE_EVENTS_DB_ID",
            "base_events_db_id",
            default=DEFAULT_DB_IDS.events,
        ),
        chapters=_get_secret(
            "EVENZ_CHAPTERS_DB_ID",
            "evenz_chapters_db_id",
            "BASE_CHAPTERS_DB_ID",
            "base_chapters_db_id",
            default=DEFAULT_DB_IDS.chapters,
        ),
        questions=_get_secret(
            "EVENZ_QUESTIONS_DB_ID",
            "evenz_questions_db_id",
            "BASE_QUESTIONS_DB_ID",
            "base_questions_db_id",
            default=DEFAULT_DB_IDS.questions,
        ),
        responses=_get_secret(
            "EVENZ_RESPONSES_DB_ID",
            "evenz_responses_db_id",
            "BASE_RESPONSES_DB_ID",
            "base_responses_db_id",
            default=DEFAULT_DB_IDS.responses,
        ),
        sessions=_get_secret(
            "EVENZ_SESSIONS_DB_ID",
            "evenz_sessions_db_id",
            "BASE_SESSIONS_DB_ID",
            "base_sessions_db_id",
            default=DEFAULT_DB_IDS.sessions,
        ),
        event_log=_get_secret(
            "EVENZ_EVENT_LOG_DB_ID",
            "evenz_event_log_db_id",
            "BASE_EVENT_LOG_DB_ID",
            "base_event_log_db_id",
            default=_get_secret(
                "EVENZ_EVENTS_DB_ID",
                "evenz_events_db_id",
                "BASE_EVENTS_DB_ID",
                "base_events_db_id",
                default=DEFAULT_DB_IDS.event_log,
            ),
        ),
    )

    return AppSettings(
        notion_token=notion_token,
        notion_version=notion_version,
        debug=debug,
        event_name=event_name,
        event_slug=event_slug,
        dbs=dbs,
    )
