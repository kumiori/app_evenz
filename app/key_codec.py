from __future__ import annotations

import math
import re
import secrets
from typing import Dict, List


DEFAULT_KEY_BYTES = 16
DEFAULT_HEX_LENGTH = DEFAULT_KEY_BYTES * 2

EMOJI_ALPHABET: List[str] = [
    "🌑",
    "🌒",
    "🌓",
    "🌔",
    "🌕",
    "🌖",
    "🌗",
    "🌘",
    "⭐",
    "🌟",
    "✨",
    "⚡",
    "🔥",
    "💧",
    "🌊",
    "🌬️",
    "🌀",
    "🌈",
    "❄️",
    "☄️",
    "🌋",
    "💎",
    "🧊",
    "🪐",
    "🌌",
    "🎇",
    "🎆",
    "🎈",
    "🎉",
    "🎯",
    "🎲",
    "🧠",
    "🫧",
    "🧬",
    "🔮",
    "🪄",
    "🛰️",
    "🚀",
    "🛸",
    "🛠️",
    "⚙️",
    "📡",
    "🔑",
    "🗝️",
    "📀",
    "💾",
    "🧲",
    "🪙",
    "🥇",
    "🎖️",
    "🔰",
    "♾️",
    "🪬",
    "🔺",
    "🔻",
    "🔷",
    "🔶",
    "⬛",
    "⬜",
    "🟥",
    "🟩",
    "🟦",
    "🟨",
]
EMOJI_BASE = len(EMOJI_ALPHABET)
EMOJI_INDEX = {symbol: idx for idx, symbol in enumerate(EMOJI_ALPHABET)}
EMOJI_SYMBOLS_PER_KEY = math.ceil(DEFAULT_KEY_BYTES * 8 / math.log2(EMOJI_BASE))

ADJECTIVES = [
    "solar",
    "lunar",
    "crystal",
    "shadow",
    "ember",
    "sonic",
    "quantum",
    "wild",
    "neon",
    "iron",
    "cipher",
    "scarlet",
    "plasma",
    "velvet",
    "static",
    "mythic",
]
NOUNS = [
    "vault",
    "pulse",
    "glyph",
    "arc",
    "spike",
    "flare",
    "crown",
    "delta",
    "prism",
    "drift",
    "forge",
    "orbit",
    "circuit",
    "veil",
    "signal",
    "quartz",
]
WORDLIST_256 = [f"{adj}{noun}" for adj in ADJECTIVES for noun in NOUNS]
WORD_INDEX: Dict[str, int] = {word: idx for idx, word in enumerate(WORDLIST_256)}

HEX_PATTERN = re.compile(r"^[0-9a-fA-F]+$")
EMOJI_PATTERN = re.compile(
    "|".join(sorted((re.escape(symbol) for symbol in EMOJI_ALPHABET), key=len, reverse=True))
)


def generate_hex_key() -> str:
    return secrets.token_hex(DEFAULT_KEY_BYTES).upper()


def _int_to_base_symbols(value: int, alphabet: List[str], pad: int) -> str:
    if value == 0:
        return alphabet[0] * max(1, pad)
    digits: List[str] = []
    base = len(alphabet)
    while value > 0:
        value, rem = divmod(value, base)
        digits.append(alphabet[rem])
    while len(digits) < pad:
        digits.append(alphabet[0])
    return "".join(reversed(digits))


def _symbols_to_int(symbols: List[str], alphabet_index: Dict[str, int]) -> int:
    value = 0
    base = len(alphabet_index)
    for symbol in symbols:
        value = value * base + alphabet_index[symbol]
    return value


def split_emoji_symbols(raw: str) -> List[str]:
    if not raw:
        return []
    symbols: List[str] = []
    index = 0
    while index < len(raw):
        match = EMOJI_PATTERN.match(raw, index)
        if not match:
            return []
        symbols.append(match.group(0))
        index = match.end()
    return symbols


def hex_to_emoji(hex_key: str) -> str:
    value = int(hex_key, 16)
    return _int_to_base_symbols(value, EMOJI_ALPHABET, EMOJI_SYMBOLS_PER_KEY)


def emoji_to_hex(emoji_key: str) -> str:
    symbols = split_emoji_symbols(emoji_key)
    if len(symbols) != EMOJI_SYMBOLS_PER_KEY:
        raise ValueError(f"Emoji keys must be {EMOJI_SYMBOLS_PER_KEY} symbols long.")
    value = _symbols_to_int(symbols, EMOJI_INDEX)
    return f"{value:0{DEFAULT_HEX_LENGTH}X}"


def hex_to_phrase(hex_key: str, separator: str = "-") -> str:
    data = bytes.fromhex(hex_key)
    if len(data) != DEFAULT_KEY_BYTES:
        raise ValueError("Hex key must represent 16 bytes for phrase projection.")
    return separator.join(WORDLIST_256[byte] for byte in data)


def phrase_to_hex(phrase: str) -> str:
    tokens = re.split(r"[\s,_-]+", phrase.strip().lower())
    tokens = [token for token in tokens if token]
    if len(tokens) != DEFAULT_KEY_BYTES:
        raise ValueError(f"Passphrase must contain {DEFAULT_KEY_BYTES} words.")
    data = bytearray()
    for token in tokens:
        if token not in WORD_INDEX:
            raise ValueError(f"Unknown token '{token}' in passphrase.")
        data.append(WORD_INDEX[token])
    return data.hex().upper()


def normalize_access_key(raw: str) -> str:
    candidate = raw.strip()
    if not candidate:
        raise ValueError("Empty access key.")

    hex_guess = candidate.replace(" ", "").replace("-", "")
    if hex_guess.lower().startswith("0x"):
        hex_guess = hex_guess[2:]
    if HEX_PATTERN.fullmatch(hex_guess) and len(hex_guess) == DEFAULT_HEX_LENGTH:
        return hex_guess.upper()

    emoji_symbols = split_emoji_symbols(candidate)
    if emoji_symbols:
        return emoji_to_hex(candidate)

    tokens = re.split(r"[\s,_-]+", candidate.lower())
    tokens = [token for token in tokens if token]
    if tokens and all(token in WORD_INDEX for token in tokens):
        return phrase_to_hex(candidate)

    raise ValueError("Access key format not recognized.")


def key_to_emoji_suffix(raw_key: str, length: int = 4) -> str:
    if length <= 0:
        return ""
    canonical = normalize_access_key(raw_key)
    emoji_key = hex_to_emoji(canonical)
    symbols = split_emoji_symbols(emoji_key)
    if not symbols:
        return ""
    return "".join(symbols[-length:])
