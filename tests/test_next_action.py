from app.intent.next_action import decide_next_best_action
from app.schemas import Intent, NextBestAction, Partner, QueryEntities, Specificity


def test_decide_next_best_action_routes_support_first() -> None:
    action = decide_next_best_action(
        Intent.CUSTOMER_SUPPORT,
        Specificity.SPECIFIC,
        None,
        QueryEntities(),
    )

    assert action == NextBestAction.ROUTE_TO_SUPPORT


def test_decide_next_best_action_asks_when_query_is_vague() -> None:
    action = decide_next_best_action(
        Intent.SEARCH,
        Specificity.VAGUE,
        None,
        QueryEntities(),
    )

    assert action == NextBestAction.ASK_CLARIFYING_QUESTION


def test_decide_next_best_action_compares_before_partner_search() -> None:
    action = decide_next_best_action(
        Intent.COMPARISON,
        Specificity.NAVIGATIONAL,
        Partner.AMAZON,
        QueryEntities(),
    )

    assert action == NextBestAction.COMPARE_PRODUCTS


def test_decide_next_best_action_uses_partner_specific_search() -> None:
    action = decide_next_best_action(
        Intent.SEARCH,
        Specificity.NAVIGATIONAL,
        Partner.DM,
        QueryEntities(),
    )

    assert action == NextBestAction.PARTNER_SPECIFIC_SEARCH


def test_decide_next_best_action_searches_catalog_for_specific_search() -> None:
    action = decide_next_best_action(
        Intent.SEARCH,
        Specificity.SPECIFIC,
        None,
        QueryEntities(),
    )

    assert action == NextBestAction.SEARCH_CATALOG
