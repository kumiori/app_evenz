from __future__ import annotations

import streamlit as st

from app.components import inject_evenz_styles, soft_header
from app.config import load_settings
from app.flow import init_participant_state
from app.key_codec import normalize_access_key
from app.notion_client import init_repo


@st.cache_resource(show_spinner=False)
def get_repo():
    return init_repo(load_settings())


def main() -> None:
    st.set_page_config(page_title="Feedback", page_icon="📝", layout="centered")
    inject_evenz_styles()
    init_participant_state()

    repo = get_repo()
    if not repo.is_ready():
        st.error(repo.unavailable_reason or "Evenz is not configured.")
        return

    event = repo.get_current_event()
    if not event:
        st.error("No active event found.")
        return

    soft_header("After the session", "A short reflection, nothing heavy.")

    access_key = st.text_input("Access key", value=st.session_state.get("evenz_access_key", ""))
    feedback = st.text_area("What did this moment move, lighten, or reveal?")
    energy = st.select_slider("Energy", options=["low", "medium", "high"], value="medium")

    if st.button("Send feedback", use_container_width=True):
        try:
            canonical = normalize_access_key(access_key)
        except ValueError as error:
            st.error(str(error))
            st.stop()
        player = repo.get_player_by_access_key(canonical)
        if not player:
            st.error("This key was not found.")
            st.stop()

        question = next((item for item in repo.list_questions(event["id"], kind="feedback") if item["kind"] == "feedback"), None)
        repo.create_response(
            title=f'Feedback · {player["display_name"]}',
            player_id=player["id"],
            event_id=event["id"],
            question_id=question["id"] if question else "",
            response_type="feedback",
            payload_text_value=feedback,
            payload_json_value={"feedback": feedback, "energy": energy},
            visibility_value="host",
            signal_strength=energy,
        )
        repo.log_event(
            title=f'Feedback · {player["display_name"]}',
            event_id=event["id"],
            actor_id=player["id"],
            action_type="submit_feedback",
            target_type="response",
            target_id=player["id"],
            summary="Participant submitted feedback.",
            payload={"energy": energy},
        )
        st.success("Feedback saved.")


if __name__ == "__main__":
    main()
