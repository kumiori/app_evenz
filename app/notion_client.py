from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional

from app.config import AppSettings, DatabaseIds
from app.key_codec import hex_to_emoji, hex_to_phrase, split_emoji_symbols

NOTION_CLIENT_AVAILABLE = False
try:
    from notion_client import Client
    from notion_client.errors import APIResponseError, HTTPResponseError, RequestTimeoutError
    NOTION_CLIENT_AVAILABLE = True
except Exception:  # pragma: no cover
    Client = Any  # type: ignore

    class APIResponseError(Exception):  # type: ignore
        status: int = 0

    class HTTPResponseError(Exception):  # type: ignore
        pass

    class RequestTimeoutError(Exception):  # type: ignore
        pass


def iso_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clean_notion_id(value: str) -> str:
    raw = str(value or "").strip().strip("\"'")
    if not raw:
        return ""
    dashed = re.search(
        r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})",
        raw,
    )
    if dashed:
        return dashed.group(1).lower()
    compact = re.search(r"([0-9a-fA-F]{32})", raw)
    if compact:
        token = compact.group(1).lower()
        return f"{token[0:8]}-{token[8:12]}-{token[12:16]}-{token[16:20]}-{token[20:32]}"
    return raw


def title_text(value: str) -> Dict[str, Any]:
    return {"title": [{"type": "text", "text": {"content": value[:2000]}}]}


def rich_text(value: str) -> Dict[str, Any]:
    return {"rich_text": [{"type": "text", "text": {"content": value[:2000]}}]}


def select(name: str) -> Dict[str, Any]:
    return {"select": {"name": name}}


def multi_select(names: List[str]) -> Dict[str, Any]:
    return {"multi_select": [{"name": name} for name in names]}


def checkbox(value: bool) -> Dict[str, Any]:
    return {"checkbox": bool(value)}


def relation(page_ids: List[str]) -> Dict[str, Any]:
    return {"relation": [{"id": page_id} for page_id in page_ids if page_id]}


def date_value(value: Optional[str] = None) -> Dict[str, Any]:
    return {"date": {"start": value or iso_now()}}


def number_value(value: Optional[int]) -> Dict[str, Any]:
    return {"number": value}


def _execute_with_retry(func: Any, *args: Any, **kwargs: Any) -> Any:
    last_error: Optional[Exception] = None
    for attempt in range(3):
        try:
            return func(*args, **kwargs)
        except APIResponseError as error:  # type: ignore[misc]
            last_error = error
            if getattr(error, "status", None) != 429 or attempt == 2:
                break
            time.sleep(0.5 * (2**attempt))
        except (HTTPResponseError, RequestTimeoutError) as error:
            last_error = error
            if attempt == 2:
                break
            time.sleep(0.5 * (2**attempt))
    if last_error:
        raise last_error
    raise RuntimeError("Notion request failed.")


def _extract_text(prop: Dict[str, Any]) -> str:
    values = prop.get("title") or prop.get("rich_text") or []
    if not isinstance(values, list):
        return ""
    return "".join(str(item.get("plain_text", "")) for item in values if isinstance(item, dict))


def _extract_select(prop: Dict[str, Any]) -> str:
    value = prop.get("select") if isinstance(prop, dict) else None
    return str(value.get("name", "")) if isinstance(value, dict) else ""


def _extract_multi_select(prop: Dict[str, Any]) -> List[str]:
    values = prop.get("multi_select") if isinstance(prop, dict) else None
    if not isinstance(values, list):
        return []
    return [str(item.get("name", "")) for item in values if isinstance(item, dict)]


def _extract_checkbox(prop: Dict[str, Any]) -> bool:
    return bool(prop.get("checkbox", False)) if isinstance(prop, dict) else False


def _extract_date(prop: Dict[str, Any]) -> str:
    date_payload = prop.get("date") if isinstance(prop, dict) else None
    return str(date_payload.get("start", "")) if isinstance(date_payload, dict) else ""


def _extract_relation_ids(prop: Dict[str, Any]) -> List[str]:
    values = prop.get("relation") if isinstance(prop, dict) else None
    if not isinstance(values, list):
        return []
    return [str(item.get("id", "")) for item in values if isinstance(item, dict)]


def _extract_number(prop: Dict[str, Any]) -> Optional[float]:
    if not isinstance(prop, dict):
        return None
    value = prop.get("number")
    return float(value) if value is not None else None


@lru_cache(maxsize=128)
def _resolve_data_source_id(client: Client, database_id: str) -> str:
    clean_id = clean_notion_id(database_id)
    if not clean_id:
        return ""

    databases_endpoint = getattr(client, "databases", None)
    db_retrieve = getattr(databases_endpoint, "retrieve", None) if databases_endpoint else None
    if callable(db_retrieve):
        try:
            payload = _execute_with_retry(db_retrieve, database_id=clean_id)
            data_sources = payload.get("data_sources", []) if isinstance(payload, dict) else []
            if data_sources and isinstance(data_sources[0], dict):
                return clean_notion_id(data_sources[0].get("id"))
            return clean_id
        except Exception:
            pass

    data_sources_endpoint = getattr(client, "data_sources", None)
    ds_retrieve = getattr(data_sources_endpoint, "retrieve", None) if data_sources_endpoint else None
    if callable(ds_retrieve):
        try:
            _execute_with_retry(ds_retrieve, data_source_id=clean_id)
            return clean_id
        except Exception:
            pass
    return clean_id


class EvenzRepo:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.unavailable_reason = ""
        if not NOTION_CLIENT_AVAILABLE:
            self.unavailable_reason = "The `notion-client` package is not installed in this Python environment."
            self.client = None
        elif not settings.notion_token:
            self.unavailable_reason = "Missing `NOTION_TOKEN` or `.streamlit/secrets.toml` notion credentials."
            self.client = None
        else:
            self.client = Client(auth=settings.notion_token, notion_version=settings.notion_version)
        self.dbs = DatabaseIds(
            players=clean_notion_id(settings.dbs.players),
            events=clean_notion_id(settings.dbs.events),
            chapters=clean_notion_id(settings.dbs.chapters),
            questions=clean_notion_id(settings.dbs.questions),
            responses=clean_notion_id(settings.dbs.responses),
            sessions=clean_notion_id(settings.dbs.sessions),
            event_log=clean_notion_id(settings.dbs.event_log),
        )
        self._reset_runtime_caches()

    def _reset_runtime_caches(self) -> None:
        self._get_current_event_cached = lru_cache(maxsize=4)(self._get_current_event_uncached)
        self._list_chapters_cached = lru_cache(maxsize=16)(self._list_chapters_uncached)
        self._list_questions_cached = lru_cache(maxsize=32)(self._list_questions_uncached)

    def is_ready(self) -> bool:
        return bool(self.client)

    def supports_data_sources(self) -> bool:
        if not self.client:
            return False
        return callable(getattr(getattr(self.client, "data_sources", None), "update", None))

    def retrieve_db(self, db_id: str) -> Dict[str, Any]:
        if not self.client:
            return {}
        return _execute_with_retry(self.client.databases.retrieve, database_id=db_id)

    @lru_cache(maxsize=64)
    def get_title_prop(self, db_id: str) -> str:
        payload = self.retrieve_db(db_id)
        props = payload.get("properties") or {}
        for name, spec in props.items():
            if spec.get("type") == "title":
                return name
        return "Name"

    def rel_prop(self, target_db_id: str, backref_name: str) -> Dict[str, Any]:
        if not self.client:
            return {}
        if self.supports_data_sources():
            return {
                "relation": {
                    "data_source_id": _resolve_data_source_id(self.client, target_db_id),
                    "dual_property": {"synced_property_name": backref_name},
                }
            }
        return {
            "relation": {
                "database_id": target_db_id,
                "dual_property": {"synced_property_name": backref_name},
            }
        }

    def update_schema(self, db_id: str, properties: Dict[str, Any]) -> None:
        if not self.client:
            return
        if self.supports_data_sources():
            _execute_with_retry(
                self.client.data_sources.update,
                data_source_id=_resolve_data_source_id(self.client, db_id),
                properties=properties,
            )
            return
        _execute_with_retry(self.client.databases.update, database_id=db_id, properties=properties)

    def query(self, db_id: str, **kwargs: Any) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        if callable(getattr(getattr(self.client, "data_sources", None), "query", None)):
            payload = _execute_with_retry(
                self.client.data_sources.query,
                data_source_id=_resolve_data_source_id(self.client, db_id),
                **kwargs,
            )
        else:
            payload = _execute_with_retry(self.client.databases.query, database_id=db_id, **kwargs)
        return list(payload.get("results", []))

    def ensure_page_by_title(
        self,
        db_id: str,
        title: str,
        extra_props: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        title_prop = self.get_title_prop(db_id)
        results = self.query(
            db_id,
            filter={"property": title_prop, "title": {"equals": title}},
            page_size=1,
        )
        if results:
            return results[0]
        properties = {title_prop: title_text(title)}
        if extra_props:
            properties.update(extra_props)
        return _execute_with_retry(
            self.client.pages.create,
            parent={"database_id": db_id},
            properties=properties,
        )

    def create_page(self, db_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        if not self.client:
            return {}
        page = _execute_with_retry(
            self.client.pages.create,
            parent={"database_id": db_id},
            properties=properties,
        )
        self._reset_runtime_caches()
        return page

    def update_page(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        if not self.client:
            return {}
        page = _execute_with_retry(self.client.pages.update, page_id=page_id, properties=properties)
        self._reset_runtime_caches()
        return page

    def get_current_event(self) -> Optional[Dict[str, Any]]:
        return self._get_current_event_cached()

    def _get_current_event_uncached(self) -> Optional[Dict[str, Any]]:
        pages = self.query(
            self.dbs.events,
            filter={"property": "slug", "rich_text": {"equals": self.settings.event_slug}},
            page_size=1,
        )
        if pages:
            return self._normalize_event(pages[0])
        active = self.query(
            self.dbs.events,
            filter={"property": "active", "checkbox": {"equals": True}},
            page_size=1,
        )
        return self._normalize_event(active[0]) if active else None

    def list_chapters(self, event_id: str) -> List[Dict[str, Any]]:
        return self._list_chapters_cached(event_id)

    def _list_chapters_uncached(self, event_id: str) -> List[Dict[str, Any]]:
        pages = self.query(
            self.dbs.chapters,
            filter={
                "and": [
                    {"property": "event", "relation": {"contains": event_id}},
                    {"property": "active", "checkbox": {"equals": True}},
                ]
            },
            sorts=[{"property": "sort_order", "direction": "ascending"}],
            page_size=50,
        )
        return [self._normalize_chapter(page) for page in pages]

    def list_players(self, limit: int = 200) -> List[Dict[str, Any]]:
        pages = self.query(
            self.dbs.players,
            sorts=[{"property": "last_seen_at", "direction": "descending"}],
            page_size=limit,
        )
        return [self._normalize_player(page) for page in pages]

    def list_questions(
        self,
        event_id: str,
        *,
        kind: str = "",
        chapter_id: str = "",
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        return self._list_questions_cached(event_id, kind, chapter_id, active_only)

    def _list_questions_uncached(
        self,
        event_id: str,
        kind: str = "",
        chapter_id: str = "",
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        filters: List[Dict[str, Any]] = [{"property": "event", "relation": {"contains": event_id}}]
        if kind:
            filters.append({"property": "kind", "select": {"equals": kind}})
        if chapter_id:
            filters.append({"property": "chapter", "relation": {"contains": chapter_id}})
        if active_only:
            filters.append({"property": "active", "checkbox": {"equals": True}})
        pages = self.query(
            self.dbs.questions,
            filter={"and": filters},
            sorts=[{"property": "step_order", "direction": "ascending"}],
            page_size=100,
        )
        return [self._normalize_question(page) for page in pages]

    def list_responses(self, event_id: str) -> List[Dict[str, Any]]:
        pages = self.query(
            self.dbs.responses,
            filter={"property": "event", "relation": {"contains": event_id}},
            sorts=[{"property": "submitted_at", "direction": "descending"}],
            page_size=200,
        )
        return [self._normalize_response(page) for page in pages]

    def list_sessions(self, event_id: str) -> List[Dict[str, Any]]:
        pages = self.query(
            self.dbs.sessions,
            filter={"property": "event", "relation": {"contains": event_id}},
            sorts=[{"property": "created_at", "direction": "descending"}],
            page_size=50,
        )
        return [self._normalize_session(page) for page in pages]

    def list_event_log(self, event_id: str, limit: int = 25) -> List[Dict[str, Any]]:
        if self.dbs.event_log != self.dbs.events:
            pages = self.query(
                self.dbs.event_log,
                filter={"property": "event", "relation": {"contains": event_id}},
                sorts=[{"property": "timestamp", "direction": "descending"}],
                page_size=limit,
            )
        else:
            pages = self.query(
                self.dbs.event_log,
                filter={
                    "and": [
                        {"property": "event", "relation": {"contains": event_id}},
                        {"property": "action_type", "select": {"is_not_empty": True}},
                    ]
                },
                sorts=[{"property": "timestamp", "direction": "descending"}],
                page_size=limit,
            )
        return [self._normalize_log(page) for page in pages]

    def get_player_by_access_key(self, access_key: str) -> Optional[Dict[str, Any]]:
        pages = self.query(
            self.dbs.players,
            filter={"property": "access_key", "rich_text": {"equals": access_key}},
            page_size=1,
        )
        return self._normalize_player(pages[0]) if pages else None

    def find_players_by_emoji_suffix(self, suffix: str, length: int = 4) -> List[Dict[str, Any]]:
        prop = "access_key_last4" if length == 4 else ""
        if not prop:
            return []
        pages = self.query(
            self.dbs.players,
            filter={"property": prop, "rich_text": {"equals": suffix}},
            page_size=10,
        )
        return [self._normalize_player(page) for page in pages]

    def create_or_update_player(
        self,
        *,
        access_key: str,
        display_name: str,
        emoji_signature: str = "",
        anonymous_name: str = "",
        contact_channel: str = "direct",
        contact_value: str = "",
        role: Optional[List[str]] = None,
        capacities: Optional[List[str]] = None,
        notes_private: str = "",
    ) -> Dict[str, Any]:
        existing = self.get_player_by_access_key(access_key)
        access_key_hash = hashlib.sha256(access_key.encode("utf-8")).hexdigest()
        emoji = hex_to_emoji(access_key)
        phrase = hex_to_phrase(access_key)

        props: Dict[str, Any] = {
            self.get_title_prop(self.dbs.players): title_text(display_name or "Anonymous"),
            "access_key": rich_text(access_key),
            "access_key_hash": rich_text(access_key_hash),
            "access_key_last4": rich_text(access_key[-4:]),
            "emoji_signature": rich_text(emoji_signature or emoji),
            "anonymous_name": rich_text(anonymous_name or "Anonymous"),
            "contact_channel": select(contact_channel),
            "contact_value": rich_text(contact_value),
            "role": multi_select(role or ["helper"]),
            "onboarding_state": select("active" if display_name else "identified"),
            "has_car": checkbox("has_car" in (capacities or [])),
            "can_lift": checkbox("carry" in (capacities or [])),
            "can_tools": checkbox("tools" in (capacities or [])),
            "can_sort": checkbox("sort" in (capacities or [])),
            "can_cook": checkbox("cook" in (capacities or [])),
            "light_tasks_only": checkbox("light_tasks_only" in (capacities or [])),
            "notes_private": rich_text(notes_private or f"emoji:{emoji} phrase:{phrase}"),
            "last_seen_at": date_value(),
        }
        if not existing:
            props["created_at"] = date_value()
        if existing:
            page = self.update_page(existing["id"], props)
        else:
            page = self.create_page(self.dbs.players, props)
        return self._normalize_player(page)

    def create_response(
        self,
        *,
        title: str,
        player_id: str,
        event_id: str,
        response_type: str,
        payload_text_value: str,
        payload_json_value: Dict[str, Any],
        visibility_value: str = "host",
        chapter_id: str = "",
        question_id: str = "",
        availability: Optional[List[str]] = None,
        exact_start: Optional[str] = None,
        exact_end: Optional[str] = None,
        signal_strength: str = "medium",
        source: str = "whatsapp_link",
    ) -> Dict[str, Any]:
        properties: Dict[str, Any] = {
            self.get_title_prop(self.dbs.responses): title_text(title),
            "player": relation([player_id]),
            "event": relation([event_id]),
            "response_type": select(response_type),
            "payload_text": rich_text(payload_text_value),
            "payload_json": rich_text(json.dumps(payload_json_value, ensure_ascii=False)),
            "availability_bucket": multi_select(availability or []),
            "signal_strength": select(signal_strength),
            "visibility": select(visibility_value),
            "submitted_at": date_value(),
            "source": select(source),
        }
        if chapter_id:
            properties["chapter"] = relation([chapter_id])
        if question_id:
            properties["question"] = relation([question_id])
        if exact_start:
            properties["exact_start"] = date_value(exact_start)
        if exact_end:
            properties["exact_end"] = date_value(exact_end)
        page = self.create_page(self.dbs.responses, properties)
        return self._normalize_response(page)

    def create_session(
        self,
        *,
        title: str,
        event_id: str,
        chapter_id: str,
        created_by: str,
        start_at: str = "",
        end_at: str = "",
        capacity_target: int = 0,
        notes: str = "",
        status: str = "proposed",
    ) -> Dict[str, Any]:
        props: Dict[str, Any] = {
            self.get_title_prop(self.dbs.sessions): title_text(title),
            "event": relation([event_id]),
            "chapter": relation([chapter_id]),
            "created_by": relation([created_by]),
            "status": select(status),
            "capacity_target": number_value(capacity_target),
            "notes": rich_text(notes),
            "generated_from": rich_text("host"),
            "created_at": date_value(),
        }
        if start_at:
            props["start_at"] = date_value(start_at)
        if end_at:
            props["end_at"] = date_value(end_at)
        page = self.create_page(self.dbs.sessions, props)
        return self._normalize_session(page)

    def log_event(
        self,
        *,
        title: str,
        event_id: str,
        action_type: str,
        target_type: str,
        summary: str,
        actor_id: str = "",
        target_id: str = "",
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        props: Dict[str, Any] = {
            self.get_title_prop(self.dbs.event_log): title_text(title),
            "timestamp": date_value(),
            "event": relation([event_id]),
            "action_type": select(action_type),
            "target_type": select(target_type),
            "target_id": rich_text(target_id),
            "summary": rich_text(summary),
            "payload_json": rich_text(json.dumps(payload or {}, ensure_ascii=False)),
        }
        if actor_id:
            props["actor"] = relation([actor_id])
        page = self.create_page(self.dbs.event_log, props)
        return self._normalize_log(page)

    def seed_host_if_missing(self) -> Optional[Dict[str, Any]]:
        pages = self.query(
            self.dbs.players,
            filter={"property": "role", "multi_select": {"contains": "host"}},
            page_size=1,
        )
        if pages:
            return self._normalize_player(pages[0])
        return None

    def _normalize_player(self, page: Dict[str, Any]) -> Dict[str, Any]:
        props = page.get("properties", {})
        return {
            "id": str(page.get("id", "")),
            "name": _extract_text(props.get(self.get_title_prop(self.dbs.players), {})),
            "display_name": _extract_text(props.get(self.get_title_prop(self.dbs.players), {})),
            "access_key": _extract_text(props.get("access_key", {})),
            "emoji_signature": _extract_text(props.get("emoji_signature", {})),
            "anonymous_name": _extract_text(props.get("anonymous_name", {})),
            "roles": _extract_multi_select(props.get("role", {})),
            "onboarding_state": _extract_select(props.get("onboarding_state", {})),
            "contact_channel": _extract_select(props.get("contact_channel", {})),
            "contact_value": _extract_text(props.get("contact_value", {})),
            "can_lift": _extract_checkbox(props.get("can_lift", {})),
            "can_sort": _extract_checkbox(props.get("can_sort", {})),
            "can_tools": _extract_checkbox(props.get("can_tools", {})),
            "can_cook": _extract_checkbox(props.get("can_cook", {})),
            "light_tasks_only": _extract_checkbox(props.get("light_tasks_only", {})),
        }

    def _normalize_event(self, page: Dict[str, Any]) -> Dict[str, Any]:
        props = page.get("properties", {})
        return {
            "id": str(page.get("id", "")),
            "name": _extract_text(props.get(self.get_title_prop(self.dbs.events), {})),
            "slug": _extract_text(props.get("slug", {})),
            "event_type": _extract_select(props.get("event_type", {})),
            "status": _extract_select(props.get("status", {})),
            "location": _extract_text(props.get("location", {})),
            "description": _extract_text(props.get("description", {})),
            "active": _extract_checkbox(props.get("active", {})),
        }

    def _normalize_chapter(self, page: Dict[str, Any]) -> Dict[str, Any]:
        props = page.get("properties", {})
        full_name = _extract_text(props.get(self.get_title_prop(self.dbs.chapters), {}))
        emoji = _extract_text(props.get("emoji", {}))
        name = full_name
        if emoji and full_name.startswith(f"{emoji} "):
            name = full_name[len(emoji) + 1 :]
        return {
            "id": str(page.get("id", "")),
            "name": name,
            "full_name": full_name,
            "emoji": emoji,
            "slug": _extract_text(props.get("slug", {})),
            "description": _extract_text(props.get("description", {})),
            "projection_label": _extract_text(props.get("projection_label", {})),
            "target_people": int(_extract_number(props.get("target_people", {})) or 0),
            "needs_followup": _extract_checkbox(props.get("needs_followup", {})),
        }

    def _normalize_question(self, page: Dict[str, Any]) -> Dict[str, Any]:
        props = page.get("properties", {})
        options = _extract_text(props.get("choice_options_json", {}))
        try:
            parsed_options = json.loads(options) if options else []
        except Exception:
            parsed_options = []
        return {
            "id": str(page.get("id", "")),
            "name": _extract_text(props.get(self.get_title_prop(self.dbs.questions), {})),
            "kind": _extract_select(props.get("kind", {})),
            "prompt": _extract_text(props.get("prompt", {})),
            "input_type": _extract_select(props.get("input_type", {})),
            "choice_options": parsed_options,
            "required": _extract_checkbox(props.get("required", {})),
            "active": _extract_checkbox(props.get("active", {})),
            "step_order": int(_extract_number(props.get("step_order", {})) or 0),
            "visibility": _extract_select(props.get("visibility", {})),
            "help_text": _extract_text(props.get("help_text", {})),
            "chapter_ids": _extract_relation_ids(props.get("chapter", {})),
        }

    def _normalize_response(self, page: Dict[str, Any]) -> Dict[str, Any]:
        props = page.get("properties", {})
        payload_json_text = _extract_text(props.get("payload_json", {}))
        try:
            payload_json_value = json.loads(payload_json_text) if payload_json_text else {}
        except Exception:
            payload_json_value = {}
        chapter_ids = _extract_relation_ids(props.get("chapter", {}))
        question_ids = _extract_relation_ids(props.get("question", {}))
        player_ids = _extract_relation_ids(props.get("player", {}))
        return {
            "id": str(page.get("id", "")),
            "name": _extract_text(props.get(self.get_title_prop(self.dbs.responses), {})),
            "player_id": player_ids[0] if player_ids else "",
            "event_id": (_extract_relation_ids(props.get("event", {})) or [""])[0],
            "chapter_id": chapter_ids[0] if chapter_ids else "",
            "chapter_slug": payload_json_value.get("chapter_slug", ""),
            "question_id": question_ids[0] if question_ids else "",
            "response_type": _extract_select(props.get("response_type", {})),
            "payload_text": _extract_text(props.get("payload_text", {})),
            "payload_json": payload_json_value,
            "availability_bucket": _extract_multi_select(props.get("availability_bucket", {})),
            "exact_start": _extract_date(props.get("exact_start", {})),
            "exact_end": _extract_date(props.get("exact_end", {})),
            "signal_strength": _extract_select(props.get("signal_strength", {})),
            "visibility": _extract_select(props.get("visibility", {})),
            "submitted_at": _extract_date(props.get("submitted_at", {})),
            "source": _extract_select(props.get("source", {})),
        }

    def _normalize_session(self, page: Dict[str, Any]) -> Dict[str, Any]:
        props = page.get("properties", {})
        return {
            "id": str(page.get("id", "")),
            "name": _extract_text(props.get(self.get_title_prop(self.dbs.sessions), {})),
            "status": _extract_select(props.get("status", {})),
            "start_at": _extract_date(props.get("start_at", {})),
            "end_at": _extract_date(props.get("end_at", {})),
            "capacity_target": int(_extract_number(props.get("capacity_target", {})) or 0),
            "notes": _extract_text(props.get("notes", {})),
        }

    def _normalize_log(self, page: Dict[str, Any]) -> Dict[str, Any]:
        props = page.get("properties", {})
        return {
            "id": str(page.get("id", "")),
            "name": _extract_text(props.get(self.get_title_prop(self.dbs.event_log), {})),
            "timestamp": _extract_date(props.get("timestamp", {})),
            "action_type": _extract_select(props.get("action_type", {})),
            "target_type": _extract_select(props.get("target_type", {})),
            "summary": _extract_text(props.get("summary", {})),
        }

    def inspect_database(self, label: str, db_id: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "label": label,
            "database_id": db_id,
            "clean_database_id": clean_notion_id(db_id),
            "data_source_id": "",
            "database_title_prop": "",
            "database_retrieve_ok": False,
            "data_source_retrieve_ok": False,
            "query_ok": False,
            "database_error": "",
            "data_source_error": "",
            "query_error": "",
        }
        if not self.client:
            result["database_error"] = self.unavailable_reason or "Notion client unavailable."
            return result

        try:
            db_payload = self.retrieve_db(db_id)
            result["database_retrieve_ok"] = True
            props = db_payload.get("properties") or {}
            for name, spec in props.items():
                if spec.get("type") == "title":
                    result["database_title_prop"] = name
                    break
        except Exception as error:
            result["database_error"] = str(error)

        try:
            ds_id = _resolve_data_source_id(self.client, db_id)
            result["data_source_id"] = ds_id
            ds_endpoint = getattr(self.client, "data_sources", None)
            ds_retrieve = getattr(ds_endpoint, "retrieve", None) if ds_endpoint else None
            if callable(ds_retrieve):
                _execute_with_retry(ds_retrieve, data_source_id=ds_id)
                result["data_source_retrieve_ok"] = True
        except Exception as error:
            result["data_source_error"] = str(error)

        try:
            self.query(db_id, page_size=1)
            result["query_ok"] = True
        except Exception as error:
            result["query_error"] = str(error)

        return result


def init_repo(settings: AppSettings) -> EvenzRepo:
    return EvenzRepo(settings)
