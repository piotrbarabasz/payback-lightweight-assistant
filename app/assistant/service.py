"""API-independent assistant response orchestration."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import replace

from app.catalog.loader import load_products
from app.intent.detector import with_clarifying_action
from app.intent.decision import build_clarifying_question
from app.retrieval import (
    category_hint_from_results,
    get_product_retriever,
    retrieve_products,
)
from app.retrieval.normalizer import (
    PARTNER_TOKENS,
    QueryAnalysis,
    normalize_query,
    tokenize,
)
from app.schemas import (
    AssistantQueryRequest,
    AssistantQueryResponse,
    IntentDetectionResult,
    NextBestAction,
    Partner,
    Product,
    ProductResult,
    QueryEntities,
)


COMPARISON_CRITERIA = [
    "price",
    "partner",
    "category",
    "promotion_status",
    "relevance_score",
]


def build_assistant_response(
    payload: AssistantQueryRequest,
    intent_result: IntentDetectionResult,
) -> AssistantQueryResponse:
    """Build a deterministic assistant response from intent and retrieval."""

    if _should_return_without_retrieval(intent_result.next_best_action):
        if intent_result.next_best_action == NextBestAction.FALLBACK:
            intent_result = _with_fallback_question(intent_result)
        return _response_from_intent_result(intent_result, results=[])

    products = load_products()
    retriever = get_product_retriever()
    is_comparison = intent_result.next_best_action == NextBestAction.COMPARE_PRODUCTS
    requested_partners = _requested_partners(payload.query) if is_comparison else []
    results = retriever.retrieve(
        payload.query,
        products,
        top_k=_retrieval_pool_size(payload.top_k, len(products), is_comparison),
        intent_analysis=_comparison_retrieval_analysis(payload.query)
        if is_comparison
        else None,
    )

    if not results:
        return _response_from_intent_result(
            with_clarifying_action(intent_result),
            results=[],
        )

    if is_comparison:
        results = _select_comparison_results(
            results,
            top_k=payload.top_k,
            requested_partners=requested_partners,
        )
        results = _annotate_comparison_results(results, products)

    return _response_from_intent_result(
        intent_result.model_copy(
            update={
                "partner_hint": _response_partner_hint(
                    intent_result.partner_hint,
                    results,
                    is_comparison,
                    requested_partners,
                ),
                "entities": _entities_from_intent_and_results(
                    intent_result.entities,
                    results,
                ),
            }
        ),
        results=results,
        comparison_summary=_build_comparison_summary(
            results,
            products,
            requested_partners,
        )
        if is_comparison
        else None,
        comparison_criteria=COMPARISON_CRITERIA if is_comparison else [],
    )


def _should_return_without_retrieval(next_best_action: NextBestAction) -> bool:
    return next_best_action in {
        NextBestAction.ASK_CLARIFYING_QUESTION,
        NextBestAction.ROUTE_TO_SUPPORT,
        NextBestAction.FALLBACK,
    }


def _with_fallback_question(
    intent_result: IntentDetectionResult,
) -> IntentDetectionResult:
    if intent_result.clarifying_question is not None:
        return intent_result

    return intent_result.model_copy(
        update={
            "clarifying_question": build_clarifying_question(
                intent_result.intent,
                intent_result.entities,
                intent_result.language,
            )
        }
    )


def _response_from_intent_result(
    intent_result: IntentDetectionResult,
    results: list[ProductResult],
    comparison_summary: str | None = None,
    comparison_criteria: list[str] | None = None,
) -> AssistantQueryResponse:
    return AssistantQueryResponse(
        query=intent_result.query,
        language=intent_result.language,
        intent=intent_result.intent,
        specificity=intent_result.specificity,
        next_best_action=intent_result.next_best_action,
        clarifying_question=intent_result.clarifying_question,
        partner_hint=intent_result.partner_hint,
        entities=intent_result.entities,
        results=results,
        comparison_summary=comparison_summary,
        comparison_criteria=comparison_criteria or [],
    )


def _partner_hint_from_results(
    query_partner_hint: Partner | None,
    results: list[ProductResult],
) -> Partner:
    if query_partner_hint is not None and query_partner_hint != Partner.UNKNOWN:
        return query_partner_hint
    if not results:
        return Partner.UNKNOWN

    first_partner = results[0].partner
    if all(result.partner == first_partner for result in results):
        return first_partner
    return Partner.UNKNOWN


def _response_partner_hint(
    query_partner_hint: Partner | None,
    results: list[ProductResult],
    is_comparison: bool,
    requested_partners: list[Partner],
) -> Partner:
    if is_comparison and len(requested_partners) > 1:
        return Partner.UNKNOWN
    if is_comparison and not requested_partners:
        return _partner_hint_from_results(None, results)
    return _partner_hint_from_results(query_partner_hint, results)


def _entities_from_intent_and_results(
    entities: QueryEntities,
    results: list[ProductResult],
) -> QueryEntities:
    if entities.product_category is not None:
        return entities

    category_hint = category_hint_from_results(results)
    if category_hint is None:
        return entities

    return entities.model_copy(update={"product_category": category_hint})


def _comparison_retrieval_analysis(query: str) -> QueryAnalysis:
    """Keep comparison retrieval broad enough to compare partners."""

    return replace(normalize_query(query), partner_hint=None)


def _retrieval_pool_size(top_k: int, product_count: int, is_comparison: bool) -> int:
    if not is_comparison:
        return top_k
    return min(product_count, max(top_k, top_k * 3))


def _requested_partners(query: str) -> list[Partner]:
    partners: list[Partner] = []
    seen: set[Partner] = set()
    for token in tokenize(query):
        partner = PARTNER_TOKENS.get(token)
        if partner is not None and partner not in seen:
            partners.append(partner)
            seen.add(partner)
    return partners


def _select_comparison_results(
    results: list[ProductResult],
    top_k: int,
    requested_partners: list[Partner],
) -> list[ProductResult]:
    if not requested_partners:
        return results[:top_k]

    selected: list[ProductResult] = []
    selected_ids: set[str] = set()
    for partner in requested_partners:
        partner_result = next(
            (result for result in results if result.partner == partner),
            None,
        )
        if partner_result is not None:
            selected.append(partner_result)
            selected_ids.add(partner_result.product_id)

    for result in results:
        if len(selected) >= top_k:
            break
        if result.product_id not in selected_ids:
            selected.append(result)
            selected_ids.add(result.product_id)

    return selected


def _annotate_comparison_results(
    results: list[ProductResult],
    products: list[Product],
) -> list[ProductResult]:
    products_by_id = {product.product_id: product for product in products}
    annotated_results: list[ProductResult] = []

    for result in results:
        product = products_by_id.get(result.product_id)
        promotion_text = ""
        if product is not None:
            promotion_text = (
                "promotion status (promotion)"
                if product.is_promotion
                else "promotion status (not on promotion)"
            )
        else:
            promotion_text = "promotion status (unavailable)"

        comparison_reason = (
            "Included for comparison on "
            f"partner ({result.partner.value}), category ({result.category}), "
            f"price ({_format_price(result.price, result.currency)}), "
            f"{promotion_text}, and relevance score ({result.score:.2f})."
        )
        reason = (
            f"{comparison_reason} {result.reason}"
            if result.reason
            else comparison_reason
        )
        annotated_results.append(result.model_copy(update={"reason": reason}))

    return annotated_results


def _build_comparison_summary(
    results: list[ProductResult],
    products: list[Product],
    requested_partners: list[Partner],
) -> str | None:
    if not results:
        return None

    products_by_id = {product.product_id: product for product in products}
    groups: dict[Partner, list[ProductResult]] = defaultdict(list)
    for result in results:
        groups[result.partner].append(result)

    ordered_partners = [
        partner for partner in requested_partners if partner in groups
    ] + sorted(
        (partner for partner in groups if partner not in requested_partners),
        key=lambda partner: partner.value,
    )
    cheapest = min(results, key=lambda result: (result.price, -result.score))
    parts = [
        "Compared returned products by partner using price, category, "
        "promotion status, and relevance score.",
        "Cheapest returned option is "
        f"{cheapest.name} from {cheapest.partner.value} at "
        f"{_format_price(cheapest.price, cheapest.currency)}.",
    ]

    partner_summaries = [
        _partner_comparison_summary(partner, groups[partner], products_by_id)
        for partner in ordered_partners
    ]
    if partner_summaries:
        parts.append(" ".join(partner_summaries))

    missing_requested_partners = [
        partner.value for partner in requested_partners if partner not in groups
    ]
    if missing_requested_partners:
        parts.append(
            "No returned matches for requested partner(s): "
            f"{', '.join(missing_requested_partners)}."
        )

    return " ".join(parts)


def _partner_comparison_summary(
    partner: Partner,
    results: list[ProductResult],
    products_by_id: dict[str, Product],
) -> str:
    cheapest = min(results, key=lambda result: (result.price, -result.score))
    top_score = max(result.score for result in results)
    categories = ", ".join(sorted({result.category for result in results}))
    promotion_count = sum(
        1
        for result in results
        if getattr(products_by_id.get(result.product_id), "is_promotion", False)
    )
    return (
        f"{partner.value}: {len(results)} result(s), cheapest "
        f"{_format_price(cheapest.price, cheapest.currency)}, top score "
        f"{top_score:.2f}, categories {categories}, promotions "
        f"{promotion_count}."
    )


def _format_price(price: float, currency: str) -> str:
    return f"{price:.2f} {currency}"
