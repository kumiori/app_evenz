from __future__ import annotations

import streamlit as st

from app.components import inject_evenz_styles, soft_header
from app.i18n import available_languages, setup_translation, translation_info


TEST_STRINGS = [
    "Welcome to Our App",
    "This app is designed to demonstrate i18n in Streamlit.",
    "Click here to proceed",
    "Hello, World!",
    "Kitchen",
    "Plants",
    "Clothes",
    "Books",
    "Art / archives",
    "This weekend",
    "Weekday evening, dinner included",
    "Next week",
    "Flexible",
    "I can carry",
    "I can sort",
    "I can assemble",
    "I can bring tools",
    "I can cook",
    "I can be creative",
    "I like to be given tasks",
    "I prefer light tasks",
    "I mostly come for presence and tea",
    "Store your helper key",
]


def main() -> None:
    st.set_page_config(page_title="Test i18n", page_icon="🌍", layout="centered")
    inject_evenz_styles()

    soft_header(
        "Test i18n",
        "Switch languages, verify compiled catalogs, and inspect how the current locale resolves known msgids.",
    )

    languages = available_languages()
    selected_language = st.selectbox("Language", languages, index=0)
    _ = setup_translation(selected_language)

    st.subheader("Catalog status")
    info = translation_info(selected_language)
    st.write(info)
    if not info["po_exists"]:
        st.error("No messages.po file found for this locale.")
    elif not info["mo_exists"]:
        st.warning("messages.po exists, but messages.mo is missing. gettext will fall back until you compile the catalog.")

    st.subheader("Live rendering")
    st.title(_("Welcome to Our App"))
    st.write(_("This app is designed to demonstrate i18n in Streamlit."))
    st.button(_("Click here to proceed"))
    st.code(_("Hello, World!"), language="text")

    st.subheader("String table")
    st.dataframe(
        [{"msgid": text, "translated": _(text)} for text in TEST_STRINGS],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Fallback check")
    fallback = "This key does not exist in the catalog."
    st.write({"msgid": fallback, "resolved": _(fallback)})


if __name__ == "__main__":
    main()
