from app.assistant import service as assistant_service
from app.intent.service import analyze_query_intent
from app.schemas import AssistantQueryRequest


def test_support_query_does_not_call_retrieval(monkeypatch) -> None:
    def fail_retrieval(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("support queries must not call retrieval")

    monkeypatch.setattr(assistant_service, "retrieve_products", fail_retrieval)

    payload = AssistantQueryRequest(query="Meine PAYBACK Punkte fehlen")
    response = assistant_service.build_assistant_response(
        payload,
        analyze_query_intent(payload.query),
    )

    assert response.next_best_action == "route_to_support"
    assert response.results == []


def test_vague_query_does_not_call_retrieval(monkeypatch) -> None:
    def fail_retrieval(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("vague queries must not call retrieval")

    monkeypatch.setattr(assistant_service, "retrieve_products", fail_retrieval)

    payload = AssistantQueryRequest(query="Something nice")
    response = assistant_service.build_assistant_response(
        payload,
        analyze_query_intent(payload.query),
    )

    assert response.next_best_action == "ask_clarifying_question"
    assert response.clarifying_question is not None
    assert response.results == []
