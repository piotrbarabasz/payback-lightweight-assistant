"""Pydantic schemas for the Stage 1 assistant API contract."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class APIModel(BaseModel):
    """Base model shared by API schemas."""

    model_config = ConfigDict(extra="forbid")


class Language(StrEnum):
    DE = "de"
    EN = "en"
    UNKNOWN = "unknown"


class Intent(StrEnum):
    SEARCH = "search"
    DISCOVERY = "discovery"
    COMPARISON = "comparison"
    CUSTOMER_SUPPORT = "customer_support"
    UNKNOWN = "unknown"


class Specificity(StrEnum):
    SPECIFIC = "specific"
    VAGUE = "vague"
    NAVIGATIONAL = "navigational"
    UNKNOWN = "unknown"


class NextBestAction(StrEnum):
    SEARCH_CATALOG = "search_catalog"
    ASK_CLARIFYING_QUESTION = "ask_clarifying_question"
    PARTNER_SPECIFIC_SEARCH = "partner_specific_search"
    COMPARE_PRODUCTS = "compare_products"
    ROUTE_TO_SUPPORT = "route_to_support"
    FALLBACK = "fallback"


class Partner(StrEnum):
    DM = "dm"
    EDEKA = "edeka"
    AMAZON = "amazon"
    UNKNOWN = "unknown"


class HealthResponse(APIModel):
    status: Literal["ok"] = "ok"
    service: Literal["payback-lightweight-assistant"] = "payback-lightweight-assistant"


class AssistantQueryRequest(APIModel):
    query: str = Field(
        ...,
        min_length=1,
        description="Raw user query to classify and route.",
    )
    user_id: str | None = Field(
        default=None,
        description="Reserved for future personalization.",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Requested number of product results.",
    )

    @field_validator("query", mode="before")
    @classmethod
    def strip_query(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class QueryEntities(APIModel):
    product_category: str | None = None
    price_preference: str | None = None
    occasion: str | None = None
    dietary_preference: str | None = None
    brand: str | None = None


class ProductResult(APIModel):
    product_id: str
    partner: Partner
    name: str
    category: str
    price: float
    currency: str = "EUR"
    score: float = Field(..., ge=0, le=1)
    reason: str | None = None


class AssistantQueryResponse(APIModel):
    query: str
    language: Language
    intent: Intent
    specificity: Specificity
    next_best_action: NextBestAction
    clarifying_question: str | None = None
    partner_hint: Partner | None = None
    entities: QueryEntities
    results: list[ProductResult] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_clarifying_question_for_clarification(self) -> AssistantQueryResponse:
        if self.next_best_action == NextBestAction.ASK_CLARIFYING_QUESTION:
            if not self.clarifying_question or not self.clarifying_question.strip():
                raise ValueError(
                    "clarifying_question is required when next_best_action is "
                    "ask_clarifying_question"
                )
        return self
