"""FastAPI application for the PAYBACK lightweight assistant stub."""

from __future__ import annotations

import re
from typing import Annotated

from fastapi import FastAPI, Query

from app.catalog.filters import filter_available, filter_by_category, filter_by_partner
from app.catalog.loader import load_products
from app.schemas import (
    AssistantQueryRequest,
    AssistantQueryResponse,
    HealthResponse,
    Intent,
    Language,
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


SUPPORT_KEYWORDS = {"punkte", "points", "account", "konto"}
DIAPER_KEYWORDS = {"baby", "babywindeln", "diaper", "diapers", "windel", "windeln"}
PASTA_KEYWORDS = {"abendessen", "dinner", "nudel", "nudeln", "pasta", "spaghetti"}
ELECTRONICS_KEYWORDS = {
    "electronics",
    "elektronik",
    "headphone",
    "headphones",
    "kopfh\u00f6rer",
    "kopfhoerer",
}
GERMAN_HINTS = {
    "angebote",
    "bitte",
    "dm",
    "edeka",
    "fuer",
    "hilfe",
    "ich",
    "konto",
    "mir",
    "punkte",
    "suche",
    "zeige",
}
VAGUE_QUERIES = {
    "angebote",
    "deals",
    "i need something nice",
    "products",
    "something nice",
}
CLARIFYING_QUESTION = "Are you looking for groceries, drugstore items, or general products?"
CATALOG_MOCK_REASON = (
    "Catalog-based mock result for Stage 2; no semantic retrieval or ranking applied."
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.post("/assistant/query", response_model=AssistantQueryResponse)
def query_assistant(payload: AssistantQueryRequest) -> AssistantQueryResponse:
    return _build_stub_response(payload)


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


def _build_stub_response(payload: AssistantQueryRequest) -> AssistantQueryResponse:
    """Return a deterministic stub response for API contract validation."""

    query = payload.query
    tokens = _tokens(query)
    language = _detect_language(query, tokens)

    if _is_support_query(query, tokens):
        return AssistantQueryResponse(
            query=query,
            language=language,
            intent=Intent.CUSTOMER_SUPPORT,
            specificity=Specificity.SPECIFIC,
            next_best_action=NextBestAction.ROUTE_TO_SUPPORT,
            clarifying_question=None,
            partner_hint=Partner.UNKNOWN,
            entities=QueryEntities(),
            results=[],
        )

    if _is_vague_query(query, tokens):
        return AssistantQueryResponse(
            query=query,
            language=language,
            intent=Intent.DISCOVERY,
            specificity=Specificity.VAGUE,
            next_best_action=NextBestAction.ASK_CLARIFYING_QUESTION,
            clarifying_question=CLARIFYING_QUESTION,
            partner_hint=Partner.UNKNOWN,
            entities=QueryEntities(),
            results=[],
        )

    products = filter_available(load_products())
    selected_products = _select_mock_catalog_products(tokens, products)

    return AssistantQueryResponse(
        query=query,
        language=language,
        intent=Intent.SEARCH,
        specificity=Specificity.SPECIFIC,
        next_best_action=NextBestAction.SEARCH_CATALOG,
        clarifying_question=None,
        partner_hint=_partner_hint_from_products(selected_products),
        entities=QueryEntities(
            product_category=_category_hint_from_products(selected_products)
        ),
        results=[
            _product_to_mock_result(product)
            for product in selected_products[: payload.top_k]
        ],
    )


def _tokens(query: str) -> set[str]:
    return set(re.findall(r"\w+", query.casefold(), flags=re.UNICODE))


def _detect_language(query: str, tokens: set[str]) -> Language:
    if any(character in query.casefold() for character in "\u00e4\u00f6\u00fc\u00df"):
        return Language.DE
    if tokens & GERMAN_HINTS:
        return Language.DE
    return Language.EN


def _is_support_query(query: str, tokens: set[str]) -> bool:
    lower_query = query.casefold()
    return bool(tokens & SUPPORT_KEYWORDS) or any(
        keyword in lower_query for keyword in SUPPORT_KEYWORDS
    )


def _is_vague_query(query: str, tokens: set[str]) -> bool:
    return len(tokens) < 4 or query.casefold() in VAGUE_QUERIES


def _select_mock_catalog_products(
    tokens: set[str],
    products: list[Product],
) -> list[Product]:
    if tokens & DIAPER_KEYWORDS:
        preferred_products = [
            product
            for product in products
            if product.partner == Partner.DM
            and _product_has_any_tag(
                product,
                {"diapers", "baby", "windeln", "babywindeln"},
            )
        ]
        if preferred_products:
            return preferred_products

    if tokens & PASTA_KEYWORDS:
        preferred_products = [
            product
            for product in products
            if product.partner == Partner.EDEKA
            and _product_has_any_tag(
                product,
                {
                    "pasta",
                    "spaghetti",
                    "nudeln",
                    "abendessen",
                    "grocery",
                    "meal ingredient",
                },
            )
        ]
        if preferred_products:
            return preferred_products

    if tokens & ELECTRONICS_KEYWORDS:
        preferred_products = [
            product
            for product in products
            if product.partner == Partner.AMAZON
            and _product_has_any_tag(
                product,
                {
                    "electronics",
                    "elektronik",
                    "headphones",
                    "wireless headphones",
                    "kopfh\u00f6rer",
                },
            )
        ]
        if preferred_products:
            return preferred_products

    return products


def _product_has_any_tag(product: Product, tags: set[str]) -> bool:
    product_tags = set(product.tags + product.tags_de)
    return bool(tags & product_tags)


def _product_to_mock_result(product: Product) -> ProductResult:
    return ProductResult(
        product_id=product.product_id,
        partner=product.partner,
        name=product.name,
        category=product.category,
        price=product.price,
        currency=product.currency,
        score=0.75,
        reason=CATALOG_MOCK_REASON,
    )


def _partner_hint_from_products(products: list[Product]) -> Partner:
    if not products:
        return Partner.UNKNOWN
    first_partner = products[0].partner
    if all(product.partner == first_partner for product in products):
        return first_partner
    return Partner.UNKNOWN


def _category_hint_from_products(products: list[Product]) -> str | None:
    if not products:
        return None
    first_category = products[0].category
    if all(product.category == first_category for product in products):
        return first_category
    return None
