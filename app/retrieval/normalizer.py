"""Pure query normalization helpers for deterministic retrieval."""

from __future__ import annotations

from dataclasses import dataclass
import re

from app.intent.language import detect_language
from app.schemas import Language, Partner


BASIC_PUNCTUATION_PATTERN = re.compile(r"[^\w\s]", flags=re.UNICODE)
WHITESPACE_PATTERN = re.compile(r"\s+")

PARTNER_TOKENS: dict[str, Partner] = {
    "dm": Partner.DM,
    "edeka": Partner.EDEKA,
    "amazon": Partner.AMAZON,
}

STOP_WORDS = {
    "a",
    "about",
    "an",
    "and",
    "any",
    "are",
    "artikel",
    "bei",
    "bitte",
    "brauche",
    "buy",
    "can",
    "could",
    "das",
    "der",
    "die",
    "ein",
    "eine",
    "for",
    "fuer",
    "fur",
    "gib",
    "give",
    "good",
    "haben",
    "i",
    "ich",
    "im",
    "in",
    "ist",
    "kaufen",
    "looking",
    "me",
    "mir",
    "need",
    "nice",
    "of",
    "please",
    "product",
    "products",
    "produkt",
    "produkte",
    "show",
    "something",
    "the",
    "to",
    "und",
    "useful",
    "was",
    "what",
    "with",
    "would",
    "zeige",
}

PRICE_PREFERENCE_TOKENS = {
    "cheap": {
        "affordable",
        "billig",
        "billige",
        "budget",
        "cheap",
        "cheaper",
        "g\u00fcnstig",
        "g\u00fcnstige",
        "guenstig",
        "guenstige",
        "gunstig",
        "gunstige",
        "preiswert",
    },
    "premium": {
        "best",
        "beste",
        "hochwertig",
        "premium",
    },
}
PREMIUM_PRICE_PHRASES = {"high quality"}

CATEGORY_HINT_RULES: tuple[tuple[str, set[str]], ...] = (
    (
        "baby care",
        {"baby", "diaper", "diapers", "windel", "windeln", "babywindeln"},
    ),
    (
        "pasta and grains",
        {"abendessen", "dinner", "nudel", "nudeln", "pasta", "spaghetti"},
    ),
    ("dairy", {"dairy", "milk", "milch", "molkerei"}),
    (
        "electronics",
        {
            "electronics",
            "elektronik",
            "headphone",
            "headphones",
            "kopfhoerer",
            "kopfhorer",
            "kopfh\u00f6rer",
        },
    ),
    ("home office", {"maus", "mouse"}),
    ("electronics", {"maus", "mouse"}),
    ("hair care", {"haarpflege", "shampoo"}),
    ("oral care", {"toothpaste", "zahnpasta"}),
)

TOKEN_SYNONYMS = {
    "abendessen": {"dinner", "meal", "meals"},
    "babywindel": {"diaper", "diapers", "windel", "windeln"},
    "babywindeln": {"diaper", "diapers", "windel", "windeln"},
    "billige": {"billig", "cheap"},
    "dinner": {"abendessen", "meal"},
    "diaper": {"diapers", "windel", "windeln", "babywindeln"},
    "diapers": {"diaper", "windel", "windeln", "babywindeln"},
    "electronics": {"elektronik"},
    "elektronik": {"electronics"},
    "g\u00fcnstig": {"cheap", "affordable", "budget", "guenstig"},
    "g\u00fcnstige": {"cheap", "affordable", "budget", "g\u00fcnstig"},
    "guenstig": {"cheap", "affordable", "budget", "g\u00fcnstig"},
    "guenstige": {"cheap", "affordable", "budget", "guenstig"},
    "gunstig": {"cheap", "affordable", "budget", "g\u00fcnstig"},
    "gunstige": {"cheap", "affordable", "budget", "gunstig"},
    "headphone": {"headphones", "kopfhoerer", "kopfhorer", "kopfh\u00f6rer"},
    "headphones": {"headphone", "kopfhoerer", "kopfhorer", "kopfh\u00f6rer"},
    "hochwertig": {"premium"},
    "kabellos": {"wireless"},
    "kabellose": {"wireless"},
    "kopfhoerer": {"headphone", "headphones", "kopfhorer", "kopfh\u00f6rer"},
    "kopfhorer": {"headphone", "headphones", "kopfhoerer", "kopfh\u00f6rer"},
    "kopfh\u00f6rer": {"headphone", "headphones", "kopfhoerer", "kopfhorer"},
    "maus": {"mouse"},
    "meal": {"abendessen", "dinner"},
    "milch": {"milk", "dairy"},
    "mouse": {"maus"},
    "nudel": {"nudeln", "pasta", "spaghetti"},
    "nudeln": {"nudel", "pasta", "spaghetti"},
    "pasta": {"nudeln", "spaghetti"},
    "spaghetti": {"pasta", "nudeln"},
    "windel": {"windeln", "diaper", "diapers", "babywindeln"},
    "windeln": {"windel", "diaper", "diapers", "babywindeln"},
    "wireless": {"kabellos", "kabellose"},
    "zahnpasta": {"toothpaste"},
}

SUPPORT_KEYWORDS = {
    "account",
    "fehlen",
    "konto",
    "missing",
    "points",
    "punkte",
}


@dataclass(frozen=True)
class QueryAnalysis:
    """Normalized query facts used by API routing and retrieval scoring."""

    raw_query: str
    normalized_query: str
    language: Language
    tokens: tuple[str, ...]
    expanded_tokens: frozenset[str]
    search_tokens: tuple[str, ...]
    partner_hint: Partner | None
    price_preference: str | None
    category_hints: tuple[str, ...]


def normalize_text(text: str) -> str:
    """Lowercase text, remove basic punctuation, and normalize whitespace."""

    lowercase_text = text.lower().strip()
    without_punctuation = BASIC_PUNCTUATION_PATTERN.sub(" ", lowercase_text)
    return WHITESPACE_PATTERN.sub(" ", without_punctuation).strip()


def tokenize(text: str) -> list[str]:
    """Normalize text and split it into non-empty German and English tokens."""

    normalized_text = normalize_text(text)
    if not normalized_text:
        return []
    return [token for token in normalized_text.split(" ") if token]


def detect_price_preference(query: str) -> str | None:
    """Detect a simple price preference from German or English query terms."""

    normalized_query = normalize_text(query)
    expanded_tokens = _expand_tokens(tuple(tokenize(query)))
    if expanded_tokens & PRICE_PREFERENCE_TOKENS["cheap"]:
        return "cheap"
    if normalized_query in PREMIUM_PRICE_PHRASES or any(
        phrase in normalized_query for phrase in PREMIUM_PRICE_PHRASES
    ):
        return "premium"
    if expanded_tokens & PRICE_PREFERENCE_TOKENS["premium"]:
        return "premium"
    return None


def detect_partner_hint(query: str) -> Partner | None:
    """Detect an explicit partner mention in a user query."""

    for token in tokenize(query):
        partner = PARTNER_TOKENS.get(token)
        if partner is not None:
            return partner
    return None


def detect_basic_category_hints(query: str) -> list[str]:
    """Detect broad catalog categories from German and English query terms."""

    expanded_tokens = _expand_tokens(tuple(tokenize(query)))
    category_hints: list[str] = []
    for category, terms in CATEGORY_HINT_RULES:
        if category not in category_hints and expanded_tokens & terms:
            category_hints.append(category)
    return category_hints


def normalize_query(query: str) -> QueryAnalysis:
    """Normalize, tokenize, enrich, and classify a raw user query."""

    normalized_query = normalize_text(query)
    tokens = tuple(tokenize(query))
    expanded_tokens = _expand_tokens(tokens)
    return QueryAnalysis(
        raw_query=query,
        normalized_query=normalized_query,
        language=detect_language(query),
        tokens=tokens,
        expanded_tokens=frozenset(expanded_tokens),
        search_tokens=tuple(
            token
            for token in sorted(expanded_tokens)
            if token not in STOP_WORDS
            and token not in PARTNER_TOKENS
            and not is_price_token(token)
        ),
        partner_hint=detect_partner_hint(query),
        price_preference=detect_price_preference(query),
        category_hints=tuple(detect_basic_category_hints(query)),
    )


def is_support_query(analysis: QueryAnalysis) -> bool:
    """Return whether the query should be routed to account support."""

    return bool(analysis.expanded_tokens & SUPPORT_KEYWORDS)


def is_price_token(token: str) -> bool:
    return any(token in tokens for tokens in PRICE_PREFERENCE_TOKENS.values())


def _expand_tokens(tokens: tuple[str, ...]) -> set[str]:
    expanded: set[str] = set()
    for token in tokens:
        expanded.add(token)
        expanded.update(_simple_variants(token))
        expanded.update(TOKEN_SYNONYMS.get(token, set()))
    return expanded


def _simple_variants(token: str) -> set[str]:
    variants: set[str] = set()
    if token.endswith("s") and len(token) > 3:
        variants.add(token[:-1])
    if token.endswith("e") and len(token) > 4:
        variants.add(token[:-1])
    if token.endswith("en") and len(token) > 5:
        variants.add(token[:-2])
    if token.endswith("n") and len(token) > 5:
        variants.add(token[:-1])
    return variants
