from __future__ import annotations

import datetime as dt
import json
import time
from typing import Dict, List

import streamlit as st

from app.components import (
    editorial_paragraph,
    gesture_cloud,
    inject_evenz_styles,
    native_multiselect_pills,
    rhythm_gap,
    review_line,
    soft_header,
    summary_block,
)
from app.flow import (
    add_exact_slot,
    clear_exact_slots,
    current_step,
    draft_value,
    get_draft,
    init_participant_state,
    mark_submitted,
    next_step,
    reset_participant_state,
    set_step,
    update_draft,
)
from app.i18n import PARTICIPANT_LANGUAGES, get_translator, set_locale
import streamlit.components.v1 as components

from app.key_codec import (
    generate_hex_key,
    hex_to_emoji,
    key_to_emoji_suffix,
    normalize_access_key,
    split_emoji_symbols,
)
from app.models import AVAILABILITY_OPTIONS, CAPACITY_OPTIONS
from app.notion_client import init_repo
from app.config import load_settings


@st.cache_resource(show_spinner=False)
def get_repo():
    return init_repo(load_settings())


LOCALE_ICONS = {"fr": "🇫🇷", "en": "🇬🇧", "it": "🇮🇹"}


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


def _profile(
    debug_rows: List[Dict[str, object]], label: str, started_at: float, **extra: object
) -> None:
    elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
    row: Dict[str, object] = {"label": label, "ms": elapsed_ms}
    row.update(extra)
    debug_rows.append(row)


def _hydrate_existing_player(repo, draft: Dict[str, object]) -> Dict[str, object]:
    if draft.get("hydrated_from_query"):
        return draft
    session_key = str(st.session_state.get("evenz_login_access_key") or "").strip()
    query_key = str(st.query_params.get("key", "")).strip()
    access_key = str(draft.get("access_key") or session_key or query_key or "").strip()
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
    if session_key:
        st.session_state.pop("evenz_login_access_key", None)
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
            "label": chapter["emoji"],
        }
        for chapter in chapters
    ]


def _availability_options(_) -> List[Dict[str, str]]:
    return [
        {"value": item["value"], "label": _(item["label"])}
        for item in AVAILABILITY_OPTIONS
    ]


def _capacity_options(_) -> List[Dict[str, str]]:
    return [
        {"value": item["value"], "label": _(item["label"])} for item in CAPACITY_OPTIONS
    ]


def _inject_locale_icon_styles() -> None:
    st.markdown(
        """
        <style>
        [class*="st-key-evenz_locale_option_"] button {
            min-height: 7rem !important;
            min-width: 7rem !important;
            margin-top: 0 !important;
            padding: 0 !important;
            border-radius: 2rem !important;
            font-size: 4.6rem !important;
            line-height: 1 !important;
            background: rgba(18, 23, 32, 0.92) !important;
            border: 1px solid rgba(255, 255, 255, 0.16) !important;
            color: var(--evenz-fg) !important;
        }
        [class*="st-key-evenz_locale_option_"] button[kind="primary"] {
            background: var(--evenz-accent-soft) !important;
            border-color: var(--evenz-accent) !important;
            color: var(--evenz-accent) !important;
        }
        [class*="st-key-evenz_locale_option_"] button p {
            font-size: 4.6rem !important;
            line-height: 1 !important;
            margin: 0 !important;
        }
        @media (max-width: 640px) {
            [class*="st-key-evenz_locale_option_"] button {
                min-height: 6.25rem !important;
                min-width: 6.25rem !important;
                font-size: 4rem !important;
            }
            [class*="st-key-evenz_locale_option_"] button p {
                font-size: 4rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _inject_chapter_icon_styles() -> None:
    st.markdown(
        """
        <style>
        [class*="st-key-evenz_chapter_option_"] button {
            min-height: 8.25rem !important;
            min-width: 8.25rem !important;
            margin-top: 0 !important;
            padding: 0 !important;
            border-radius: 2.4rem !important;
            font-size: 6rem !important;
            line-height: 1 !important;
            background: rgba(14, 19, 28, 0.92) !important;
            border: 1px solid rgba(255, 255, 255, 0.16) !important;
            color: var(--evenz-fg) !important;
        }
        [class*="st-key-evenz_chapter_option_"] button[kind="primary"] {
            background: var(--evenz-accent-soft) !important;
            border-color: var(--evenz-accent) !important;
            color: var(--evenz-accent) !important;
        }
        [class*="st-key-evenz_chapter_option_"] button p {
            font-size: 6rem !important;
            line-height: 1 !important;
            margin: 0 !important;
        }
        @media (max-width: 640px) {
            [class*="st-key-evenz_chapter_option_"] button {
                min-height: 7.2rem !important;
                min-width: 7.2rem !important;
                font-size: 5.2rem !important;
            }
            [class*="st-key-evenz_chapter_option_"] button p {
                font-size: 5.2rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _locale_editorial_text(_) -> str:
    return " · ".join(
        f"{LOCALE_ICONS.get(code, '')} {label.split(' ', 1)[1] if ' ' in label else label}"
        for code, label in PARTICIPANT_LANGUAGES
    )


def _chapter_hint_text(_) -> str:
    translated = _("chapter_hints")
    if translated != "chapter_hints":
        return translated
    return (
        "🍳 cook, imagine, set in place · 🪴 tend, repot, prune · "
        "👘 sort, fold, gift · 📚 read, release, gift · "
        "🎨 display, transform, archive"
    )


def _toggle_chapter(slug: str) -> None:
    current = list(draft_value("chapters", []))
    if slug in current:
        current = [item for item in current if item != slug]
    else:
        current.append(slug)
    update_draft(chapters=current)


def _ensure_widget_state(widget_key: str, draft_key: str) -> None:
    if widget_key not in st.session_state:
        st.session_state[widget_key] = list(draft_value(draft_key, []))


def _ensure_scalar_widget_state(
    widget_key: str, draft_key: str, default: str = ""
) -> None:
    if widget_key not in st.session_state:
        st.session_state[widget_key] = str(draft_value(draft_key, default) or default)


def _ensure_exact_slot_state() -> None:
    exact_slots = list(draft_value("exact_slots", []))
    if "evenz_exact_slot_enabled" not in st.session_state:
        st.session_state["evenz_exact_slot_enabled"] = bool(exact_slots)
    if exact_slots:
        try:
            start_value = dt.datetime.fromisoformat(str(exact_slots[0]["start"]))
            end_value = dt.datetime.fromisoformat(str(exact_slots[0]["end"]))
        except Exception:
            start_value = dt.datetime.combine(
                dt.date.today(), dt.time(hour=14, minute=0)
            )
            end_value = dt.datetime.combine(dt.date.today(), dt.time(hour=16, minute=0))
    else:
        start_value = dt.datetime.combine(dt.date.today(), dt.time(hour=14, minute=0))
        end_value = dt.datetime.combine(dt.date.today(), dt.time(hour=16, minute=0))
    st.session_state.setdefault("evenz_exact_start_date", start_value.date())
    st.session_state.setdefault(
        "evenz_exact_start_time", start_value.time().replace(second=0, microsecond=0)
    )
    st.session_state.setdefault("evenz_exact_end_date", end_value.date())
    st.session_state.setdefault(
        "evenz_exact_end_time", end_value.time().replace(second=0, microsecond=0)
    )


def _mark_exact_slot_enabled() -> None:
    st.session_state["evenz_exact_slot_enabled"] = True


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
                    "question_ids": {
                        key: value.get("id", "")
                        for key, value in question_by_kind.items()
                    },
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
            title=f"Interest · {chapter['name']} · {draft.get('name', '')}",
            player_id=player["id"],
            event_id=event["id"],
            chapter_id=chapter["id"],
            question_id=question_by_kind["chapter_interest"]["id"],
            response_type="interest",
            payload_text_value=f"Interested in {chapter['name']}",
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
        title=f"Availability · {draft.get('name', '')}",
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
            title=f"Capacity · {draft.get('name', '')}",
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
            title=f"Create key · {draft.get('name', '')}",
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
        title=f"Select chapters · {draft.get('name', '')}",
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
        title=f"Submit availability · {draft.get('name', '')}",
        event_id=event["id"],
        actor_id=player["id"],
        action_type="submit_availability",
        target_type="response",
        target_id=player["id"],
        summary="Participant submitted availability.",
        payload={
            "locale": locale,
            "availability": availability,
            "exact_slots": exact_slots,
        },
    )
    _profile(timings, "log_submit_availability", started_at)
    if capacities:
        started_at = time.perf_counter()
        repo.log_event(
            title=f"Submit capacity · {draft.get('name', '')}",
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


def _existing_short_emoji_suffixes(repo) -> set[str]:
    suffixes: set[str] = set()
    for player in repo.list_players(limit=500):
        access_key = str(player.get("access_key") or "")
        if not access_key:
            continue
        try:
            suffix = key_to_emoji_suffix(access_key, 4)
        except ValueError:
            continue
        if suffix:
            suffixes.add(suffix)
    return suffixes


def _mint_unique_access_key(repo, suffix_length: int = 4, attempts: int = 256) -> str:
    existing_suffixes = _existing_short_emoji_suffixes(repo)
    for _ in range(attempts):
        candidate = generate_hex_key()
        try:
            suffix = key_to_emoji_suffix(candidate, suffix_length)
        except ValueError:
            continue
        if suffix not in existing_suffixes and not repo.get_player_by_access_key(candidate):
            return candidate
    raise RuntimeError("Could not mint a unique emoji access key.")


def _prefill_login_with_current_key() -> None:
    access_key = str(get_draft().get("access_key") or "")
    if not access_key:
        return
    try:
        st.session_state["evenz_login_short_emoji_prefill"] = key_to_emoji_suffix(
            access_key, 4
        )
    except ValueError:
        st.session_state.pop("evenz_login_short_emoji_prefill", None)


def _open_confirm_send_dialog(repo, event, draft, chapters, question_by_kind, _):
    @st.dialog(_("Store your helper key"))
    def _confirm_send_dialog() -> None:
        access_key = str(draft.get("access_key") or "")
        emoji_key = hex_to_emoji(access_key)
        emoji_symbols = split_emoji_symbols(emoji_key)
        short_emoji = (
            "".join(emoji_symbols[-4:]) if len(emoji_symbols) >= 4 else emoji_key
        )
        st.markdown(
            f"""
            <div style="text-align:center; font-size:4rem; line-height:1.2; letter-spacing:.14em; margin: 1.1rem 0 1.2rem 0;">
                {short_emoji}
            </div>
            """,
            unsafe_allow_html=True,
        )
        components.html(
            f"""
            <div style="display:flex; justify-content:center; margin: .6rem 0 1rem 0;">
              <button
                onclick="navigator.clipboard.writeText({short_emoji!r})"
                style="
                  border: 1px solid rgba(255,255,255,.18);
                  border-radius: 999px;
                  background: rgba(255,255,255,.04);
                  color: rgba(244,241,232,.92);
                  padding: .6rem 1rem;
                  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                  font-size: 1rem;
                  line-height: 1.2;
                  cursor: pointer;
                "
              >
                ⧉ {_("Copy the emoji key")}
              </button>
            </div>
            """,
            height=62,
        )
        st.caption(_("Take a screenshot of this short key and store it safely."))
        if st.button(_("I took a screenshot"), use_container_width=True):
            _submit(repo, event, draft, chapters, question_by_kind)
            st.rerun()

    _confirm_send_dialog()


def main() -> None:
    st.set_page_config(
        page_title="Base",
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
        preview_locale = str(
            st.session_state.get("evenz_locale_choice", draft.get("locale") or "fr")
        )
        set_locale(preview_locale)
        _ = get_translator()
        _inject_locale_icon_styles()
        soft_header(
            "_Major update @ Base_", _("How shall we communicate?"), step="1 / 7"
        )
        current_locale = str(draft.get("locale") or "fr")
        locale_columns = st.columns(len(PARTICIPANT_LANGUAGES), gap="small")
        for column, (code, _label) in zip(locale_columns, PARTICIPANT_LANGUAGES):
            with column:
                if st.button(
                    LOCALE_ICONS.get(code, code),
                    key=f"evenz_locale_option_{code}",
                    type="primary" if code == current_locale else "secondary",
                    use_container_width=True,
                ):
                    update_draft(locale=code)
                    st.rerun()
        editorial_paragraph(_("base_update_story"))
        editorial_paragraph(_locale_editorial_text(_))
        st.caption(
            _("Selected language:")
            + f" {dict(PARTICIPANT_LANGUAGES).get(current_locale, current_locale)}"
        )
        rhythm_gap(0.8)
        if st.button(
            _("Continue"),
            type="primary",
            use_container_width=True,
            key="evenz_locale_continue",
        ):
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
    _profile(
        page_timings,
        "bundle_counts",
        time.perf_counter(),
        questions=len(questions),
        chapters=len(chapters),
    )

    started_at = time.perf_counter()
    hydrated_draft = _hydrate_existing_player(repo, draft)
    _profile(
        page_timings,
        "hydrate_existing_player",
        started_at,
        has_key=bool(hydrated_draft.get("access_key")),
    )
    if hydrated_draft != draft:
        update_draft(**hydrated_draft)
        draft = get_draft()
    else:
        draft = hydrated_draft
    set_locale(str(draft.get("locale") or "fr"))
    _ = get_translator()

    _render_debug_sidebar(
        event,
        draft,
        question_by_kind,
        page_timings + list(st.session_state.get("evenz_last_submit_profile", [])),
    )
    locale = str(draft_value("locale", "fr"))
    set_locale(locale)
    _ = get_translator()

    if step == "chapters":
        _inject_chapter_icon_styles()
        soft_header(_("Where would you like to help?"), "", step="2 / 7")
        selected = list(draft_value("chapters", []))
        chapter_rows = [chapters[:3], chapters[3:]]
        for row in chapter_rows:
            row_columns = st.columns(len(row), gap="small")
            for column, chapter in zip(row_columns, row):
                with column:
                    if st.button(
                        chapter["emoji"],
                        key=f"evenz_chapter_option_{chapter['slug']}",
                        type="primary" if chapter["slug"] in selected else "secondary",
                        use_container_width=True,
                    ):
                        _toggle_chapter(chapter["slug"])
                        st.rerun()
            rhythm_gap(0.4)
        selected = list(draft_value("chapters", []))
        gesture_cloud(_chapter_hint_text(_))

        rhythm_gap(0.8)
        if st.button(_("Continue"), use_container_width=True):
            if not selected:
                st.error(_("Choose at least one chapter."))
            else:
                next_step()
                st.rerun()
        return

    if step == "identity":
        soft_header(
            _("How shall I recognise you?"),
            _("It would be lovely to know what to call each other."),
            step="3 / 7",
        )
        _ensure_scalar_widget_state("evenz_identity_name", "name")
        name = st.text_input(_("Name or nickname"), key="evenz_identity_name")
        if name != draft.get("name", ""):
            update_draft(name=name)
            draft = get_draft()

        rhythm_gap(0.8)
        if st.button(_("Continue"), use_container_width=True):
            if not str(name).strip():
                st.error(_("It would be lovely to know what to call you."))
            else:
                next_step()
                st.rerun()
        return

    if step == "availability":
        soft_header(
            _("When could you pass by?"), _("Choose one or more moments."), step="4 / 7"
        )
        options = _availability_options(_)
        _ensure_widget_state("evenz_availability_pills", "availability_buckets")
        selected = native_multiselect_pills("", options, "evenz_availability_pills")
        update_draft(availability_buckets=selected)

        _ensure_exact_slot_state()
        with st.expander(_("Add a precise date / time"), expanded=False):
            start_date = st.date_input(
                _("Start date"),
                key="evenz_exact_start_date",
                on_change=_mark_exact_slot_enabled,
            )
            start_time = st.time_input(
                _("Start time"),
                key="evenz_exact_start_time",
                on_change=_mark_exact_slot_enabled,
            )
            end_date = st.date_input(
                _("End date"),
                key="evenz_exact_end_date",
                on_change=_mark_exact_slot_enabled,
            )
            end_time = st.time_input(
                _("End time"),
                key="evenz_exact_end_time",
                on_change=_mark_exact_slot_enabled,
            )
            if st.session_state.get("evenz_exact_slot_enabled"):
                add_exact_slot(
                    _combine_date_and_time(start_date, start_time),
                    _combine_date_and_time(end_date, end_time),
                )
            else:
                clear_exact_slots()

        rhythm_gap(0.8)
        if st.button(_("Continue"), use_container_width=True):
            if not selected:
                st.error(_("Choose at least one availability option."))
            else:
                next_step()
                st.rerun()
        return

    if step == "capacity":
        soft_header(
            _("What kind of help feels good?"),
            _("Choose what you can offer."),
            step="5 / 7",
        )
        options = _capacity_options(_)
        _ensure_widget_state("evenz_capacity_pills", "capacities")
        selected = native_multiselect_pills("", options, "evenz_capacity_pills")
        update_draft(capacities=selected)

        rhythm_gap(0.8)
        if st.button(_("Continue"), use_container_width=True):
            next_step()
            st.rerun()
        return

    if step == "review":
        access_key = str(draft_value("access_key", "") or "")
        if not access_key:
            access_key = _mint_unique_access_key(repo)
            update_draft(access_key=access_key)
            draft = get_draft()

        emoji_key = hex_to_emoji(access_key)
        chapter_labels = []
        chapter_by_slug = {chapter["slug"]: chapter for chapter in chapters}
        for slug in draft.get("chapters", []):
            chapter = chapter_by_slug.get(slug)
            if chapter:
                chapter_labels.append(f"{chapter['emoji']} {_(chapter['name'])}")
        availability_labels = [
            _(item["label"])
            for item in AVAILABILITY_OPTIONS
            if item["value"] in draft.get("availability_buckets", [])
        ]
        capacity_labels = [
            _(item["label"])
            for item in CAPACITY_OPTIONS
            if item["value"] in draft.get("capacities", [])
        ]

        soft_header(
            _("Review"), _("Check your draft before syncing anything."), step="6 / 7"
        )
        review_line(_("Name"), str(draft.get("name") or ""))
        review_line(_("Chapters"), ", ".join(chapter_labels))
        review_line(_("Availability"), ", ".join(availability_labels))
        review_line(_("Capacities"), ", ".join(capacity_labels) or _("Presence only"))

        rhythm_gap(0.8)
        left, right = st.columns(2)
        with left:
            if st.button(_("Edit"), use_container_width=True):
                set_step("chapters")
                st.rerun()
        with right:
            if st.button(_("Send"), use_container_width=True):
                _open_confirm_send_dialog(
                    repo, event, get_draft(), chapters, question_by_kind, _
                )
        return

    if step == "done":
        is_authenticated = bool(st.session_state.get("evenz_authenticated_access_key"))
        display_name = str(draft.get("name") or "").strip()
        soft_header(
            _("You’re in."),
            _("I’ll gather the signals and suggest a moment."),
            step="7 / 7",
        )
        summary_block(
            _("Saved"),
            _("Your preferences are integrating with the others'. Thank you for sharing them."),
        )
        editorial_paragraph(_("Wait for a signal through WhatsApp."))
        editorial_paragraph(
            _("Have a look at the library. Log in with your emoji key, then see what may resonate.")
        )
        left, right = st.columns(2)
        with left:
            if st.button(_("Browse the library"), use_container_width=True):
                st.session_state["evenz_post_login_target"] = "pages/05_library.py"
                _prefill_login_with_current_key()
                st.switch_page("pages/00_login.py")
        with right:
            if is_authenticated:
                summary_block(
                    _("Welcome"),
                    _("Welcome, {name}.").format(name=display_name or _("friend")),
                )
            else:
                if st.button(_("Go to login"), use_container_width=True):
                    _prefill_login_with_current_key()
                    st.switch_page("pages/00_login.py")


if __name__ == "__main__":
    main()
