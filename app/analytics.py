from __future__ import annotations

import json
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Tuple


AVAILABILITY_LABELS = {
    "this_weekend": "this weekend",
    "weekday_evening": "weekday evening",
    "next_week": "next week",
    "flexible": "flexible",
}

CAPACITY_LABELS = {
    "carry": "carrying hands",
    "sort": "sorting help",
    "assemble": "assembly help",
    "tools": "tools",
    "cook": "cooking",
    "light_tasks_only": "light tasks only",
    "presence_and_tea": "presence and tea",
    "repot": "repotting",
    "bring_soil": "pots / soil",
    "clean": "cleaning after install",
    "carry_boxes": "box carrying",
    "delicate_handling": "delicate handling",
}


def _parse_payload(response: Dict[str, Any]) -> Dict[str, Any]:
    payload = response.get("payload_json")
    if isinstance(payload, dict):
        return payload
    if not payload:
        return {}
    try:
        return json.loads(str(payload))
    except Exception:
        return {}


def latest_response_index(responses: Iterable[Dict[str, Any]]) -> Dict[Tuple[str, str, str], Dict[str, Any]]:
    ordered = sorted(
        responses,
        key=lambda item: item.get("submitted_at") or "",
        reverse=True,
    )
    latest: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    for response in ordered:
        player_id = str(response.get("player_id") or "")
        response_type = str(response.get("response_type") or "")
        chapter_slug = str(response.get("chapter_slug") or "")
        key = (player_id, response_type, chapter_slug)
        if key not in latest:
            latest[key] = response
    return latest


def build_coverage(chapters: List[Dict[str, Any]], responses: List[Dict[str, Any]]) -> Dict[str, Any]:
    latest = latest_response_index(responses)
    availability_by_player: Dict[str, List[str]] = {}
    capacities_by_player: Dict[str, List[str]] = {}

    for (player_id, response_type, _), response in latest.items():
        payload = _parse_payload(response)
        if response_type == "availability":
            buckets = response.get("availability_bucket") or payload.get("availability") or []
            availability_by_player[player_id] = list(buckets)
        elif response_type == "capacity":
            capacities_by_player[player_id] = list(payload.get("capacities") or [])

    chapter_rows: List[Dict[str, Any]] = []
    interested_players_by_chapter: Dict[str, List[str]] = defaultdict(list)

    for (player_id, response_type, chapter_slug), response in latest.items():
        if response_type != "interest" or not chapter_slug:
            continue
        interested_players_by_chapter[chapter_slug].append(player_id)

    for chapter in chapters:
        slug = str(chapter.get("slug") or "")
        players = sorted(set(interested_players_by_chapter.get(slug, [])))
        availability_counts = Counter()
        capacity_counts = Counter()

        for player_id in players:
            for bucket in availability_by_player.get(player_id, []):
                availability_counts[bucket] += 1
            for capacity in capacities_by_player.get(player_id, []):
                capacity_counts[capacity] += 1

        best_bucket = ""
        best_count = 0
        if availability_counts:
            best_bucket, best_count = availability_counts.most_common(1)[0]

        needs: List[str] = []
        target_people = int(chapter.get("target_people") or 0)
        if target_people and len(players) < target_people:
            needs.append(f"{target_people - len(players)} more signal(s)")
        if capacity_counts.get("carry", 0) == 0:
            needs.append("carrying hands")
        if slug == "plants" and capacity_counts.get("bring_soil", 0) == 0:
            needs.append("pots / soil")
        if slug == "kitchen" and capacity_counts.get("assemble", 0) == 0:
            needs.append("install help")

        chapter_rows.append(
            {
                "slug": slug,
                "name": chapter.get("name", slug),
                "emoji": chapter.get("emoji", ""),
                "projection_label": chapter.get("projection_label", ""),
                "interested_count": len(players),
                "players": players,
                "availability_counts": dict(availability_counts),
                "capacity_counts": dict(capacity_counts),
                "best_bucket": best_bucket,
                "best_bucket_label": AVAILABILITY_LABELS.get(best_bucket, ""),
                "best_bucket_count": best_count,
                "needs": needs,
            }
        )

    total_players = len({str(response.get("player_id") or "") for response in responses if response.get("player_id")})
    return {
        "total_players": total_players,
        "chapters": chapter_rows,
    }


def candidate_sessions(coverage: Dict[str, Any]) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for chapter in coverage.get("chapters", []):
        if chapter["interested_count"] == 0:
            continue
        if chapter["best_bucket"]:
            label = chapter["best_bucket_label"]
            title = f'{chapter["name"]} · {label.title()}'
            body = (
                f'{chapter["interested_count"]} interested, '
                f'{chapter["best_bucket_count"]} aligned on {label}.'
            )
            candidates.append(
                {
                    "slug": chapter["slug"],
                    "title": title,
                    "body": body,
                }
            )
    return candidates


def recent_activity(responses: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
    ordered = sorted(responses, key=lambda item: item.get("submitted_at") or "", reverse=True)
    return ordered[:limit]


def whatsapp_summary(coverage: Dict[str, Any], sessions: List[Dict[str, Any]]) -> str:
    lines = ["The Base moves forward", ""]
    for chapter in coverage.get("chapters", []):
        line = (
            f'{chapter["emoji"]} {chapter["name"]}: {chapter["interested_count"]} interested'
        )
        if chapter["best_bucket_label"]:
            line += f', best overlap: {chapter["best_bucket_label"]}'
        lines.append(line)
    if sessions:
        lines.append("")
        lines.append("Host-created sessions:")
        for session in sessions:
            status = session.get("status", "proposed")
            lines.append(f'- {session.get("name", "Untitled")} ({status})')
    return "\n".join(lines)
