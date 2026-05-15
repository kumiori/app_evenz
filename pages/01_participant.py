from __future__ import annotations

import datetime as dt
import json
import time
from typing import Dict, List

import streamlit as st

from app.components import (
    inject_evenz_styles,
    native_multiselect_pills,
    native_single_segmented,
    review_line,
    soft_header,
    summary_block,
)
from app.flow import (
    add_exact_slot,
    current_step,
    draft_value,
    get_draft,
    init_participant_state,
    mark_submitted,
    next_step,
    previous_step,
    reset_participant_state,
    set_step,
    update_draft,
)
from app.i18n import PARTICIPANT_LANGUAGES, get_translator, set_locale
from app.key_codec import generate_hex_key, hex_to_emoji, normalize_access_key, split_emoji_symbols
from app.models import AVAILABILITY_OPTIONS, CAPACITY_OPTIONS
from app.notion_client import init_repo
from app.config import load_settings


@st.cache_resource(show_spinner=False)
def get_repo():
    return init_repo(load_settings())


@st.cache_data(show_spinner=False)
def get_event_bundle(event_slug: str) -> Dict[str, object]:
    repo = get_repo()
    event = repo.get_current_event()
    if not event:
        return {"event": None, "questions": [], "chapters": []}
    return {
        "event": event,
        "questions": repo.list_questions(event["id"]),
        "chapters": repo.list_chapters(event["id"]),
    }


def _combine_date_and_time(date_value: dt.date, time_value: dt.time) -> str:
    return dt.datetime.combine(date_value, time_value).isoformat()


def _profile(debug_rows: List[Dict[str, object]], label: str, started_at: float, **extra: object) -> None:
    elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
    row: Dict[str, object] = {"label": label, "ms": elapsed_ms}
    row.update(extra)
    debug_rows.append(row)


def _hydrate_existing_player(repo, draft: Dict[str, object]) -> Dict[str, object]:
    if draft.get("hydrated_from_query"):
        return draft
    query_key = str(st.query_params.get("key", "")).strip()
    access_key = str(draft.get("access_key") or query_key or "").strip()
    if not access_key:
        updated = dict(draft)
        updated["hydrated_from_query"] = True
        return updated

    try:
        canonical = normalize_access_key(access_key)
    except ValueError:
        updated = dict(draft)
        updated["hydrated_from_query"] = True
        return updated

    player = repo.get_player_by_access_key(canonical)
    updated = dict(draft)
    updated["access_key"] = canonical
    updated["hydrated_from_query"] = True
    if player:
        updated["existing_player_id"] = player["id"]
        if not updated.get("name"):
            updated["name"] = player.get("display_name") or player.get("name") or ""
        if not updated.get("emoji_signature"):
            updated["emoji_signature"] = player.get("emoji_signature") or ""
    return updated


def _chapter_options(chapters: List[Dict[str, str]], _) -> List[Dict[str, str]]:
    return [
        {
            "value": chapter["slug"],
            "label": f'{chapter["emoji"]} {_(chapter["name"])}',
        }
        for chapter in chapters
    ]


def _availability_options(_) -> List[Dict[str, str]]:
    return [{"value": item["value"], "label": _(item["label"])} for item in AVAILABILITY_OPTIONS]


def _capacity_options(_) -> List[Dict[str, str]]:
    return [{"value": item["value"], "label": _(item["label"])} for item in CAPACITY_OPTIONS]


def _ensure_widget_state(widget_key: str, draft_key: str) -> None:
    if widget_key not in st.session_state:
        st.session_state[widget_key] = list(draft_value(draft_key, []))


def _ensure_scalar_widget_state(widget_key: str, draft_key: str, default: str = "") -> None:
    if widget_key not in st.session_state:
        st.session_state[widget_key] = str(draft_value(draft_key, default) or default)


def _render_debug_sidebar(
    event,
    draft: Dict[str, object],
    question_by_kind: Dict[str, Dict[str, str]],
    timings: List[Dict[str, object]],
) -> None:
    with st.sidebar:
        st.caption("debug")
        if st.button("Reset draft", use_container_width=True):
            reset_participant_state()
            st.rerun()
        st.write(
            {
                "step": current_step(),
                "event_id": event.get("id", "") if event else "",
                "event_name": event.get("name", "") if event else "",
                "locale": draft.get("locale", ""),
                "access_key_suffix": str(draft.get("access_key") or "")[-4:],
            }
        )
        with st.expander("Profiling", expanded=True):
            st.write(timings)
        with st.expander("Draft", expanded=False):
            st.code(json.dumps(draft, indent=2, ensure_ascii=False), language="json")
        with st.expander("Runtime", expanded=False):
            st.write(
                {
                    "question_ids": {key: value.get("id", "") for key, value in question_by_kind.items()},
                }
            )


def _submit(
    repo,
    event: Dict[str, str],
    draft: Dict[str, object],
    chapters: List[Dict[str, str]],
    question_by_kind: Dict[str, Dict[str, str]],
) -> List[Dict[str, object]]:
    timings: List[Dict[str, object]] = []
    chapter_by_slug = {chapter["slug"]: chapter for chapter in chapters}
    access_key = str(draft.get("access_key") or "").strip()
    started_at = time.perf_counter()
    player = repo.create_or_update_player(
        access_key=access_key,
        display_name=str(draft.get("name") or "Anonymous"),
        emoji_signature=str(draft.get("emoji_signature") or ""),
        anonymous_name=str(draft.get("name") or "Anonymous"),
        role=["helper"],
        capacities=list(draft.get("capacities") or []),
    )
    _profile(timings, "create_or_update_player", started_at, player_id=player["id"])

    locale = str(draft.get("locale") or "fr")
    selected_chapters = list(draft.get("chapters") or [])
    availability = list(draft.get("availability_buckets") or [])
    capacities = list(draft.get("capacities") or [])
    exact_slots = list(draft.get("exact_slots") or [])

    for slug in selected_chapters:
        chapter = chapter_by_slug.get(slug)
        if not chapter:
            continue
        started_at = time.perf_counter()
        repo.create_response(
            title=f'Interest · {chapter["name"]} · {draft.get("name", "")}',
            player_id=player["id"],
            event_id=event["id"],
            chapter_id=chapter["id"],
            question_id=question_by_kind["chapter_interest"]["id"],
            response_type="interest",
            payload_text_value=f'Interested in {chapter["name"]}',
            payload_json_value={
                "locale": locale,
                "chapter_slug": slug,
                "chapter_name": chapter["name"],
            },
            visibility_value="host",
            signal_strength="high",
        )
        _profile(timings, "create_interest_response", started_at, chapter=slug)

    started_at = time.perf_counter()
    repo.create_response(
        title=f'Availability · {draft.get("name", "")}',
        player_id=player["id"],
        event_id=event["id"],
        question_id=question_by_kind["availability"]["id"],
        response_type="availability",
        payload_text_value=", ".join(availability),
        payload_json_value={
            "locale": locale,
            "availability": availability,
            "exact_slots": exact_slots,
        },
        availability=availability,
        exact_start=exact_slots[0]["start"] if exact_slots else None,
        exact_end=exact_slots[0]["end"] if exact_slots else None,
        visibility_value="host",
    )
    _profile(timings, "create_availability_response", started_at)

    if capacities:
        started_at = time.perf_counter()
        repo.create_response(
            title=f'Capacity · {draft.get("name", "")}',
            player_id=player["id"],
            event_id=event["id"],
            question_id=question_by_kind["capacity_offer"]["id"],
            response_type="capacity",
            payload_text_value=", ".join(capacities),
            payload_json_value={"locale": locale, "capacities": capacities},
            visibility_value="host",
        )
        _profile(timings, "create_capacity_response", started_at)

    if not draft.get("existing_player_id"):
        started_at = time.perf_counter()
        repo.log_event(
            title=f'Create key · {draft.get("name", "")}',
            event_id=event["id"],
            actor_id=player["id"],
            action_type="create_key",
            target_type="player",
            target_id=player["id"],
            summary="Participant minted a new key during final submit.",
            payload={"locale": locale},
        )
        _profile(timings, "log_create_key", started_at)

    started_at = time.perf_counter()
    repo.log_event(
        title=f'Select chapters · {draft.get("name", "")}',
        event_id=event["id"],
        actor_id=player["id"],
        action_type="select_chapter",
        target_type="response",
        target_id=player["id"],
        summary="Participant selected chapters.",
        payload={"locale": locale, "chapters": selected_chapters},
    )
    _profile(timings, "log_select_chapter", started_at)
    started_at = time.perf_counter()
    repo.log_event(
        title=f'Submit availability · {draft.get("name", "")}',
        event_id=event["id"],
        actor_id=player["id"],
        action_type="submit_availability",
        target_type="response",
        target_id=player["id"],
        summary="Participant submitted availability.",
        payload={"locale": locale, "availability": availability, "exact_slots": exact_slots},
    )
    _profile(timings, "log_submit_availability", started_at)
    if capacities:
        started_at = time.perf_counter()
        repo.log_event(
            title=f'Submit capacity · {draft.get("name", "")}',
            event_id=event["id"],
            actor_id=player["id"],
            action_type="submit_capacity",
            target_type="response",
            target_id=player["id"],
            summary="Participant submitted capacities.",
            payload={"locale": locale, "capacities": capacities},
        )
        _profile(timings, "log_submit_capacity", started_at)

    update_draft(existing_player_id=player["id"])
    mark_submitted()
    st.session_state["evenz_last_submit_profile"] = timings
    return timings


@st.dialog("Store your helper key")
def _confirm_send_dialog(repo, event, draft, chapters, question_by_kind, _):
    access_key = str(draft.get("access_key") or "")
    emoji_key = hex_to_emoji(access_key)
    emoji_symbols = split_emoji_symbols(emoji_key)
    short_emoji = "".join(emoji_symbols[-4:]) if len(emoji_symbols) >= 4 else emoji_key
    st.markdown(
        f"""
        <div style="text-align:center; font-size:2.2rem; line-height:1.4; margin: 1rem 0 1.5rem 0;">
            {short_emoji}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(_("Take a screenshot of this short key and store it safely."))
    st.code(str(access_key)[-4:], language="text")
    if st.button(_("I took a screenshot"), use_container_width=True):
        _submit(repo, event, draft, chapters, question_by_kind)
        st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="Participant",
        page_icon="🌿",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    inject_evenz_styles()
    init_participant_state()
    page_timings: List[Dict[str, object]] = []
    draft = get_draft()
    step = current_step()

    if step == "locale":
        preview_locale = str(st.session_state.get("evenz_locale_choice", draft.get("locale") or "fr"))
        set_locale(preview_locale)
        _ = get_translator()
        soft_header("Evenz", _("Choose where you want to help."), step="1 / 7")
        selected_locale = native_single_segmented(
            "",
            PARTICIPANT_LANGUAGES,
            "evenz_locale_choice",
            default=str(draft.get("locale") or "fr"),
        )
        if selected_locale != draft.get("locale"):
            update_draft(locale=selected_locale)
            draft = get_draft()
        st.caption(_("Selected language:") + f" {dict(PARTICIPANT_LANGUAGES).get(selected_locale, selected_locale)}")
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        if st.button(_("Start"), use_container_width=True):
            set_step("chapters")
            st.rerun()
        return

    started_at = time.perf_counter()
    repo = get_repo()
    _profile(page_timings, "get_repo", started_at)
    if not repo.is_ready():
        st.error(repo.unavailable_reason or "Evenz is not configured.")
        return

    try:
        started_at = time.perf_counter()
        bundle = get_event_bundle(repo.settings.event_slug or "")
        _profile(page_timings, "get_event_bundle", started_at)
    except Exception as error:
        st.error(str(error))
        return
    event = bundle.get("event")
    if not event:
        st.error("No active event found.")
        return
    questions = list(bundle.get("questions") or [])
    question_by_kind = {question["kind"]: question for question in questions}
    chapters = list(bundle.get("chapters") or [])
    _profile(page_timings, "bundle_counts", time.perf_counter(), questions=len(questions), chapters=len(chapters))

    started_at = time.perf_counter()
    hydrated_draft = _hydrate_existing_player(repo, draft)
    _profile(page_timings, "hydrate_existing_player", started_at, has_key=bool(hydrated_draft.get("access_key")))
    if hydrated_draft != draft:
        update_draft(**hydrated_draft)
        draft = get_draft()
    else:
        draft = hydrated_draft
    set_locale(str(draft.get("locale") or "fr"))
    _ = get_translator()

    _render_debug_sidebar(event, draft, question_by_kind, page_timings + list(st.session_state.get("evenz_last_submit_profile", [])))
    locale = str(draft_value("locale", "fr"))
    set_locale(locale)
    _ = get_translator()

    if step == "chapters":
        soft_header(_("Where would you like to help?"), "", step="2 / 7")
        options = _chapter_options(chapters, _)
        _ensure_widget_state("evenz_chapter_pills", "chapters")
        selected = native_multiselect_pills("", options, "evenz_chapter_pills")
        update_draft(chapters=selected)

        st.markdown("<div style='height: .75rem;'></div>", unsafe_allow_html=True)
        left, right = st.columns(2)
        with left:
            if st.button(_("Back"), use_container_width=True):
                set_step("locale")
                st.rerun()
        with right:
            if st.button(_("Continue"), use_container_width=True):
                if not selected:
                    st.error(_("Choose at least one chapter."))
                else:
                    next_step()
                    st.rerun()
        return

    if step == "identity":
        soft_header(_("How shall I recognise you?"), _("It would be lovely to know what to call each other."), step="3 / 7")
        _ensure_scalar_widget_state("evenz_identity_name", "name")
        name = st.text_input(_("Name or nickname"), key="evenz_identity_name")
        if name != draft.get("name", ""):
            update_draft(name=name)
            draft = get_draft()

        st.markdown("<div style='height: .75rem;'></div>", unsafe_allow_html=True)
        left, right = st.columns(2)
        with left:
            if st.button(_("Back"), use_container_width=True):
                previous_step()
                st.rerun()
        with right:
            if st.button(_("Continue"), use_container_width=True):
                if not str(name).strip():
                    st.error(_("It would be lovely to know what to call you."))
                else:
                    next_step()
                    st.rerun()
        return

    if step == "availability":
        soft_header(_("When could you pass by?"), _("Choose one or more moments."), step="4 / 7")
        options = _availability_options(_)
        _ensure_widget_state("evenz_availability_pills", "availability_buckets")
        selected = native_multiselect_pills("", options, "evenz_availability_pills")
        update_draft(availability_buckets=selected)

        with st.expander(_("Add a precise date / time"), expanded=False):
            precise = st.checkbox(_("Use a precise slot"))
            if precise:
                start_date = st.date_input(_("Start date"), value=dt.date.today())
                start_time = st.time_input(_("Start time"), value=dt.time(hour=14, minute=0))
                end_date = st.date_input(_("End date"), value=dt.date.today())
                end_time = st.time_input(_("End time"), value=dt.time(hour=16, minute=0))
                add_exact_slot(
                    _combine_date_and_time(start_date, start_time),
                    _combine_date_and_time(end_date, end_time),
                )
            else:
                update_draft(exact_slots=[])

        st.markdown("<div style='height: .75rem;'></div>", unsafe_allow_html=True)
        left, right = st.columns(2)
        with left:
            if st.button(_("Back"), use_container_width=True):
                previous_step()
                st.rerun()
        with right:
            if st.button(_("Continue"), use_container_width=True):
                if not selected:
                    st.error(_("Choose at least one availability option."))
                else:
                    next_step()
                    st.rerun()
        return

    if step == "capacity":
        soft_header(_("What kind of help feels good?"), _("Choose what you can offer."), step="5 / 7")
        options = _capacity_options(_)
        _ensure_widget_state("evenz_capacity_pills", "capacities")
        selected = native_multiselect_pills("", options, "evenz_capacity_pills")
        update_draft(capacities=selected)

        st.markdown("<div style='height: .75rem;'></div>", unsafe_allow_html=True)
        left, right = st.columns(2)
        with left:
            if st.button(_("Back"), use_container_width=True):
                previous_step()
                st.rerun()
        with right:
            if st.button(_("Continue"), use_container_width=True):
                next_step()
                st.rerun()
        return

    if step == "review":
        access_key = str(draft_value("access_key", "") or "")
        if not access_key:
            access_key = generate_hex_key()
            update_draft(access_key=access_key)
            draft = get_draft()

        emoji_key = hex_to_emoji(access_key)
        chapter_labels = []
        chapter_by_slug = {chapter["slug"]: chapter for chapter in chapters}
        for slug in draft.get("chapters", []):
            chapter = chapter_by_slug.get(slug)
            if chapter:
                chapter_labels.append(f'{chapter["emoji"]} {_(chapter["name"])}')
        availability_labels = [_(item["label"]) for item in AVAILABILITY_OPTIONS if item["value"] in draft.get("availability_buckets", [])]
        capacity_labels = [_(item["label"]) for item in CAPACITY_OPTIONS if item["value"] in draft.get("capacities", [])]

        soft_header(_("Review"), _("Check your draft before syncing anything."), step="6 / 7")
        review_line(_("Name"), str(draft.get("name") or ""))
        review_line(_("Chapters"), ", ".join(chapter_labels))
        review_line(_("Availability"), ", ".join(availability_labels))
        review_line(_("Capacities"), ", ".join(capacity_labels) or _("Presence only"))
        review_line(_("Key ending"), str(access_key)[-4:])

        summary_block(
            _("Your helper key"),
            _("Only the short ending is shown here. You will see the screenshot card before sending."),
        )

        st.markdown("<div style='height: .75rem;'></div>", unsafe_allow_html=True)
        left, right = st.columns(2)
        with left:
            if st.button(_("Edit"), use_container_width=True):
                set_step("chapters")
                st.rerun()
        with right:
            if st.button(_("Send"), use_container_width=True):
                _confirm_send_dialog(repo, event, get_draft(), chapters, question_by_kind, _)
        return

    if step == "done":
        soft_header(_("You’re in."), _("I’ll gather the signals and suggest a moment."), step="7 / 7")
        summary_block(
            _("Saved"),
            _("Your draft has been synced. Thank you for helping The Base move forward."),
        )
        if st.button(_("Start again"), use_container_width=True):
            reset_participant_state()
            st.rerun()


if __name__ == "__main__":
    main()
