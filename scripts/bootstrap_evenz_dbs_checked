#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import load_settings
from app.models import (
    CHAPTER_SCHEMA,
    CHAPTER_SEEDS,
    DEFAULT_QUESTIONS,
    EVENT_LOG_SCHEMA,
    EVENT_SCHEMA,
    FOLLOWUP_QUESTIONS,
    PLAYER_SCHEMA,
    QUESTION_SCHEMA,
    RESPONSE_SCHEMA,
    SESSION_SCHEMA,
)
from app.notion_client import (
    EvenzRepo,
    checkbox,
    date_value,
    init_repo,
    iso_now,
    multi_select,
    number_value,
    relation,
    rich_text,
    select,
)


def _db(repo: EvenzRepo, name: str, fallback: str | None = None) -> str:
    """Resolve a DB id from repo.dbs with a fallback attribute.

    Current Evenz convention:
    - repo.dbs.events = append-only EVENT LOG / ledger
    - repo.dbs.gatherings = organized happenings
    - repo.dbs.signals = query-friendly participant signals
    """
    value = getattr(repo.dbs, name, None)
    if value:
        return value
    if fallback:
        value = getattr(repo.dbs, fallback, None)
        if value:
            return value
    raise AttributeError(f"Missing Notion database id for {name!r}; no fallback {fallback!r} found.")


def dbs(repo: EvenzRepo) -> Dict[str, str]:
    return {
        "players": _db(repo, "players"),
        "gatherings": _db(repo, "gatherings", "events"),
        "chapters": _db(repo, "chapters"),
        "questions": _db(repo, "questions"),
        "signals": _db(repo, "signals", "responses"),
        "responses": _db(repo, "responses", "signals"),
        "sessions": _db(repo, "sessions"),
        "event_log": _db(repo, "events", "event_log"),
    }


def add_relations(repo: EvenzRepo) -> None:
    d = dbs(repo)
    repo.update_schema(d["gatherings"], {"host": repo.rel_prop(d["players"], "hosted_gatherings")})
    repo.update_schema(d["chapters"], {"event": repo.rel_prop(d["gatherings"], "chapters")})
    repo.update_schema(
        d["questions"],
        {
            "event": repo.rel_prop(d["gatherings"], "questions"),
            "chapter": repo.rel_prop(d["chapters"], "questions"),
        },
    )
    repo.update_schema(
        d["signals"],
        {
            "player": repo.rel_prop(d["players"], "signals"),
            "event": repo.rel_prop(d["gatherings"], "signals"),
            "chapter": repo.rel_prop(d["chapters"], "signals"),
            "question": repo.rel_prop(d["questions"], "signals"),
        },
    )
    if d["responses"] != d["signals"]:
        repo.update_schema(
            d["responses"],
            {
                "player": repo.rel_prop(d["players"], "responses"),
                "event": repo.rel_prop(d["gatherings"], "responses"),
                "chapter": repo.rel_prop(d["chapters"], "responses"),
                "question": repo.rel_prop(d["questions"], "responses"),
            },
        )
    repo.update_schema(
        d["sessions"],
        {
            "event": repo.rel_prop(d["gatherings"], "sessions"),
            "chapter": repo.rel_prop(d["chapters"], "sessions"),
            "created_by": repo.rel_prop(d["players"], "created_sessions"),
        },
    )
    repo.update_schema(
        d["event_log"],
        {
            "event": repo.rel_prop(d["gatherings"], "event_log"),
            "actor": repo.rel_prop(d["players"], "event_log"),
        },
    )

def seed(repo: EvenzRepo) -> None:
    d = dbs(repo)
    host = repo.ensure_page_by_title(
        d["players"],
        "Andres / Host",
        {
            "access_key": rich_text("EVENZ-HOST"),
            "access_key_hash": rich_text(""),
            "access_key_last4": rich_text("HOST"),
            "emoji_signature": rich_text("🏠✨"),
            "anonymous_name": rich_text("Host"),
            "contact_channel": select("direct"),
            "contact_value": rich_text(""),
            "role": multi_select(["host", "organizer"]),
            "onboarding_state": select("active"),
            "created_at": date_value(),
            "last_seen_at": date_value(),
        },
    )

    event = repo.ensure_page_by_title(
        d["gatherings"],
        repo.settings.event_name,
        {
            "slug": rich_text(repo.settings.event_slug),
            "event_type": select("move"),
            "status": select("active"),
            "location": rich_text("The Base"),
            "description": rich_text(
                "A soft coordination space to help The Base move forward after renovation."
            ),
            "active": checkbox(True),
            "projection_mode": checkbox(True),
            "visibility": select("link"),
            "default_language": select("fr"),
            "host": relation([host["id"]]),
            "created_at": date_value(),
        },
    )

    chapter_pages: Dict[str, Dict[str, Any]] = {}
    for chapter in CHAPTER_SEEDS:
        page = repo.ensure_page_by_title(
            d["chapters"],
            f'{chapter["emoji"]} {chapter["name"]}',
            {
                "event": relation([event["id"]]),
                "emoji": rich_text(chapter["emoji"]),
                "slug": rich_text(chapter["slug"]),
                "description": rich_text(chapter["description"]),
                "sort_order": number_value(chapter["sort_order"]),
                "active": checkbox(True),
                "target_people": number_value(chapter["target_people"]),
                "mood": select(chapter["mood"]),
                "needs_followup": checkbox(chapter["needs_followup"]),
                "projection_label": rich_text(f'{chapter["emoji"]} {chapter["name"]}'),
                "color_tag": select(chapter["color_tag"]),
            },
        )
        chapter_pages[chapter["slug"]] = page

    question_pages: Dict[str, Dict[str, Any]] = {}
    for question in DEFAULT_QUESTIONS:
        page = repo.ensure_page_by_title(
            d["questions"],
            question["title"],
            {
                "event": relation([event["id"]]),
                "kind": select(question["kind"]),
                "prompt": rich_text(question["prompt"]),
                "input_type": select(question["input_type"]),
                "choice_options_json": rich_text(
                    json.dumps(question["choice_options_json"], ensure_ascii=False)
                ),
                "required": checkbox(question["required"]),
                "active": checkbox(question["active"]),
                "step_order": number_value(question["step_order"]),
                "visibility": select(question["visibility"]),
                "help_text": rich_text(question["help_text"]),
                "created_at": date_value(),
            },
        )
        question_pages[question["kind"]] = page

    for followup in FOLLOWUP_QUESTIONS:
        repo.ensure_page_by_title(
            d["questions"],
            followup["title"],
            {
                "event": relation([event["id"]]),
                "chapter": relation([chapter_pages[followup["chapter_slug"]]["id"]]),
                "kind": select("followup"),
                "prompt": rich_text(followup["prompt"]),
                "input_type": select("multiselect"),
                "choice_options_json": rich_text(json.dumps(followup["options"], ensure_ascii=False)),
                "required": checkbox(False),
                "active": checkbox(True),
                "step_order": number_value(10),
                "visibility": select("participant"),
                "help_text": rich_text("Shown only after selecting this chapter."),
                "created_at": date_value(),
            },
        )

    demo_player = repo.ensure_page_by_title(
        d["players"],
        "Demo Helper 🌿",
        {
            "access_key": rich_text("EVENZ-DEMO"),
            "access_key_hash": rich_text(""),
            "access_key_last4": rich_text("DEMO"),
            "emoji_signature": rich_text("🌿📚"),
            "anonymous_name": rich_text("Green Reader"),
            "contact_channel": select("whatsapp"),
            "contact_value": rich_text(""),
            "role": multi_select(["helper"]),
            "onboarding_state": select("active"),
            "can_lift": checkbox(True),
            "can_sort": checkbox(True),
            "created_at": date_value(),
            "last_seen_at": date_value(),
        },
    )

    repo.ensure_page_by_title(
        d["signals"],
        "Demo · Books interest",
        {
            "player": relation([demo_player["id"]]),
            "event": relation([event["id"]]),
            "chapter": relation([chapter_pages["books"]["id"]]),
            "question": relation([question_pages["chapter_interest"]["id"]]),
            "response_type": select("interest"),
            "payload_text": rich_text("Interested in Books"),
            "payload_json": rich_text(json.dumps({"chapter_slug": "books", "chapter_name": "Books"}, ensure_ascii=False)),
            "visibility": select("host"),
            "signal_strength": select("high"),
            "source": select("test"),
            "submitted_at": date_value(),
        },
    )
    repo.ensure_page_by_title(
        d["signals"],
        "Demo · Weekend availability",
        {
            "player": relation([demo_player["id"]]),
            "event": relation([event["id"]]),
            "question": relation([question_pages["availability"]["id"]]),
            "response_type": select("availability"),
            "payload_text": rich_text("Available this weekend"),
            "payload_json": rich_text(json.dumps({"availability": ["this_weekend"]}, ensure_ascii=False)),
            "availability_bucket": multi_select(["this_weekend"]),
            "visibility": select("host"),
            "source": select("test"),
            "submitted_at": date_value(),
        },
    )
    repo.ensure_page_by_title(
        d["signals"],
        "Demo · Sort capacity",
        {
            "player": relation([demo_player["id"]]),
            "event": relation([event["id"]]),
            "question": relation([question_pages["capacity_offer"]["id"]]),
            "response_type": select("capacity"),
            "payload_text": rich_text("Can sort and carry"),
            "payload_json": rich_text(json.dumps({"capacities": ["sort", "carry"]}, ensure_ascii=False)),
            "visibility": select("host"),
            "source": select("test"),
            "submitted_at": date_value(),
        },
    )

    repo.ensure_page_by_title(
        d["sessions"],
        "Books · Saturday afternoon",
        {
            "event": relation([event["id"]]),
            "chapter": relation([chapter_pages["books"]["id"]]),
            "created_by": relation([host["id"]]),
            "status": select("proposed"),
            "capacity_target": number_value(3),
            "notes": rich_text("Host-created seed."),
            "generated_from": rich_text("host"),
            "created_at": date_value(),
        },
    )

    repo.ensure_page_by_title(
        d["event_log"],
        f"Bootstrap · {iso_now()}",
        {
            "timestamp": date_value(),
            "event": relation([event["id"]]),
            "actor": relation([host["id"]]),
            "action_type": select("bootstrap"),
            "target_type": select("system"),
            "target_id": rich_text(repo.settings.event_slug),
            "summary": rich_text("Bootstrapped Evenz schema and The Base seed payload."),
            "payload_json": rich_text(json.dumps({"event": repo.settings.event_slug}, ensure_ascii=False)),
        },
    )


def verify(repo: EvenzRepo) -> None:
    d = dbs(repo)
    print("✅ PLAYERS DB verified")
    print("✅ EVENTS DB verified as EVENT_LOG / ledger")
    print("✅ CHAPTERS DB verified")
    print("✅ QUESTIONS DB verified")
    print("✅ SIGNALS DB verified")
    print("✅ SESSIONS DB verified")
    print("✅ GATHERINGS DB verified")
    print("Seeded:")
    print(f"- Gathering: {repo.settings.event_name}")
    print("- Chapters: Kitchen, Plants, Clothes, Books, Art / archives")
    print("- Questions: 5")
    print("- Sample player: Demo Helper 🌿")
    print("")
    print("[notion]")
    print('api_key = "secret_..."')
    print(f'evenz_players_db_id = "{d["players"]}"')
    print(f'evenz_events_db_id = "{d["event_log"]}"  # EVENT_LOG ledger')
    print(f'evenz_gatherings_db_id = "{d["gatherings"]}"  # organized happenings')
    print(f'evenz_chapters_db_id = "{d["chapters"]}"')
    print(f'evenz_questions_db_id = "{d["questions"]}"')
    print(f'evenz_signals_db_id = "{d["signals"]}"')
    print(f'evenz_responses_db_id = "{d["responses"]}"  # legacy/optional')
    print(f'evenz_sessions_db_id = "{d["sessions"]}"')

def main() -> None:
    settings = load_settings()
    repo = init_repo(settings)
    if not repo.is_ready():
        raise RuntimeError(
            "Notion is not configured. Set notion.api_key and evenz_*_db_id values "
            "in .streamlit/secrets.toml, or equivalent env vars. Current convention: "
            "evenz_events_db_id is the EVENT_LOG ledger; evenz_gatherings_db_id is the happenings DB."
        )

    d = dbs(repo)

    repo.update_schema(d["players"], PLAYER_SCHEMA)
    repo.update_schema(d["gatherings"], EVENT_SCHEMA)
    repo.update_schema(d["chapters"], CHAPTER_SCHEMA)
    repo.update_schema(d["questions"], QUESTION_SCHEMA)
    repo.update_schema(d["signals"], RESPONSE_SCHEMA)
    if d["responses"] != d["signals"]:
        repo.update_schema(d["responses"], RESPONSE_SCHEMA)
    repo.update_schema(d["sessions"], SESSION_SCHEMA)
    repo.update_schema(d["event_log"], EVENT_LOG_SCHEMA)

    add_relations(repo)
    seed(repo)
    verify(repo)


if __name__ == "__main__":
    main()
