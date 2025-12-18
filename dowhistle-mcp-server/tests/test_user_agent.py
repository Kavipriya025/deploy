import pytest


@pytest.mark.asyncio
async def test_toggle_visibility(monkeypatch, mcp_client, dummy_token):
    monkeypatch.setattr("agents.user.get_access_token", lambda: dummy_token)

    captured = {}

    async def fake_request(method, endpoint, data=None, params=None, headers=None):
        captured["method"] = method
        captured["endpoint"] = endpoint
        captured["data"] = data
        return {
            "user": {
                "_id": "user-1",
                "name": "Test User",
                "phone": "5551234",
                "countryCode": "+1",
                "visible": data["visible"],
            }
        }

    monkeypatch.setattr("agents.user.api_client.request", fake_request)

    result = await mcp_client.call_tool(
        name="toggle_visibility",
        arguments={"visible": "true"},
    )

    assert captured["method"] == "PUT"
    assert captured["endpoint"] == "/user"
    assert captured["data"] == {"visible": True}

    payload = result.data.root
    assert payload["success"] is True
    assert payload["data"]["visible"] is True


@pytest.mark.asyncio
async def test_toggle_visibility_false(monkeypatch, mcp_client, dummy_token):
    """
    Positive: setting visible='false' should send visible=False to backend.
    """
    monkeypatch.setattr("agents.user.get_access_token", lambda: dummy_token)

    captured = {}

    async def fake_request(method, endpoint, data=None, params=None, headers=None):
        captured["data"] = data
        return {
            "user": {
                "_id": "user-1",
                "name": "Test User",
                "phone": "5551234",
                "countryCode": "+1",
                "visible": data["visible"],
            }
        }

    monkeypatch.setattr("agents.user.api_client.request", fake_request)

    result = await mcp_client.call_tool(
        name="toggle_visibility",
        arguments={"visible": "false"},
    )

    payload = result.data.root
    assert captured["data"] == {"visible": False}
    assert payload["data"]["visible"] is False


@pytest.mark.asyncio
async def test_toggle_visibility_unauthorized(monkeypatch, mcp_client):
    # Negative: no access token should result in failure
    monkeypatch.setattr("agents.user.get_access_token", lambda: None)

    result = await mcp_client.call_tool(
        name="toggle_visibility",
        arguments={"visible": "false"},
    )

    payload = result.data.root
    assert payload["success"] is False
    assert "Unauthorized" in payload.get("message", "")


@pytest.mark.asyncio
async def test_get_user_profile(monkeypatch, mcp_client, dummy_token):
    monkeypatch.setattr("agents.user.get_access_token", lambda: dummy_token)

    async def fake_request(method, endpoint, data=None, params=None, headers=None):
        return {
            "user": {
                "_id": "user-1",
                "name": "Test User",
                "phone": "5551234",
                "countryCode": "+1",
                "visible": True,
                "Whistles": [],
            }
        }

    monkeypatch.setattr("agents.user.api_client.request", fake_request)

    result = await mcp_client.call_tool(
        name="get_user_profile",
        arguments={},
    )

    payload = result.data.root
    assert payload["success"] is True
    assert payload["data"]["id"] == "user-1"
    assert payload["data"]["visible"] is True


@pytest.mark.asyncio
async def test_get_user_profile_unauthorized(monkeypatch, mcp_client):
    # Negative: missing token should return an error response
    monkeypatch.setattr("agents.user.get_access_token", lambda: None)

    result = await mcp_client.call_tool(
        name="get_user_profile",
        arguments={},
    )

    payload = result.data.root
    assert payload["success"] is False
    assert "Unauthorized" in payload.get("message", "")

