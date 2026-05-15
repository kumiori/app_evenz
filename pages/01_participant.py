from __future__ import annotations

import datetime as dt
from typing import Dict, List

import streamlit as st

from app.components import card_grid, chapter_grid, inject_evenz_styles, soft_header
from app.config import load_settings
from app.copy import (
    AVAILABILITY_PROMPT,
    CAPACITY_PROMPT,
    CHAPTER_PROMPT,
    CONFIRMATION_TITLE,
    IDENTITY_PROMPT,
    NOTES_PROMPT,
    WELCOME_BODY,
    WELCOME_TITLE,
)
from app.flow import followup_selection, init_participant_state, set_followup_selection
from app.key_codec import generate_hex_key, normalize_access_key
from app.notion_client import init_repo


@st.cache_resource(show_spinner=False)
def get_repo():
    return init_repo(load_settings())


def _combine_date_and_time(date_value: dt.date, time_value: dt.time) -> str:
    return dt.datetime.combine(date_value, time_value).isoformat()


def main() -> None:
    st.set_page_config(page_title="Participant", page_icon="🌿", layout="centered")
    inject_evenz_styles()
    init_participant_state()

    repo = get_repo()
    settings = load_settings()
    if not repo.is_ready():
        st.error(repo.unavailable_reason or "Evenz is not configured.")
        return

    event = repo.get_current_event()
    if not event:
        st.error("No active event found.")
        return

    chapters = repo.list_chapters(event["id"])
    questions = repo.list_questions(event["id"])
    followups = repo.list_questions(event["id"], kind="followup")
    question_by_kind = {question["kind"]: question for question in questions}
    followup_by_chapter_id = {
        question["chapter_ids"][0]: question for question in followups if question["chapter_ids"]
    }
    chapter_by_slug = {chapter["slug"]: chapter for chapter in chapters}

    query_key = str(st.query_params.get("key", "")).strip()
    if query_key and not st.session_state.get("evenz_existing_access_key"):
        st.session_state["evenz_existing_access_key"] = query_key

    soft_header(WELCOME_TITLE, WELCOME_BODY)

    st.subheader(IDENTITY_PROMPT)
    st.text_input("Name or nickname", key="evenz_name")
    st.text_input("Emoji signature, optional", key="evenz_emoji_signature")
    st.text_input("Access key, optional", key="evenz_existing_access_key")

    if st.button("Enter", use_container_width=True):
        existing_key = str(st.session_state.get("evenz_existing_access_key", "")).strip()
        if existing_key:
            try:
                canonical = normalize_access_key(existing_key)
            except ValueError as error:
                st.error(str(error))
                st.stop()
            player = repo.get_player_by_access_key(canonical)
            if not player:
                st.error("This access key was not found.")
                st.stop()
            st.session_state["evenz_player_id"] = player["id"]
            st.session_state["evenz_access_key"] = canonical
            st.session_state["evenz_name"] = player.get("display_name", "") or st.session_state["evenz_name"]
            repo.log_event(
                title=f"Login · {st.session_state['evenz_name'] or 'participant'}",
                event_id=event["id"],
                actor_id=player["id"],
                action_type="login",
                target_type="player",
                target_id=player["id"],
                summary="Participant logged in with an existing key.",
                payload={"source": "participant_flow"},
            )
        else:
            if not st.session_state.get("evenz_name"):
                st.error("Give at least a name or nickname.")
                st.stop()
            access_key = generate_hex_key()
            player = repo.create_or_update_player(
                access_key=access_key,
                display_name=st.session_state["evenz_name"],
                emoji_signature=st.session_state.get("evenz_emoji_signature", ""),
                anonymous_name=st.session_state["evenz_name"],
                role=["helper"],
            )
            st.session_state["evenz_player_id"] = player["id"]
            st.session_state["evenz_access_key"] = access_key
            repo.log_event(
                title=f"Create key · {st.session_state['evenz_name']}",
                event_id=event["id"],
                actor_id=player["id"],
                action_type="create_key",
                target_type="player",
                target_id=player["id"],
                summary="Participant minted a new key.",
                payload={"source": "participant_flow"},
            )

    if not st.session_state.get("evenz_player_id"):
        return

    st.caption(f"Your access key: `{st.session_state.get('evenz_access_key', '')}`")

    st.subheader(CHAPTER_PROMPT)
    st.caption("Choose one or more chapters.")
    chapter_grid(chapters, "evenz_chapters")

    with st.expander("Rank preferences, optional"):
        options = [""] + [chapter["slug"] for chapter in chapters]
        st.selectbox("First choice", options, key="evenz_rank_1")
        st.selectbox("Second choice", options, key="evenz_rank_2")

    st.subheader(AVAILABILITY_PROMPT)
    availability_options = question_by_kind["availability"]["choice_options"]
    card_grid(availability_options, "evenz_availability", columns=2)
    with st.expander("Add a precise slot, optional"):
        use_precise_slot = st.checkbox("Add a precise slot")
        if use_precise_slot:
            start_date = st.date_input("Start date", value=dt.date.today())
            start_time = st.time_input("Start time", value=dt.time(hour=14, minute=0))
            end_date = st.date_input("End date", value=dt.date.today())
            end_time = st.time_input("End time", value=dt.time(hour=16, minute=0))
            st.session_state["evenz_exact_start"] = _combine_date_and_time(start_date, start_time)
            st.session_state["evenz_exact_end"] = _combine_date_and_time(end_date, end_time)

    st.subheader(CAPACITY_PROMPT)
    capacity_options = question_by_kind["capacity_offer"]["choice_options"]
    card_grid(capacity_options, "evenz_capacities", columns=2)

    st.subheader(NOTES_PROMPT)
    st.text_area("A detail, a constraint, a desire", key="evenz_notes", label_visibility="collapsed")

    selected_slugs: List[str] = list(st.session_state.get("evenz_chapters", []))
    for slug in selected_slugs:
        chapter = chapter_by_slug.get(slug)
        if not chapter:
            continue
        followup = followup_by_chapter_id.get(chapter["id"])
        if not followup:
            continue
        with st.expander(f'{chapter["emoji"]} {chapter["name"]} follow-up, optional'):
            current = followup_selection(slug)
            options = [{"value": value, "label": value.replace("_", " ").title()} for value in followup["choice_options"]]
            st.session_state[f"followup-{slug}"] = current
            chosen = card_grid(options, f"followup-{slug}", columns=2)
            set_followup_selection(slug, chosen)

    if st.button("Save my signals", use_container_width=True):
        if not selected_slugs:
            st.error("Choose at least one chapter.")
            st.stop()
        availability = list(st.session_state.get("evenz_availability", []))
        if not availability:
            st.error("Choose at least one availability bucket.")
            st.stop()

        player = repo.create_or_update_player(
            access_key=st.session_state["evenz_access_key"],
            display_name=st.session_state["evenz_name"] or "Anonymous",
            emoji_signature=st.session_state.get("evenz_emoji_signature", ""),
            anonymous_name=st.session_state["evenz_name"] or "Anonymous",
            role=["helper"],
            capacities=list(st.session_state.get("evenz_capacities", [])),
            notes_private=st.session_state.get("evenz_notes", ""),
        )
        st.session_state["evenz_player_id"] = player["id"]

        for slug in selected_slugs:
            chapter = chapter_by_slug[slug]
            repo.create_response(
                title=f'Interest · {chapter["name"]} · {st.session_state["evenz_name"]}',
                player_id=player["id"],
                event_id=event["id"],
                chapter_id=chapter["id"],
                question_id=question_by_kind["chapter_interest"]["id"],
                response_type="interest",
                payload_text_value=f'Interested in {chapter["name"]}',
                payload_json_value={
                    "chapter_slug": slug,
                    "chapter_name": chapter["name"],
                    "rank_1": st.session_state.get("evenz_rank_1", ""),
                    "rank_2": st.session_state.get("evenz_rank_2", ""),
                },
                visibility_value="host",
                signal_strength="high",
            )

        repo.create_response(
            title=f'Availability · {st.session_state["evenz_name"]}',
            player_id=player["id"],
            event_id=event["id"],
            question_id=question_by_kind["availability"]["id"],
            response_type="availability",
            payload_text_value=", ".join(availability),
            payload_json_value={"availability": availability},
            availability=availability,
            exact_start=st.session_state.get("evenz_exact_start"),
            exact_end=st.session_state.get("evenz_exact_end"),
            visibility_value="host",
        )

        capacities = list(st.session_state.get("evenz_capacities", []))
        if capacities:
            repo.create_response(
                title=f'Capacity · {st.session_state["evenz_name"]}',
                player_id=player["id"],
                event_id=event["id"],
                question_id=question_by_kind["capacity_offer"]["id"],
                response_type="capacity",
                payload_text_value=", ".join(capacities),
                payload_json_value={"capacities": capacities},
                visibility_value="host",
            )

        if st.session_state.get("evenz_notes", "").strip():
            repo.create_response(
                title=f'Note · {st.session_state["evenz_name"]}',
                player_id=player["id"],
                event_id=event["id"],
                question_id=question_by_kind["notes"]["id"],
                response_type="note",
                payload_text_value=st.session_state["evenz_notes"],
                payload_json_value={"notes": st.session_state["evenz_notes"]},
                visibility_value="private",
                signal_strength="low",
            )

        for slug, values in st.session_state.get("evenz_followups", {}).items():
            if not values:
                continue
            chapter = chapter_by_slug.get(slug)
            if not chapter:
                continue
            followup = followup_by_chapter_id.get(chapter["id"])
            if not followup:
                continue
            repo.create_response(
                title=f'Follow-up · {chapter["name"]} · {st.session_state["evenz_name"]}',
                player_id=player["id"],
                event_id=event["id"],
                chapter_id=chapter["id"],
                question_id=followup["id"],
                response_type="followup",
                payload_text_value=", ".join(values),
                payload_json_value={"chapter_slug": slug, "followup": values},
                visibility_value="host",
            )

        repo.log_event(
            title=f'Submit availability · {st.session_state["evenz_name"]}',
            event_id=event["id"],
            actor_id=player["id"],
            action_type="submit_availability",
            target_type="response",
            target_id=player["id"],
            summary="Participant submitted their chapter and availability signals.",
            payload={"chapters": selected_slugs, "availability": availability},
        )
        st.session_state["evenz_saved"] = True

    if st.session_state.get("evenz_saved"):
        st.subheader(CONFIRMATION_TITLE)
        pretty_chapters = [chapter_by_slug[slug]["name"] for slug in selected_slugs if slug in chapter_by_slug]
        availability = list(st.session_state.get("evenz_availability", []))
        st.success(
            f"You marked: {', '.join(pretty_chapters)}. Best fit for now: {', '.join(availability)}."
        )
        st.caption("I'll gather the signals and suggest a moment.")


if __name__ == "__main__":
    main()
