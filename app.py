from __future__ import annotations

import streamlit as st

from app.components import inject_evenz_styles, soft_header
from app.config import load_settings
from app.notion_client import init_repo


@st.cache_resource(show_spinner=False)
def get_repo():
    return init_repo(load_settings())


def main() -> None:
    st.set_page_config(
        page_title="evenz",
        page_icon="🏠",
        layout="centered",
    )
    inject_evenz_styles()

    settings = load_settings()
    repo = get_repo()

    soft_header(
        "evenz",
        "A warm coordination ritual for reopening, shared help, and chapter-based sessions.",
    )
    st.caption(
        "Parts of these texts have been AI-assisted. Reach out to improve the wording."
    )

    st.page_link("pages/01_base.py", label="Base", icon="🌿")
    st.page_link("pages/02_host.py", label="Host console", icon="🧭")
    st.page_link("pages/03_projection.py", label="Projection view", icon="✨")
    st.page_link("pages/04_feedback.py", label="Feedback", icon="📝")
    st.page_link("pages/05_library.py", label="Base library", icon="📚")
    st.page_link("pages/98_test_i18n.py", label="Test i18n", icon="🌍")
    st.page_link("pages/99_test_db_connection.py", label="Test DB connection", icon="🧪")

    if not repo.is_ready():
        st.warning(repo.unavailable_reason or "Evenz is not configured yet.")
        return

    try:
        event = repo.get_current_event()
    except Exception as error:
        st.error(f"Notion connection error: {error}")
        st.info("Use `Test DB connection` to inspect database access and sharing.")
        return

    if not event:
        st.error("No active event found. Run the bootstrap script first, or inspect the DB connection page.")
        return

    st.markdown(
        f"""
        <div class="base-note">
            <strong>{event["name"]}</strong><br/>
            {event.get("description", "")}
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
