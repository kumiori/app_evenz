from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd
import streamlit as st

from app.components import (
    editorial_paragraph,
    inject_evenz_styles,
    rhythm_gap,
    soft_header,
    summary_block,
)
from app.flow import get_draft
from app.key_codec import key_to_emoji_suffix


ASSET_PATH = (
    Path(__file__).resolve().parents[1] / "assets" / "base-Bookshelf-2026-05-16.csv"
)


def _library_styles() -> None:
    st.markdown(
        """
        <style>
        .library-toolbar {
            margin: 0 0 1.25rem 0;
        }
        .library-toolbar [data-testid="stPills"] button {
            min-height: 3.2rem !important;
            padding: 0.7rem 1rem !important;
            border-radius: 999px !important;
            justify-content: center !important;
            background: rgba(17, 22, 31, 0.92) !important;
        }
        .library-toolbar [data-testid="stPills"] button p,
        .library-toolbar [data-testid="stPills"] button span,
        .library-toolbar [data-testid="stPills"] button div {
            font-size: 0.95rem !important;
            line-height: 1.2 !important;
        }
        .library-toolbar [data-testid="stSegmentedControl"] button {
            min-height: 3.2rem !important;
            padding: 0.7rem 1rem !important;
            border-radius: 999px !important;
        }
        .library-toolbar [data-testid="stSegmentedControl"] button p,
        .library-toolbar [data-testid="stSegmentedControl"] button span,
        .library-toolbar [data-testid="stSegmentedControl"] button div {
            font-size: 0.95rem !important;
        }
        .library-grid-title {
            margin: 0 0 1rem 0;
            opacity: .76;
            font-size: .92rem;
            letter-spacing: .04em;
            text-transform: uppercase;
        }
        .library-card {
            border: 1px solid rgba(255,255,255,.10);
            background:
                radial-gradient(circle at top right, rgba(255,255,255,.035), transparent 28%),
                rgba(255,255,255,.04);
            border-radius: 24px;
            padding: 1.2rem 1.2rem 1.05rem;
            min-height: 13rem;
        }
        .library-card.resonating {
            border-color: rgba(255,86,92,.46);
            background:
                radial-gradient(circle at top right, rgba(255,86,92,.08), transparent 28%),
                rgba(132,38,44,.14);
        }
        .library-card h3 {
            margin: 0 0 .55rem 0;
            font-size: 1.35rem;
            line-height: 1.12;
            letter-spacing: -0.03em;
        }
        .library-card .author {
            font-size: 1rem;
            opacity: .84;
            line-height: 1.35;
            margin-bottom: .8rem;
        }
        .library-card .meta {
            font-size: .88rem;
            opacity: .68;
            line-height: 1.45;
            margin-bottom: .8rem;
        }
        .library-card .desc {
            font-size: .95rem;
            line-height: 1.55;
            opacity: .78;
            display: -webkit-box;
            -webkit-line-clamp: 4;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        .library-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: .45rem;
            margin-bottom: .8rem;
        }
        .library-chip {
            border-radius: 999px;
            padding: .3rem .6rem;
            font-size: .78rem;
            line-height: 1;
            border: 1px solid rgba(255,255,255,.12);
            background: rgba(255,255,255,.05);
            color: rgba(244,241,232,.92);
        }
        .library-chip.accent {
            border-color: rgba(255,86,92,.5);
            background: rgba(132,38,44,.26);
            color: #ff6c70;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _short_emoji_from_access_key(raw_key: str) -> str:
    try:
        return key_to_emoji_suffix(raw_key, 4)
    except ValueError:
        return ""


@st.cache_data(show_spinner=False)
def load_library() -> pd.DataFrame:
    frame = pd.read_csv(ASSET_PATH)
    frame = frame.fillna("")
    frame["Page Count"] = pd.to_numeric(frame["Page Count"], errors="coerce")
    frame["Published At"] = pd.to_datetime(frame["Published At"], errors="coerce")
    frame["Date added"] = pd.to_datetime(frame["Date added"], errors="coerce")
    frame["Read"] = frame["Read"].astype(str).eq("1")
    frame["Wishlist"] = frame["Wishlist"].astype(str).eq("1")
    frame["Signed"] = frame["Signed"].astype(str).eq("1")
    frame["display_author"] = frame["Authors"].replace("", "Unknown author")
    frame["display_language"] = frame["Language"].replace("", "unknown")
    frame["display_shelf"] = frame["Bookshelf"].str.strip().replace("", "Shelf")
    frame["display_format"] = frame["Format"].replace("", "book")
    frame["display_categories"] = frame["Categories"].replace("", "")
    frame["display_description"] = frame["Description"].replace("", "")
    frame["published_year"] = frame["Published At"].dt.year.fillna(0).astype(int)
    return frame


def _format_book_count(value: int) -> str:
    return f"{value} book" if value == 1 else f"{value} books"


def _filter_pills(
    label: str, options: List[str], key: str, default: str = "All"
) -> str:
    selected = st.pills(
        label,
        options,
        selection_mode="single",
        default=st.session_state.get(
            key, default if default in options else options[0]
        ),
        key=key,
        label_visibility="collapsed",
    )
    return str(selected or default)


def _sort_segmented(options: List[str], key: str, default: str) -> str:
    selected = st.segmented_control(
        "Sort",
        options,
        default=st.session_state.get(key, default),
        key=key,
        label_visibility="collapsed",
    )
    return str(selected or default)


def _apply_filters(
    frame: pd.DataFrame, shelf: str, language: str, status: str
) -> pd.DataFrame:
    filtered = frame.copy()
    if shelf != "All shelves":
        filtered = filtered[filtered["display_shelf"] == shelf]
    if language != "All languages":
        filtered = filtered[filtered["display_language"] == language]
    if status == "Read":
        filtered = filtered[filtered["Read"]]
    elif status == "Unread":
        filtered = filtered[~filtered["Read"]]
    elif status == "Wishlist":
        filtered = filtered[filtered["Wishlist"]]
    elif status == "Signed":
        filtered = filtered[filtered["Signed"]]
    return filtered


def _apply_sort(frame: pd.DataFrame, sort_mode: str) -> pd.DataFrame:
    if sort_mode == "Recently added":
        return frame.sort_values(
            ["Date added", "Title"], ascending=[False, True], na_position="last"
        )
    if sort_mode == "Title":
        return frame.sort_values(
            ["Title", "display_author"], ascending=[True, True], na_position="last"
        )
    if sort_mode == "Author":
        return frame.sort_values(
            ["display_author", "Title"], ascending=[True, True], na_position="last"
        )
    if sort_mode == "Published":
        return frame.sort_values(
            ["Published At", "Title"], ascending=[False, True], na_position="last"
        )
    if sort_mode == "Length":
        return frame.sort_values(
            ["Page Count", "Title"], ascending=[False, True], na_position="last"
        )
    return frame


def _toggle_signal(book_id: str) -> None:
    current = list(st.session_state.get("library_signals", []))
    if book_id in current:
        current = [item for item in current if item != book_id]
    else:
        current.append(book_id)
    st.session_state["library_signals"] = current


def _render_book_card(book: Dict[str, object], signaled: bool = False) -> None:
    chips: List[str] = []
    if book.get("display_shelf"):
        chips.append(f'<span class="library-chip">{book["display_shelf"]}</span>')
    if book.get("display_language"):
        chips.append(
            f'<span class="library-chip">{str(book["display_language"]).upper()}</span>'
        )
    if book.get("display_format"):
        chips.append(f'<span class="library-chip">{book["display_format"]}</span>')
    if bool(book.get("Read")):
        chips.append('<span class="library-chip accent">read</span>')
    if bool(book.get("Wishlist")):
        chips.append('<span class="library-chip accent">wishlist</span>')
    if bool(book.get("Signed")):
        chips.append('<span class="library-chip accent">signed</span>')
    if signaled:
        chips.append('<span class="library-chip accent">resonating</span>')

    year = int(book.get("published_year") or 0)
    year_text = str(year) if year > 0 else "undated"
    pages = book.get("Page Count")
    pages_text = f"{int(pages)} pages" if pd.notna(pages) and pages else ""
    publisher = str(book.get("Publisher") or "").strip()
    meta_parts = [part for part in [year_text, pages_text, publisher] if part]
    meta_text = " · ".join(meta_parts)
    subtitle = str(book.get("Subtitle") or "").strip()
    description = str(book.get("display_description") or "").strip()
    excerpt = (
        description or subtitle or str(book.get("display_categories") or "").strip()
    )
    excerpt = (
        excerpt
        if excerpt
        else "A quiet object on the shelf, waiting for its next reader."
    )

    st.markdown(
        f"""
        <div class="library-card {"resonating" if signaled else ""}">
            <h3>{book["Title"]}</h3>
            <div class="author">{book["display_author"]}</div>
            <div class="library-chip-row">{"".join(chips)}</div>
            <div class="meta">{meta_text}</div>
            <div class="desc">{excerpt}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Library", page_icon="📚", layout="centered")
    inject_evenz_styles()
    _library_styles()

    books = load_library()
    st.session_state.setdefault("library_signals", [])
    draft = get_draft()
    is_logged_in = bool(
        st.session_state.get("evenz_authenticated_access_key")
        or draft.get("access_key")
        or draft.get("existing_player_id")
    )

    soft_header(
        "Base Library",
        "Many shelves: philosophy, poetry, non-fiction, fiction, social thought, manuals, and food trips.",
        step="library",
    )
    editorial_paragraph(
        "Use the pills to slice the shelf quickly, then wander through the cards. This is not a database view, it is a browsing surface."
    )
    if is_logged_in:
        editorial_paragraph(
            "Tap Signal on anything that may resonate. It is a light way of marking what you may want to dig later."
        )
    else:
        editorial_paragraph(
            "Have a look around. To signal a book, log in with your emoji key first."
        )
        if st.button("Log in to signal", use_container_width=True):
            st.session_state["evenz_post_login_target"] = "pages/05_library.py"
            short_emoji = _short_emoji_from_access_key(str(draft.get("access_key") or ""))
            if short_emoji:
                st.session_state["evenz_login_short_emoji_prefill"] = short_emoji
            st.switch_page("pages/00_login.py")

    total_books = len(books)
    read_books = int(books["Read"].sum())
    languages = sorted(
        [value for value in books["display_language"].unique().tolist() if value]
    )
    shelves = sorted(
        [value for value in books["display_shelf"].unique().tolist() if value]
    )

    summary_block(
        "Shelf pulse",
        f"{_format_book_count(total_books)} · {read_books} marked read · {len(languages)} languages · {len(shelves)} shelf states",
    )

    st.markdown('<div class="library-toolbar">', unsafe_allow_html=True)
    shelf = _filter_pills("Shelf", ["All shelves"] + shelves, "library_shelf_filter")
    language = _filter_pills(
        "Language", ["All languages"] + languages, "library_language_filter"
    )
    status = _filter_pills(
        "Status",
        ["All", "Unread", "Read", "Wishlist", "Signed"],
        "library_status_filter",
        default="All",
    )
    sort_mode = _sort_segmented(
        ["Recently added", "Title", "Author", "Published", "Length"],
        "library_sort_mode",
        default="Recently added",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    filtered = _apply_filters(books, shelf, language, status)
    filtered = _apply_sort(filtered, sort_mode)
    signaled_ids = set(st.session_state.get("library_signals", []))

    if signaled_ids:
        signaled_titles = books[books["Book Id"].astype(str).isin(signaled_ids)][
            "Title"
        ].tolist()
        preview = " · ".join(signaled_titles[:4])
        if len(signaled_titles) > 4:
            preview += " · …"
        summary_block("Resonance", preview)

    rhythm_gap(0.5)
    st.markdown(
        f'<div class="library-grid-title">{_format_book_count(len(filtered))} visible</div>',
        unsafe_allow_html=True,
    )

    rows = filtered.to_dict("records")
    for index in range(0, len(rows), 2):
        cols = st.columns(2, gap="medium")
        for column, book in zip(cols, rows[index : index + 2]):
            with column:
                book_id = str(book.get("Book Id") or "")
                is_signaled = book_id in signaled_ids
                _render_book_card(book, signaled=is_signaled)
                if st.button(
                    "Signaled" if is_signaled else "Signal",
                    key=f"library_signal_{book_id}",
                    type="primary" if is_signaled else "secondary",
                    use_container_width=True,
                    disabled=not is_logged_in,
                ):
                    _toggle_signal(book_id)
                    st.rerun()
        rhythm_gap(0.5)


if __name__ == "__main__":
    main()
