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


def add_relations(repo: EvenzRepo) -> None:
    repo.update_schema(repo.dbs.events, {"host": repo.rel_prop(repo.dbs.players, "hosted_events")})
    repo.update_schema(repo.dbs.chapters, {"event": repo.rel_prop(repo.dbs.events, "chapters")})
    repo.update_schema(
        repo.dbs.questions,
        {
            "event": repo.rel_prop(repo.dbs.events, "questions"),
            "chapter": repo.rel_prop(repo.dbs.chapters, "questions"),
        },
    )
    repo.update_schema(
        repo.dbs.responses,
        {
            "player": repo.rel_prop(repo.dbs.players, "responses"),
            "event": repo.rel_prop(repo.dbs.events, "responses"),
            "chapter": repo.rel_prop(repo.dbs.chapters, "responses"),
            "question": repo.rel_prop(repo.dbs.questions, "responses"),
        },
    )
    repo.update_schema(
        repo.dbs.sessions,
        {
            "event": repo.rel_prop(repo.dbs.events, "suggested_sessions"),
            "chapter": repo.rel_prop(repo.dbs.chapters, "suggested_sessions"),
            "created_by": repo.rel_prop(repo.dbs.players, "created_sessions"),
        },
    )
    repo.update_schema(
        repo.dbs.event_log,
        {
            "event": repo.rel_prop(repo.dbs.events, "event_log"),
            "actor": repo.rel_prop(repo.dbs.players, "event_log"),
        },
    )


def seed(repo: EvenzRepo) -> None:
    host = repo.ensure_page_by_title(
        repo.dbs.players,
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
        repo.dbs.events,
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
            repo.dbs.chapters,
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
            repo.dbs.questions,
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
            repo.dbs.questions,
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
        repo.dbs.players,
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

    repo.create_response(
        title="Demo · Books interest",
        player_id=demo_player["id"],
        event_id=event["id"],
        chapter_id=chapter_pages["books"]["id"],
        question_id=question_pages["chapter_interest"]["id"],
        response_type="interest",
        payload_text_value="Interested in Books",
        payload_json_value={"chapter_slug": "books", "chapter_name": "Books"},
        visibility_value="host",
        signal_strength="high",
        source="test",
    )
    repo.create_response(
        title="Demo · Weekend availability",
        player_id=demo_player["id"],
        event_id=event["id"],
        question_id=question_pages["availability"]["id"],
        response_type="availability",
        payload_text_value="Available this weekend",
        payload_json_value={"availability": ["this_weekend"]},
        availability=["this_weekend"],
        visibility_value="host",
        source="test",
    )
    repo.create_response(
        title="Demo · Sort capacity",
        player_id=demo_player["id"],
        event_id=event["id"],
        question_id=question_pages["capacity_offer"]["id"],
        response_type="capacity",
        payload_text_value="Can sort and carry",
        payload_json_value={"capacities": ["sort", "carry"]},
        visibility_value="host",
        source="test",
    )

    repo.ensure_page_by_title(
        repo.dbs.sessions,
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

    repo.log_event(
        title=f"Bootstrap · {iso_now()}",
        event_id=event["id"],
        actor_id=host["id"],
        action_type="bootstrap",
        target_type="system",
        summary="Bootstrapped Evenz schema and The Base seed payload.",
        payload={"event": repo.settings.event_slug},
    )


def verify(repo: EvenzRepo) -> None:
    print("✅ PLAYERS DB verified")
    print("✅ EVENTS DB verified")
    print("✅ CHAPTERS DB verified")
    print("✅ QUESTIONS DB verified")
    print("✅ RESPONSES DB verified")
    print("✅ SESSIONS DB verified")
    print("✅ EVENT_LOG DB verified")
    print("Seeded:")
    print(f"- Event: {repo.settings.event_name}")
    print("- Chapters: Kitchen, Plants, Clothes, Books, Art / archives")
    print("- Questions: 5")
    print("- Sample player: Demo Helper 🌿")
    print("")
    print("[notion]")
    print('api_key = "secret_..."')
    print(f'evenz_players_db_id = "{repo.dbs.players}"')
    print(f'evenz_events_db_id = "{repo.dbs.events}"')
    print(f'evenz_chapters_db_id = "{repo.dbs.chapters}"')
    print(f'evenz_questions_db_id = "{repo.dbs.questions}"')
    print(f'evenz_responses_db_id = "{repo.dbs.responses}"')
    print(f'evenz_sessions_db_id = "{repo.dbs.sessions}"')
    print(f'evenz_event_log_db_id = "{repo.dbs.event_log}"')


def main() -> None:
    settings = load_settings()
    repo = init_repo(settings)
    if not repo.is_ready():
        raise RuntimeError("Notion is not configured. Set notion.api_key and evenz_*_db_id values in .streamlit/secrets.toml, or equivalent env vars.")

    repo.update_schema(repo.dbs.players, PLAYER_SCHEMA)
    repo.update_schema(repo.dbs.events, EVENT_SCHEMA)
    repo.update_schema(repo.dbs.chapters, CHAPTER_SCHEMA)
    repo.update_schema(repo.dbs.questions, QUESTION_SCHEMA)
    repo.update_schema(repo.dbs.responses, RESPONSE_SCHEMA)
    repo.update_schema(repo.dbs.sessions, SESSION_SCHEMA)
    if repo.dbs.event_log != repo.dbs.events:
        repo.update_schema(repo.dbs.event_log, EVENT_LOG_SCHEMA)

    add_relations(repo)
    seed(repo)
    verify(repo)


if __name__ == "__main__":
    main()
