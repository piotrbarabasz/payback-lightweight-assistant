"""Pydantic schemas for the Stage 1 assistant API contract."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.config import get_settings


settings = get_settings()


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
    environment: str = "local"


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
        default=settings.DEFAULT_TOP_K,
        ge=1,
        le=settings.MAX_TOP_K,
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


class IntentDetectionResult(APIModel):
    query: str
    language: Language
    intent: Intent
    specificity: Specificity
    next_best_action: NextBestAction
    partner_hint: Optional[Partner] = None
    entities: QueryEntities
    confidence: float = Field(default=0.7, ge=0, le=1)
    requires_clarification: bool = False
    clarifying_question: Optional[str] = None


class Product(APIModel):
    """Raw catalog product entity used before retrieval scoring."""

    product_id: str = Field(..., min_length=1)
    partner: Partner
    name: str = Field(..., min_length=1)
    name_de: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    description_de: str = Field(..., min_length=1)
    brand: str = Field(..., min_length=1)
    price: float = Field(..., ge=0)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    tags: list[str] = Field(..., min_length=1)
    tags_de: list[str] = Field(..., min_length=1)
    availability: bool = True
    popularity_score: float = Field(default=0.5, ge=0, le=1)
    is_promotion: bool = False
    product_url: Optional[str] = None

    @field_validator(
        "product_id",
        "name",
        "name_de",
        "category",
        "description",
        "description_de",
        "brand",
        mode="before",
    )
    @classmethod
    def strip_catalog_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("partner")
    @classmethod
    def require_catalog_partner(cls, value: Partner) -> Partner:
        if value == Partner.UNKNOWN:
            raise ValueError("catalog products must use a concrete partner")
        return value

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("tags", "tags_de")
    @classmethod
    def normalize_tags(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()

        for raw_value in values:
            value = raw_value.strip().casefold()
            if not value:
                continue
            if value not in seen:
                normalized.append(value)
                seen.add(value)

        if not normalized:
            raise ValueError("at least one non-blank tag is required")

        return normalized

    @field_validator("product_url", mode="before")
    @classmethod
    def normalize_product_url(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            if not normalized:
                return None
            if not normalized.startswith(("https://", "http://")):
                raise ValueError("product_url must start with http:// or https://")
            return normalized
        return value

    @model_validator(mode="after")
    def require_partner_prefixed_product_id(self) -> Product:
        expected_prefix = f"{self.partner.value}-"
        if not self.product_id.startswith(expected_prefix):
            raise ValueError(
                f"product_id must start with partner prefix {expected_prefix!r}"
            )
        return self


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
