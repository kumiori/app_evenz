from __future__ import annotations

import streamlit as st

from app.analytics import build_coverage
from app.components import inject_evenz_styles, metric_card, soft_header
from app.config import load_settings
from app.copy import PROJECTION_TITLE
from app.notion_client import init_repo


@st.cache_resource(show_spinner=False)
def get_repo():
    return init_repo(load_settings())


def main() -> None:
    st.set_page_config(page_title="Projection", page_icon="✨", layout="wide")
    inject_evenz_styles()

    repo = get_repo()
    if not repo.is_ready():
        st.error(repo.unavailable_reason or "Evenz is not configured.")
        return

    event = repo.get_current_event()
    if not event:
        st.error("No active event found.")
        return

    responses = repo.list_responses(event["id"])
    chapters = repo.list_chapters(event["id"])
    coverage = build_coverage(chapters, responses)

    soft_header(PROJECTION_TITLE, "A calm public board. Counts and needs only.")

    cols = st.columns(3)
    for index, chapter in enumerate(coverage["chapters"]):
        with cols[index % 3]:
            body = f'{chapter["interested_count"]} signals'
            if chapter["needs"]:
                body += f'<br/>Still calling for: {", ".join(chapter["needs"][:2])}'
            metric_card(chapter["name"], body, accent=chapter["emoji"])

    needs = []
    for chapter in coverage["chapters"]:
        for need in chapter["needs"]:
            needs.append(f'{chapter["emoji"]} {need}')

    st.subheader("Still calling for")
    if needs:
        for line in needs[:6]:
            st.markdown(f"- {line}")
    else:
        st.caption("The field looks covered for now.")


if __name__ == "__main__":
    main()
