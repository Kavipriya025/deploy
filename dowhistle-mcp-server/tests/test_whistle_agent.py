import pytest

from agents.whistle import AdvancedLLMExtractor, ExtractedWhistleData


@pytest.mark.asyncio
async def test_create_whistle_success(monkeypatch, mcp_client, dummy_token):
    # Stub authentication to simulate an authorized user
    monkeypatch.setattr("agents.whistle.get_access_token", lambda: dummy_token)

    # Stub OpenAI-based extractor to avoid network calls
    async def fake_extract(self, user_input: str):
        return ExtractedWhistleData(
            description=user_input,
            alert_radius=5,
            tags=["plumbing"],
            provider=True,
            expiry="2030-01-01T00:00:00Z",
            ask_again=False,
            reason="",
            confidence_score=0.95,
        )

    monkeypatch.setattr(
        AdvancedLLMExtractor,
        "extract_attributes",
        fake_extract,
    )

    # Stub backend API client
    async def fake_request(method, endpoint, data=None, params=None, headers=None):
        if endpoint == "/whistle":
            return {
                "newWhistle": {
                    "_id": "whistle-123",
                    "description": data["whistle"]["description"],
                    "tags": data["whistle"]["tags"],
                    "alertRadius": data["whistle"]["alertRadius"],
                    "expiry": data["whistle"]["expiry"],
                    "provider": data["whistle"]["provider"],
                    "active": True,
                },
                "matchingWhistles": [],
            }
        return {}

    monkeypatch.setattr("agents.whistle.api_client.request", fake_request)

    result = await mcp_client.call_tool(
        name="create_whistle",
        arguments={"user_input": "I can fix kitchen sinks", "confidence_threshold": 0.2},
    )

    payload = result.data.root
    assert payload["status"] == "success"
    assert payload["whistle"]["tags"] == ["plumbing"]
    assert payload["whistle"]["provider"] is True
    assert "message" in payload
    assert "Whistle created successfully" in payload["message"]


@pytest.mark.asyncio
async def test_create_whistle_unauthorized(monkeypatch, mcp_client):
    # Negative: no access token should produce an error
    monkeypatch.setattr("agents.whistle.get_access_token", lambda: None)

    result = await mcp_client.call_tool(
        name="create_whistle",
        arguments={"user_input": "I can fix kitchen sinks", "confidence_threshold": 0.2},
    )

    payload = result.data.root
    assert payload["status"] == "error"
    assert "Authentication" in payload["message"] or "sign in" in payload["message"].lower()


@pytest.mark.asyncio
async def test_create_whistle_low_confidence_requires_clarification(monkeypatch, mcp_client, dummy_token):
    """
    If the extractor returns low confidence and ask_again=True,
    the tool should respond with CLARIFICATION_NEEDED.
    """
    from agents.whistle import ProcessingStatus

    monkeypatch.setattr("agents.whistle.get_access_token", lambda: dummy_token)

    async def fake_extract(self, user_input: str):
        return ExtractedWhistleData(
            description=user_input,
            alert_radius=2,
            tags=[],
            provider=None,
            expiry="2030-01-01T00:00:00Z",
            ask_again=True,
            reason="Need more details",
            confidence_score=0.2,
        )

    monkeypatch.setattr(AdvancedLLMExtractor, "extract_attributes", fake_extract)

    result = await mcp_client.call_tool(
        name="create_whistle",
        arguments={"user_input": "help", "confidence_threshold": 0.8},
    )

    payload = result.data.root
    assert payload["status"] == ProcessingStatus.CLARIFICATION_NEEDED.value
    assert "Need more details" in payload["message"]


@pytest.mark.asyncio
async def test_list_whistles(monkeypatch, mcp_client, dummy_token):
    monkeypatch.setattr("agents.whistle.get_access_token", lambda: dummy_token)

    async def fake_request(method, endpoint, data=None, params=None, headers=None):
        return {
            "user": {
                "Whistles": [
                    {
                        "_id": "w1",
                        "description": "Test whistle",
                        "tags": ["help"],
                        "alertRadius": 3,
                        "expiry": "never",
                        "provider": False,
                        "active": True,
                    }
                ]
            }
        }

    monkeypatch.setattr("agents.whistle.api_client.request", fake_request)

    result = await mcp_client.call_tool(name="list_whistles", arguments={"active_only": True})

    payload = result.data.root
    assert payload["status"] == "success"
    assert "message" in payload
    assert "Found" in payload["message"] or "whistle" in payload["message"].lower()
    assert len(payload["whistles"]) == 1
    whistle = payload["whistles"][0]
    assert whistle["id"] == "w1"
    assert whistle["active"] is True


@pytest.mark.asyncio
async def test_list_whistles_unauthorized(monkeypatch, mcp_client):
    # Negative: no token means listing whistles should fail
    monkeypatch.setattr("agents.whistle.get_access_token", lambda: None)

    result = await mcp_client.call_tool(name="list_whistles", arguments={"active_only": True})

    payload = result.data.root
    assert payload["status"] == "error"
    assert "Authentication" in payload["message"] or "sign in" in payload["message"].lower()

