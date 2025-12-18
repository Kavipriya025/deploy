import pytest

from config.strings import WORKOS_HEADER


@pytest.mark.asyncio
async def test_search_requires_auth(monkeypatch, mcp_client):
    monkeypatch.setattr("agents.search.get_access_token", lambda: None)

    result = await mcp_client.call_tool(
        name="search_businesses",
        arguments={
            "latitude": 0.0,
            "longitude": 0.0,
            "radius": 5,
            "keyword": "coffee",
            "limit": 3,
        },
    )

    payload = result.data.root  # FastMCP wraps JSON in a Root model
    assert payload["error"] == "Unauthorized: No access token provided"
    assert payload["providers"] == []


@pytest.mark.asyncio
async def test_search_success(monkeypatch, mcp_client, dummy_token):
    monkeypatch.setattr("agents.search.get_access_token", lambda: dummy_token)

    captured = {}

    async def fake_request(method, endpoint, data=None, params=None, headers=None):
        captured["method"] = method
        captured["endpoint"] = endpoint
        captured["data"] = data
        captured["headers"] = headers
        return {
            "providers": [
                {
                    "id": "p1",
                    "name": "Coffee Spot",
                    "countryCode": "+1",
                    "phone": "5551234",
                    "address": "123 Bean St",
                    "distance": 1.2,
                    "latitude": 12.34,
                    "longitude": 56.78,
                    "rating": 4.5,
                }
            ]
        }

    monkeypatch.setattr("agents.search.api_client.request", fake_request)

    result = await mcp_client.call_tool(
        name="search_businesses",
        arguments={
            "latitude": 12.34,
            "longitude": 56.78,
            "radius": 10,
            "keyword": "coffee",
            "limit": 5,
        },
    )

    payload = result.data.root
    providers = payload["providers"]

    assert captured["method"] == "POST"
    assert captured["endpoint"] == "/searchAround"
    assert captured["headers"][WORKOS_HEADER] == dummy_token.client_id
    assert payload["total_count"] == 1
    assert providers[0]["name"] == "Coffee Spot"
    assert providers[0]["distance"] == 1.2


@pytest.mark.asyncio
async def test_search_keyword_sanitization(monkeypatch, mcp_client, dummy_token):
    """
    Ensure that keywords containing '|' are sanitized down to a single value.
    """
    monkeypatch.setattr("agents.search.get_access_token", lambda: dummy_token)

    captured = {}

    async def fake_request(method, endpoint, data=None, params=None, headers=None):
        captured["data"] = data
        return {"providers": []}

    monkeypatch.setattr("agents.search.api_client.request", fake_request)

    await mcp_client.call_tool(
        name="search_businesses",
        arguments={
            "latitude": 1.0,
            "longitude": 2.0,
            "radius": 10,
            "keyword": "coffee|tea",
            "limit": 5,
        },
    )

    # The server should have sanitized "coffee|tea" → "coffee"
    assert captured["data"]["keyword"] == "coffee"

