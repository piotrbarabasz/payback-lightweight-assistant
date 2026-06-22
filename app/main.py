"""FastAPI application for the PAYBACK lightweight assistant."""

from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, Query

from app.catalog.filters import filter_available, filter_by_category, filter_by_partner
from app.catalog.loader import load_products
from app.retrieval import (
    QueryAnalysis,
    category_hint_from_results,
    is_support_query,
    normalize_query,
    retrieve_products,
)
from app.schemas import (
    AssistantQueryRequest,
    AssistantQueryResponse,
    HealthResponse,
    Intent,
    NextBestAction,
    Partner,
    Product,
    ProductResult,
    QueryEntities,
    Specificity,
)


app = FastAPI(
    title="PAYBACK Lightweight Assistant",
    version="0.1.0",
    description="Recruitment challenge backend for a lightweight PAYBACK-like assistant.",
)


VAGUE_QUERIES = {
    "angebot",
    "angebote",
    "deals",
    "i need something nice",
    "products",
    "produkte",
    "something nice",
}
CLARIFYING_QUESTION = "Are you looking for groceries, drugstore items, or general products?"
COMPARISON_WORDS = {"compare", "comparison", "vergleich", "vergleiche"}
MEAL_OR_OCCASION_WORDS = {
    "abendessen",
    "breakfast",
    "dinner",
    "fruehstueck",
    "fr\u00fchst\u00fcck",
    "lunch",
}


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.post("/assistant/query", response_model=AssistantQueryResponse)
def query_assistant(payload: AssistantQueryRequest) -> AssistantQueryResponse:
    return _build_assistant_response(payload)


@app.get("/catalog/products", response_model=list[Product])
def preview_catalog_products(
    partner: Partner | None = None,
    category: str | None = None,
    available_only: bool = True,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[Product]:
    """Return local catalog products for development and demo inspection."""

    products = load_products()
    if partner is not None:
        products = filter_by_partner(products, partner)
    if category is not None:
        products = filter_by_category(products, category)
    if available_only:
        products = filter_available(products)
    return products[:limit]


def _build_assistant_response(payload: AssistantQueryRequest) -> AssistantQueryResponse:
    """Return a deterministic assistant response backed by local retrieval."""

    query = payload.query
    analysis = normalize_query(query)

    if is_support_query(analysis):
        return AssistantQueryResponse(
            query=query,
            language=analysis.language,
            intent=Intent.CUSTOMER_SUPPORT,
            specificity=Specificity.SPECIFIC,
            next_best_action=NextBestAction.ROUTE_TO_SUPPORT,
            clarifying_question=None,
            partner_hint=Partner.UNKNOWN,
            entities=QueryEntities(),
            results=[],
        )

    if _is_vague_query(analysis):
        return AssistantQueryResponse(
            query=query,
            language=analysis.language,
            intent=Intent.DISCOVERY,
            specificity=Specificity.VAGUE,
            next_best_action=NextBestAction.ASK_CLARIFYING_QUESTION,
            clarifying_question=CLARIFYING_QUESTION,
            partner_hint=Partner.UNKNOWN,
            entities=QueryEntities(),
            results=[],
        )

    results = retrieve_products(
        query,
        load_products(),
        top_k=payload.top_k,
    )

    if not results:
        return AssistantQueryResponse(
            query=query,
            language=analysis.language,
            intent=_detect_temporary_intent(analysis),
            specificity=Specificity.VAGUE,
            next_best_action=NextBestAction.ASK_CLARIFYING_QUESTION,
            clarifying_question=CLARIFYING_QUESTION,
            partner_hint=analysis.partner_hint,
            entities=QueryEntities(price_preference=analysis.price_preference),
            results=[],
        )

    intent = _detect_temporary_intent(analysis)
    return AssistantQueryResponse(
        query=query,
        language=analysis.language,
        intent=intent,
        specificity=_specificity_for_search(analysis),
        next_best_action=_next_best_action_for_search(intent, analysis),
        clarifying_question=None,
        partner_hint=_partner_hint_from_results(
            analysis.partner_hint,
            results,
        ),
        entities=QueryEntities(
            product_category=category_hint_from_results(results),
            price_preference=analysis.price_preference,
            occasion=_occasion_hint(analysis),
            dietary_preference=_dietary_preference_hint(analysis),
        ),
        results=results,
    )


def _is_vague_query(analysis: QueryAnalysis) -> bool:
    if analysis.normalized_query in VAGUE_QUERIES:
        return True
    return not analysis.search_tokens


def _detect_temporary_intent(analysis: QueryAnalysis) -> Intent:
    """Temporary rule-based intent detection until Stage 4 intent handling."""

    if analysis.expanded_tokens & COMPARISON_WORDS:
        return Intent.COMPARISON
    if analysis.expanded_tokens & MEAL_OR_OCCASION_WORDS:
        return Intent.DISCOVERY
    return Intent.SEARCH


def _next_best_action_for_search(
    intent: Intent,
    analysis: QueryAnalysis,
) -> NextBestAction:
    """Temporary rule-based next action until Stage 4 intent handling."""

    if intent == Intent.COMPARISON:
        return NextBestAction.COMPARE_PRODUCTS
    if analysis.partner_hint is not None:
        return NextBestAction.PARTNER_SPECIFIC_SEARCH
    return NextBestAction.SEARCH_CATALOG


def _specificity_for_search(analysis: QueryAnalysis) -> Specificity:
    if analysis.partner_hint is not None:
        return Specificity.NAVIGATIONAL
    return Specificity.SPECIFIC


def _partner_hint_from_results(
    query_partner_hint: Partner | None,
    results: list[ProductResult],
) -> Partner:
    if query_partner_hint is not None:
        return query_partner_hint
    if not results:
        return Partner.UNKNOWN

    first_partner = results[0].partner
    if all(result.partner == first_partner for result in results):
        return first_partner
    return Partner.UNKNOWN


def _occasion_hint(analysis: QueryAnalysis) -> str | None:
    if analysis.expanded_tokens & {"abendessen", "dinner"}:
        return "dinner"
    if analysis.expanded_tokens & {"breakfast", "fruehstueck", "fruhstuck"}:
        return "breakfast"
    return None


def _dietary_preference_hint(analysis: QueryAnalysis) -> str | None:
    if analysis.expanded_tokens & {"bio", "organic"}:
        return "organic"
    if analysis.expanded_tokens & {"vegetarian", "vegetarisch"}:
        return "vegetarian"
    if analysis.expanded_tokens & {"vegan"}:
        return "vegan"
    return None
