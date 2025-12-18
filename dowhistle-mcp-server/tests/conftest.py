import os
import pytest

from fastmcp.client import Client

# Ensure required settings exist before the app is imported
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("EXPRESS_API_BASE_URL", "http://localhost:8000")

from app import create_app  # noqa: E402


@pytest.fixture(scope="session")
def mcp_server():
    app = create_app()
    return app.state.mcp


@pytest.fixture
async def mcp_client(mcp_server):
    async with Client(transport=mcp_server) as client:
        yield client


@pytest.fixture
def dummy_token():
    class _Token:
        def __init__(self):
            self.claims = {"sub": "test-user"}
            self.client_id = "test-user"

    return _Token()

