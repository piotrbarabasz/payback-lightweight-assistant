"""Retrieval utilities for the local synthetic product catalog."""

from app.retrieval.base import ProductRetriever
from app.retrieval.factory import get_product_retriever
from app.retrieval.keyword_search import (
    keyword_match_score,
    product_search_text,
    search_products_by_keywords,
)
from app.retrieval.keyword_retriever import KeywordProductRetriever
from app.retrieval.normalizer import QueryAnalysis, is_support_query, normalize_query
from app.retrieval.scorer import calculate_final_score, build_recommendation_reason
from app.retrieval.service import (
    category_hint_from_results,
    product_to_result,
    retrieve_products,
)

__all__ = [
    "ProductRetriever",
    "KeywordProductRetriever",
    "QueryAnalysis",
    "build_recommendation_reason",
    "calculate_final_score",
    "category_hint_from_results",
    "get_product_retriever",
    "is_support_query",
    "keyword_match_score",
    "normalize_query",
    "product_search_text",
    "product_to_result",
    "retrieve_products",
    "search_products_by_keywords",
]
