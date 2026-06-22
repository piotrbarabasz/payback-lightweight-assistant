"""Deterministic language detection helpers for raw user queries."""

from __future__ import annotations

import re

from app.schemas import Language


BASIC_PUNCTUATION_PATTERN = re.compile(r"[^\w\s]", flags=re.UNICODE)
WHITESPACE_PATTERN = re.compile(r"\s+")

GERMAN_HINTS = {
    "abendessen",
    "billig",
    "bitte",
    "g\u00fcnstige",
    "guenstig",
    "guenstige",
    "gunstig",
    "gunstige",
    "fr\u00fchst\u00fcck",
    "fruehstueck",
    "fruhstuck",
    "konto",
    "kopfh\u00f6rer",
    "kopfhoerer",
    "kopfhorer",
    "meine",
    "milch",
    "nudeln",
    "punkte",
    "vergleiche",
    "vergleich",
    "windeln",
    "zahnpasta",
    "zeige",
}

GERMAN_PHRASE_HINTS = {
    "ich brauche",
}

ENGLISH_HINTS = {
    "account",
    "affordable",
    "breakfast",
    "cheap",
    "compare",
    "diapers",
    "dinner",
    "headphones",
    "milk",
    "pasta",
    "please",
    "points",
    "show",
    "toothpaste",
}

ENGLISH_PHRASE_HINTS = {
    "i need",
}


def detect_language(query: str) -> Language:
    """Infer German or English from deterministic query features."""

    normalized_query = _normalize_text(query)
    if not normalized_query:
        return Language.UNKNOWN

    if _contains_phrase_hint(normalized_query, GERMAN_PHRASE_HINTS):
        return Language.DE
    if _contains_phrase_hint(normalized_query, ENGLISH_PHRASE_HINTS):
        return Language.EN

    token_set = set(normalized_query.split(" "))
    if token_set & GERMAN_HINTS:
        return Language.DE
    if token_set & ENGLISH_HINTS:
        return Language.EN
    return Language.UNKNOWN


def _normalize_text(text: str) -> str:
    lowercase_text = text.casefold().strip()
    without_punctuation = BASIC_PUNCTUATION_PATTERN.sub(" ", lowercase_text)
    return WHITESPACE_PATTERN.sub(" ", without_punctuation).strip()


def _contains_phrase_hint(query: str, phrase_hints: set[str]) -> bool:
    padded_query = f" {query} "
    return any(f" {phrase} " in padded_query for phrase in phrase_hints)
