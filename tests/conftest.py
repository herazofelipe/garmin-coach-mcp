"""Shared setup: import the server once, with a test secret and no Garmin account.

Garmin is never contacted: every test replaces `_call` with a fake.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_SECRET_PATH = "/mcp/ci-test-secret-4f9a2c"

os.environ["HOST"] = "127.0.0.1"
os.environ["MCP_PATH"] = TEST_SECRET_PATH
for var in ("GARMIN_EMAIL", "GARMIN_PASSWORD", "GARMIN_TOKENS", "MCP_SECRET"):
    os.environ.pop(var, None)
sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402

import garmin_mcp_server as server  # noqa: E402


@pytest.fixture(scope="session")
def m():
    return server


@pytest.fixture
def fake_garmin(monkeypatch):
    """Install a fake Garmin backend. Usage: fake_garmin({"method": fn_or_value})."""
    def install(handlers: dict):
        calls = []

        def fake(method, *args, **kwargs):
            calls.append((method, args))
            if method not in handlers:
                raise AttributeError(method)
            h = handlers[method]
            return h(*args, **kwargs) if callable(h) else h

        monkeypatch.setattr(server, "_call", fake)
        return calls
    return install
