from __future__ import annotations

from typing import Any, Dict, List


AVAILABILITY_OPTIONS: List[Dict[str, str]] = [
    {"value": "this_weekend", "label": "This weekend"},
    {"value": "weekday_evening", "label": "Weekday evening"},
    {"value": "next_week", "label": "Next week"},
    {"value": "flexible", "label": "Flexible"},
]


CAPACITY_OPTIONS: List[Dict[str, str]] = [
    {"value": "carry", "label": "I can carry"},
    {"value": "sort", "label": "I can sort"},
    {"value": "assemble", "label": "I can assemble"},
    {"value": "tools", "label": "I can bring tools"},
    {"value": "cook", "label": "I can cook"},
    {"value": "light_tasks_only", "label": "I prefer light tasks"},
    {"value": "presence_and_tea", "label": "I mostly come for presence and tea"},
]


CHAPTER_SEEDS: List[Dict[str, Any]] = [
    {
        "name": "Kitchen",
        "emoji": "🍳",
        "slug": "kitchen",
        "description": "Practical help to make the kitchen functional and joyful.",
        "sort_order": 1,
        "mood": "practical",
        "needs_followup": True,
        "color_tag": "yellow",
        "target_people": 3,
    },
    {
        "name": "Plants",
        "emoji": "🪴",
        "slug": "plants",
        "description": "Repotting, cuttings, care, and plant redistribution.",
        "sort_order": 2,
        "mood": "light",
        "needs_followup": True,
        "color_tag": "green",
        "target_people": 2,
    },
    {
        "name": "Clothes",
        "emoji": "👕",
        "slug": "clothes",
        "description": "Sorting, giving, folding, choosing what stays.",
        "sort_order": 3,
        "mood": "sorting",
        "needs_followup": False,
        "color_tag": "blue",
        "target_people": 2,
    },
    {
        "name": "Books",
        "emoji": "📚",
        "slug": "books",
        "description": "Sorting, carrying, shelving, transmission, and gifts.",
        "sort_order": 4,
        "mood": "intimate",
        "needs_followup": True,
        "color_tag": "brown",
        "target_people": 3,
    },
    {
        "name": "Art / archives",
        "emoji": "🎨",
        "slug": "art_archives",
        "description": "Delicate objects, documents, images, memories, and placement.",
        "sort_order": 5,
        "mood": "delicate",
        "needs_followup": True,
        "color_tag": "pink",
        "target_people": 2,
    },
]


DEFAULT_QUESTIONS: List[Dict[str, Any]] = [
    {
        "title": "Q1 · Chapter interest",
        "kind": "chapter_interest",
        "prompt": "Which chapters call you?",
        "input_type": "multiselect",
        "choice_options_json": [
            {"slug": chapter["slug"], "label": f'{chapter["emoji"]} {chapter["name"]}'}
            for chapter in CHAPTER_SEEDS
        ],
        "required": True,
        "active": True,
        "step_order": 1,
        "visibility": "participant",
        "help_text": "Choose one or more chapters. You can refine later.",
    },
    {
        "title": "Q2 · Availability",
        "kind": "availability",
        "prompt": "When could you pass by?",
        "input_type": "multiselect",
        "choice_options_json": AVAILABILITY_OPTIONS,
        "required": True,
        "active": True,
        "step_order": 2,
        "visibility": "participant",
        "help_text": "Precise slots stay optional.",
    },
    {
        "title": "Q3 · Capacity",
        "kind": "capacity_offer",
        "prompt": "What kind of help feels good for you?",
        "input_type": "multiselect",
        "choice_options_json": CAPACITY_OPTIONS,
        "required": False,
        "active": True,
        "step_order": 3,
        "visibility": "participant",
        "help_text": "A light signal is enough.",
    },
    {
        "title": "Q4 · Notes",
        "kind": "notes",
        "prompt": "Anything I should know?",
        "input_type": "text",
        "choice_options_json": [],
        "required": False,
        "active": True,
        "step_order": 4,
        "visibility": "participant",
        "help_text": "Constraints, curiosities, desired objects, timing notes.",
    },
    {
        "title": "Q5 · Feedback",
        "kind": "feedback",
        "prompt": "What did this moment move, lighten, or reveal?",
        "input_type": "text",
        "choice_options_json": [],
        "required": False,
        "active": True,
        "step_order": 5,
        "visibility": "participant",
        "help_text": "For after the session.",
    },
]


FOLLOWUP_QUESTIONS: List[Dict[str, Any]] = [
    {
        "title": "Kitchen follow-up",
        "chapter_slug": "kitchen",
        "prompt": "Kitchen: what kind of help calls you?",
        "options": [
            "assemble",
            "clean",
            "test_appliances",
            "cook_during_session",
        ],
    },
    {
        "title": "Plants follow-up",
        "chapter_slug": "plants",
        "prompt": "Plants: what kind of help calls you?",
        "options": [
            "repot",
            "cuttings",
            "bring_soil",
            "identify_needs",
        ],
    },
    {
        "title": "Books follow-up",
        "chapter_slug": "books",
        "prompt": "Books: what kind of help calls you?",
        "options": [
            "sort",
            "carry_boxes",
            "receive_books",
            "catalogue",
        ],
    },
    {
        "title": "Art archives follow-up",
        "chapter_slug": "art_archives",
        "prompt": "Art / archives: what kind of help calls you?",
        "options": [
            "delicate_handling",
            "choose_keep_give",
            "photograph",
            "hang_place",
        ],
    },
]


PLAYER_SCHEMA: Dict[str, Any] = {
    "access_key": {"rich_text": {}},
    "access_key_hash": {"rich_text": {}},
    "access_key_last4": {"rich_text": {}},
    "emoji_signature": {"rich_text": {}},
    "anonymous_name": {"rich_text": {}},
    "contact_channel": {
        "select": {
            "options": [
                {"name": "whatsapp", "color": "green"},
                {"name": "telegram", "color": "blue"},
                {"name": "email", "color": "purple"},
                {"name": "direct", "color": "gray"},
            ]
        }
    },
    "contact_value": {"rich_text": {}},
    "role": {
        "multi_select": {
            "options": [
                {"name": "host", "color": "red"},
                {"name": "helper", "color": "green"},
                {"name": "cook", "color": "orange"},
                {"name": "driver", "color": "blue"},
                {"name": "organizer", "color": "purple"},
            ]
        }
    },
    "onboarding_state": {
        "select": {
            "options": [
                {"name": "invited", "color": "gray"},
                {"name": "identified", "color": "blue"},
                {"name": "active", "color": "green"},
                {"name": "inactive", "color": "red"},
            ]
        }
    },
    "has_car": {"checkbox": {}},
    "can_lift": {"checkbox": {}},
    "can_tools": {"checkbox": {}},
    "can_sort": {"checkbox": {}},
    "can_cook": {"checkbox": {}},
    "light_tasks_only": {"checkbox": {}},
    "notes_private": {"rich_text": {}},
    "created_at": {"date": {}},
    "last_seen_at": {"date": {}},
}


EVENT_SCHEMA: Dict[str, Any] = {
    "slug": {"rich_text": {}},
    "event_type": {
        "select": {
            "options": [
                {"name": "move", "color": "blue"},
                {"name": "dinner", "color": "orange"},
                {"name": "workshop", "color": "purple"},
                {"name": "ritual", "color": "pink"},
            ]
        }
    },
    "status": {
        "select": {
            "options": [
                {"name": "draft", "color": "gray"},
                {"name": "active", "color": "green"},
                {"name": "paused", "color": "yellow"},
                {"name": "done", "color": "blue"},
            ]
        }
    },
    "start_at": {"date": {}},
    "end_at": {"date": {}},
    "location": {"rich_text": {}},
    "description": {"rich_text": {}},
    "active": {"checkbox": {}},
    "projection_mode": {"checkbox": {}},
    "visibility": {
        "select": {
            "options": [
                {"name": "private", "color": "gray"},
                {"name": "link", "color": "blue"},
                {"name": "projection", "color": "green"},
            ]
        }
    },
    "default_language": {
        "select": {
            "options": [
                {"name": "fr", "color": "blue"},
                {"name": "en", "color": "green"},
                {"name": "it", "color": "orange"},
            ]
        }
    },
    "created_at": {"date": {}},
}


CHAPTER_SCHEMA: Dict[str, Any] = {
    "emoji": {"rich_text": {}},
    "slug": {"rich_text": {}},
    "description": {"rich_text": {}},
    "sort_order": {"number": {"format": "number"}},
    "active": {"checkbox": {}},
    "target_people": {"number": {"format": "number"}},
    "mood": {
        "select": {
            "options": [
                {"name": "light", "color": "green"},
                {"name": "practical", "color": "blue"},
                {"name": "intimate", "color": "purple"},
                {"name": "heavy", "color": "red"},
                {"name": "sorting", "color": "yellow"},
                {"name": "delicate", "color": "pink"},
            ]
        }
    },
    "needs_followup": {"checkbox": {}},
    "projection_label": {"rich_text": {}},
    "color_tag": {
        "select": {
            "options": [
                {"name": "green", "color": "green"},
                {"name": "yellow", "color": "yellow"},
                {"name": "blue", "color": "blue"},
                {"name": "pink", "color": "pink"},
                {"name": "brown", "color": "brown"},
            ]
        }
    },
}


QUESTION_SCHEMA: Dict[str, Any] = {
    "kind": {
        "select": {
            "options": [
                {"name": "chapter_interest", "color": "green"},
                {"name": "availability", "color": "blue"},
                {"name": "capacity_offer", "color": "orange"},
                {"name": "followup", "color": "purple"},
                {"name": "feedback", "color": "pink"},
                {"name": "notes", "color": "gray"},
            ]
        }
    },
    "prompt": {"rich_text": {}},
    "input_type": {
        "select": {
            "options": [
                {"name": "multiselect", "color": "purple"},
                {"name": "single_select", "color": "blue"},
                {"name": "text", "color": "gray"},
                {"name": "checkbox", "color": "green"},
                {"name": "date_slot", "color": "yellow"},
                {"name": "scale", "color": "orange"},
            ]
        }
    },
    "choice_options_json": {"rich_text": {}},
    "required": {"checkbox": {}},
    "active": {"checkbox": {}},
    "step_order": {"number": {"format": "number"}},
    "visibility": {
        "select": {
            "options": [
                {"name": "participant", "color": "green"},
                {"name": "host", "color": "blue"},
                {"name": "projection", "color": "purple"},
            ]
        }
    },
    "help_text": {"rich_text": {}},
    "created_at": {"date": {}},
}


RESPONSE_SCHEMA: Dict[str, Any] = {
    "response_type": {
        "select": {
            "options": [
                {"name": "interest", "color": "green"},
                {"name": "availability", "color": "blue"},
                {"name": "capacity", "color": "orange"},
                {"name": "followup", "color": "purple"},
                {"name": "feedback", "color": "pink"},
                {"name": "note", "color": "gray"},
            ]
        }
    },
    "payload_text": {"rich_text": {}},
    "payload_json": {"rich_text": {}},
    "availability_bucket": {
        "multi_select": {
            "options": [
                {"name": "this_weekend", "color": "green"},
                {"name": "weekday_evening", "color": "blue"},
                {"name": "next_week", "color": "purple"},
                {"name": "flexible", "color": "gray"},
            ]
        }
    },
    "exact_start": {"date": {}},
    "exact_end": {"date": {}},
    "signal_strength": {
        "select": {
            "options": [
                {"name": "low", "color": "gray"},
                {"name": "medium", "color": "yellow"},
                {"name": "high", "color": "green"},
            ]
        }
    },
    "visibility": {
        "select": {
            "options": [
                {"name": "private", "color": "gray"},
                {"name": "host", "color": "blue"},
                {"name": "projection", "color": "green"},
            ]
        }
    },
    "submitted_at": {"date": {}},
    "source": {
        "select": {
            "options": [
                {"name": "whatsapp_link", "color": "green"},
                {"name": "qr", "color": "blue"},
                {"name": "host_entry", "color": "purple"},
                {"name": "test", "color": "gray"},
            ]
        }
    },
}


SESSION_SCHEMA: Dict[str, Any] = {
    "status": {
        "select": {
            "options": [
                {"name": "proposed", "color": "yellow"},
                {"name": "confirmed", "color": "green"},
                {"name": "done", "color": "blue"},
                {"name": "cancelled", "color": "red"},
            ]
        }
    },
    "start_at": {"date": {}},
    "end_at": {"date": {}},
    "capacity_target": {"number": {"format": "number"}},
    "notes": {"rich_text": {}},
    "generated_from": {"rich_text": {}},
    "created_at": {"date": {}},
}


EVENT_LOG_SCHEMA: Dict[str, Any] = {
    "timestamp": {"date": {}},
    "action_type": {
        "select": {
            "options": [
                {"name": "bootstrap", "color": "gray"},
                {"name": "create_key", "color": "blue"},
                {"name": "login", "color": "green"},
                {"name": "select_chapter", "color": "purple"},
                {"name": "submit_availability", "color": "yellow"},
                {"name": "submit_capacity", "color": "orange"},
                {"name": "create_session", "color": "pink"},
                {"name": "view_projection", "color": "blue"},
                {"name": "submit_feedback", "color": "purple"},
            ]
        }
    },
    "target_type": {
        "select": {
            "options": [
                {"name": "player", "color": "green"},
                {"name": "event", "color": "blue"},
                {"name": "chapter", "color": "purple"},
                {"name": "response", "color": "orange"},
                {"name": "session", "color": "pink"},
                {"name": "system", "color": "gray"},
            ]
        }
    },
    "target_id": {"rich_text": {}},
    "summary": {"rich_text": {}},
    "payload_json": {"rich_text": {}},
}
