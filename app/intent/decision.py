"""Next-best-action decisions for deterministic intent results."""

from __future__ import annotations

from app.schemas import (
    Intent,
    Language,
    NextBestAction,
    Partner,
    QueryEntities,
    Specificity,
)


GENERAL_CLARIFYING_QUESTIONS = {
    Language.DE: "Suchst du Lebensmittel, Drogerieprodukte oder allgemeine Produkte?",
    Language.EN: "Are you looking for groceries, drugstore items, or general products?",
    Language.UNKNOWN: "Are you looking for groceries, drugstore items, or general products?",
}
FOOD_CLARIFYING_QUESTIONS = {
    Language.DE: "Suchst du etwas f\u00fcr Fr\u00fchst\u00fcck, Mittagessen, Abendessen oder Snacks?",
    Language.EN: "Are you looking for breakfast, lunch, dinner, or snacks?",
    Language.UNKNOWN: "Are you looking for breakfast, lunch, dinner, or snacks?",
}
PRODUCT_CLARIFYING_QUESTIONS = {
    Language.DE: "Kannst du genauer sagen, welche Art von Produkt du suchst?",
    Language.EN: "Could you specify what type of product you are looking for?",
    Language.UNKNOWN: "Could you specify what type of product you are looking for?",
}


def decide_next_best_action(
    intent: Intent,
    specificity: Specificity,
    partner_hint: Partner | None,
    entities: QueryEntities,
) -> NextBestAction:
    """Map detected query facts to the next backend action."""

    if intent == Intent.CUSTOMER_SUPPORT:
        return NextBestAction.ROUTE_TO_SUPPORT
    if specificity == Specificity.VAGUE:
        return NextBestAction.ASK_CLARIFYING_QUESTION
    if intent == Intent.COMPARISON:
        return NextBestAction.COMPARE_PRODUCTS
    if specificity == Specificity.NAVIGATIONAL and _has_partner_hint(partner_hint):
        return NextBestAction.PARTNER_SPECIFIC_SEARCH
    if intent in {Intent.SEARCH, Intent.DISCOVERY}:
        return NextBestAction.SEARCH_CATALOG
    return NextBestAction.FALLBACK


def build_clarifying_question(
    intent: Intent,
    entities: QueryEntities,
    language: Language,
) -> str:
    """Build a short deterministic clarifying question."""

    if _has_food_context(intent, entities):
        return FOOD_CLARIFYING_QUESTIONS.get(language, FOOD_CLARIFYING_QUESTIONS[Language.EN])
    if _has_product_context(intent, entities):
        return PRODUCT_CLARIFYING_QUESTIONS.get(
            language,
            PRODUCT_CLARIFYING_QUESTIONS[Language.EN],
        )
    return GENERAL_CLARIFYING_QUESTIONS.get(
        language,
        GENERAL_CLARIFYING_QUESTIONS[Language.EN],
    )


def _has_partner_hint(partner_hint: Partner | None) -> bool:
    return partner_hint is not None and partner_hint != Partner.UNKNOWN


def _has_food_context(intent: Intent, entities: QueryEntities) -> bool:
    if entities.occasion in {"breakfast", "lunch", "dinner", "party"}:
        return True
    if entities.product_category in {"dairy", "fresh produce", "pasta and grains"}:
        return True
    return intent == Intent.DISCOVERY and entities.dietary_preference is not None


def _has_product_context(intent: Intent, entities: QueryEntities) -> bool:
    if entities.product_category or entities.brand:
        return True
    return intent == Intent.SEARCH
