"""FastAPI application for the Stage 1 lightweight assistant stub."""

from __future__ import annotations

import re

from fastapi import FastAPI

from app.schemas import (
    AssistantQueryRequest,
    AssistantQueryResponse,
    HealthResponse,
    Intent,
    Language,
    NextBestAction,
    Partner,
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


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.post("/assistant/query", response_model=AssistantQueryResponse)
def query_assistant(payload: AssistantQueryRequest) -> AssistantQueryResponse:
    return _build_stub_response(payload)


def _build_stub_response(payload: AssistantQueryRequest) -> AssistantQueryResponse:
    """Return a deterministic Stage 1 response for API contract validation."""

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

    return AssistantQueryResponse(
        query=query,
        language=language,
        intent=Intent.SEARCH,
        specificity=Specificity.SPECIFIC,
        next_best_action=NextBestAction.SEARCH_CATALOG,
        clarifying_question=None,
        partner_hint=Partner.UNKNOWN,
        entities=QueryEntities(product_category="drugstore"),
        results=[
            ProductResult(
                product_id="mock-dm-001",
                partner=Partner.DM,
                name="Mock Drugstore Product",
                category="drugstore",
                price=4.99,
                score=0.87,
                reason="Mock result for Stage 1 API contract validation.",
            )
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
