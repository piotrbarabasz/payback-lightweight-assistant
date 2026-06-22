from app.intent.decision import build_clarifying_question, decide_next_best_action
from app.schemas import (
    Intent,
    Language,
    NextBestAction,
    Partner,
    QueryEntities,
    Specificity,
)


def test_customer_support_routes_to_support() -> None:
    assert (
        decide_next_best_action(
            Intent.CUSTOMER_SUPPORT,
            Specificity.SPECIFIC,
            None,
            QueryEntities(),
        )
        == NextBestAction.ROUTE_TO_SUPPORT
    )


def test_vague_query_asks_clarifying_question() -> None:
    assert (
        decide_next_best_action(
            Intent.UNKNOWN,
            Specificity.VAGUE,
            None,
            QueryEntities(),
        )
        == NextBestAction.ASK_CLARIFYING_QUESTION
    )


def test_comparison_uses_compare_products() -> None:
    assert (
        decide_next_best_action(
            Intent.COMPARISON,
            Specificity.SPECIFIC,
            None,
            QueryEntities(),
        )
        == NextBestAction.COMPARE_PRODUCTS
    )


def test_navigational_with_partner_hint_uses_partner_specific_search() -> None:
    assert (
        decide_next_best_action(
            Intent.SEARCH,
            Specificity.NAVIGATIONAL,
            Partner.AMAZON,
            QueryEntities(),
        )
        == NextBestAction.PARTNER_SPECIFIC_SEARCH
    )


def test_specific_search_uses_search_catalog() -> None:
    assert (
        decide_next_best_action(
            Intent.SEARCH,
            Specificity.SPECIFIC,
            None,
            QueryEntities(product_category="electronics"),
        )
        == NextBestAction.SEARCH_CATALOG
    )


def test_specific_discovery_uses_search_catalog() -> None:
    assert (
        decide_next_best_action(
            Intent.DISCOVERY,
            Specificity.SPECIFIC,
            None,
            QueryEntities(occasion="dinner"),
        )
        == NextBestAction.SEARCH_CATALOG
    )


def test_unknown_uses_fallback() -> None:
    assert (
        decide_next_best_action(
            Intent.UNKNOWN,
            Specificity.UNKNOWN,
            None,
            QueryEntities(),
        )
        == NextBestAction.FALLBACK
    )


def test_build_clarifying_question_returns_german_question() -> None:
    question = build_clarifying_question(
        Intent.UNKNOWN,
        QueryEntities(),
        Language.DE,
    )

    assert question == "Suchst du Lebensmittel, Drogerieprodukte oder allgemeine Produkte?"


def test_build_clarifying_question_returns_english_question() -> None:
    question = build_clarifying_question(
        Intent.UNKNOWN,
        QueryEntities(),
        Language.EN,
    )

    assert question == "Are you looking for groceries, drugstore items, or general products?"


def test_clarifying_questions_are_non_empty_and_concise() -> None:
    questions = [
        build_clarifying_question(Intent.UNKNOWN, QueryEntities(), Language.EN),
        build_clarifying_question(Intent.UNKNOWN, QueryEntities(), Language.DE),
        build_clarifying_question(
            Intent.DISCOVERY,
            QueryEntities(occasion="dinner"),
            Language.EN,
        ),
        build_clarifying_question(
            Intent.SEARCH,
            QueryEntities(product_category="electronics"),
            Language.DE,
        ),
    ]

    assert all(question.strip() for question in questions)
    assert all(len(question) <= 90 for question in questions)
