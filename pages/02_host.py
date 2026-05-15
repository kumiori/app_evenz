from __future__ import annotations

import streamlit as st

from app.analytics import build_coverage, candidate_sessions, recent_activity, whatsapp_summary
from app.components import inject_evenz_styles, metric_card, soft_header
from app.config import load_settings
from app.notion_client import init_repo


@st.cache_resource(show_spinner=False)
def get_repo():
    return init_repo(load_settings())


def main() -> None:
    st.set_page_config(page_title="Host", page_icon="🧭", layout="wide")
    inject_evenz_styles()

    repo = get_repo()
    if not repo.is_ready():
        st.error(repo.unavailable_reason or "Evenz is not configured.")
        return

    event = repo.get_current_event()
    if not event:
        st.error("No event found.")
        return

    chapters = repo.list_chapters(event["id"])
    responses = repo.list_responses(event["id"])
    sessions = repo.list_sessions(event["id"])
    players = repo.list_players()
    coverage = build_coverage(chapters, responses)
    candidates = candidate_sessions(coverage)

    soft_header("Host console", "Coverage, chapter gaps, candidate sessions, and a quick WhatsApp summary.")

    top_cols = st.columns(4)
    with top_cols[0]:
        metric_card("Participants", str(len(players)))
    with top_cols[1]:
        metric_card("Responses", str(len(responses)))
    with top_cols[2]:
        metric_card("Chapters", str(len(chapters)))
    with top_cols[3]:
        metric_card("Sessions", str(len(sessions)))

    st.subheader("Chapter coverage")
    chapter_cols = st.columns(2)
    for index, chapter in enumerate(coverage["chapters"]):
        with chapter_cols[index % 2]:
            body = (
                f'{chapter["interested_count"]} interested'
                f'<br/>{chapter["best_bucket_count"]} in {chapter["best_bucket_label"] or "no overlap yet"}'
            )
            if chapter["needs"]:
                body += f'<br/>Needs: {", ".join(chapter["needs"][:3])}'
            metric_card(chapter["name"], body, accent=chapter["emoji"])

    st.subheader("Candidate sessions")
    if candidates:
        for candidate in candidates:
            st.markdown(f'- **{candidate["title"]}**: {candidate["body"]}')
    else:
        st.caption("No overlap is strong enough yet.")

    st.subheader("Create suggested session")
    chapter_options = {f'{chapter["emoji"]} {chapter["name"]}': chapter for chapter in chapters}
    with st.form("create-session"):
        chapter_label = st.selectbox("Chapter", list(chapter_options.keys()))
        title = st.text_input("Title", value=f'{chapter_label} · Session')
        start_at = st.text_input("Start at, optional", placeholder="2026-05-17T14:00:00")
        end_at = st.text_input("End at, optional", placeholder="2026-05-17T16:00:00")
        capacity_target = st.number_input("Capacity target", min_value=0, max_value=12, value=3)
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Create session")

    if submitted:
        host = next((player for player in players if "host" in player.get("roles", [])), None)
        chapter = chapter_options[chapter_label]
        session = repo.create_session(
            title=title,
            event_id=event["id"],
            chapter_id=chapter["id"],
            created_by=host["id"] if host else "",
            start_at=start_at.strip(),
            end_at=end_at.strip(),
            capacity_target=int(capacity_target),
            notes=notes,
        )
        repo.log_event(
            title=f"Create session · {title}",
            event_id=event["id"],
            actor_id=host["id"] if host else "",
            action_type="create_session",
            target_type="session",
            target_id=session["id"],
            summary=f"Host created session {title}.",
            payload={"chapter": chapter["slug"]},
        )
        st.success(f"Created session: {session['name']}")

    st.subheader("Recent activity")
    activity = recent_activity(responses, limit=12)
    if activity:
        st.dataframe(
            [
                {
                    "when": item.get("submitted_at", ""),
                    "type": item.get("response_type", ""),
                    "text": item.get("payload_text", ""),
                    "visibility": item.get("visibility", ""),
                }
                for item in activity
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No activity yet.")

    st.subheader("WhatsApp summary")
    summary = whatsapp_summary(coverage, sessions)
    st.code(summary, language="text")


if __name__ == "__main__":
    main()
