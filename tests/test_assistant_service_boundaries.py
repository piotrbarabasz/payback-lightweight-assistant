from app.agents.assistant import AssistantAgent
from app.assistant import service as assistant_service
from app.intent.service import analyze_query_intent
from app.schemas import AssistantQueryRequest


def test_assistant_service_delegates_to_assistant_agent(monkeypatch) -> None:
    payload = AssistantQueryRequest(query="Show me baby diapers")
    intent_result = analyze_query_intent(payload.query)
    expected_response = object()
    calls = {}

    class FakeAssistantAgent:
        def respond(self, payload_arg, intent_arg):
            calls["payload"] = payload_arg
            calls["intent_result"] = intent_arg
            return expected_response

    monkeypatch.setattr(assistant_service, "AssistantAgent", FakeAssistantAgent)

    response = assistant_service.build_assistant_response(payload, intent_result)

    assert response is expected_response
    assert calls == {"payload": payload, "intent_result": intent_result}


def test_support_query_does_not_call_retrieval() -> None:
    def fail_retriever_factory():
        raise AssertionError("support queries must not call retrieval")

    payload = AssistantQueryRequest(query="Meine PAYBACK Punkte fehlen")
    response = AssistantAgent(
        retriever_factory=fail_retriever_factory,
    ).respond(
        payload,
        analyze_query_intent(payload.query),
    )

    assert response.next_best_action == "route_to_support"
    assert response.results == []


def test_vague_query_does_not_call_retrieval() -> None:
    def fail_retriever_factory():
        raise AssertionError("vague queries must not call retrieval")

    payload = AssistantQueryRequest(query="Something nice")
    response = AssistantAgent(
        retriever_factory=fail_retriever_factory,
    ).respond(
        payload,
        analyze_query_intent(payload.query),
    )

    assert response.next_best_action == "ask_clarifying_question"
    assert response.clarifying_question is not None
    assert response.results == []
