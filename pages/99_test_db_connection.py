from __future__ import annotations

import json

import streamlit as st

from app.components import inject_evenz_styles, soft_header
from app.config import load_settings
from app.notion_client import init_repo


@st.cache_resource(show_spinner=False)
def get_repo():
    return init_repo(load_settings())


def get_fresh_repo_if_needed():
    settings = load_settings()
    repo = get_repo()
    if not hasattr(repo, "inspect_database"):
        return init_repo(settings)
    return repo


def main() -> None:
    st.set_page_config(page_title="Test DB connection", page_icon="🧪", layout="wide")
    inject_evenz_styles()

    settings = load_settings()
    repo = get_fresh_repo_if_needed()

    soft_header(
        "Test DB connection",
        "Inspect raw Notion access: token presence, database ids, data source resolution, and query status.",
    )

    st.subheader("Environment")
    st.write(
        {
            "repo_ready": repo.is_ready(),
            "unavailable_reason": repo.unavailable_reason,
            "notion_version": settings.notion_version,
            "event_slug": settings.event_slug,
            "has_inspect_database": hasattr(repo, "inspect_database"),
        }
    )

    dbs = {
        "players": settings.dbs.players,
        "events": settings.dbs.events,
        "chapters": settings.dbs.chapters,
        "questions": settings.dbs.questions,
        "responses": settings.dbs.responses,
        "sessions": settings.dbs.sessions,
        "event_log": settings.dbs.event_log,
    }

    st.subheader("Configured database ids")
    st.code(json.dumps(dbs, indent=2), language="json")

    if not repo.is_ready():
        st.warning(repo.unavailable_reason or "Evenz is not ready.")
        return

    st.subheader("Per-database diagnostics")
    rows = [repo.inspect_database(label, db_id) for label, db_id in dbs.items()]
    st.dataframe(rows, use_container_width=True, hide_index=True)

    st.subheader("Event lookup")
    try:
        event = repo.get_current_event()
        st.success("Event lookup completed.")
        st.write(event)
    except Exception as error:
        st.error(str(error))

    st.subheader("Sharing reminder")
    st.markdown(
        """
        - Open each Notion database page.
        - Click `Share`.
        - Invite the integration `fuckthesystem`.
        - Confirm the exact database ids match the ones configured here.
        """
    )


if __name__ == "__main__":
    main()
