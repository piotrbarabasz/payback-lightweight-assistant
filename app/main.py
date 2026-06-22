"""FastAPI application for the PAYBACK lightweight assistant."""

from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, Query

from app.assistant.service import build_assistant_response
from app.catalog.filters import filter_available, filter_by_category, filter_by_partner
from app.catalog.loader import load_products
from app.intent.service import analyze_query_intent
from app.schemas import (
    AssistantQueryRequest,
    AssistantQueryResponse,
    HealthResponse,
    Partner,
    Product,
)


app = FastAPI(
    title="PAYBACK Lightweight Assistant",
    version="0.1.0",
    description="Recruitment challenge backend for a lightweight PAYBACK-like assistant.",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.post("/assistant/query", response_model=AssistantQueryResponse)
def query_assistant(payload: AssistantQueryRequest) -> AssistantQueryResponse:
    intent_result = analyze_query_intent(payload.query)
    return build_assistant_response(payload, intent_result)


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
