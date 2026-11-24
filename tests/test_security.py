"""Security checks. A failure here blocks the deploy."""
import asyncio
import logging
import threading
import time

import mcp_types
import pytest
from fastmcp import Client

from conftest import ROOT, TEST_SECRET_PATH


# --------------------------------------------------------------------------- #
# HTTP surface: only the secret path and /health exist
# --------------------------------------------------------------------------- #
def test_only_secret_path_and_health_are_exposed(m):
    app = m.mcp.http_app(path=m.MCP_PATH)
    paths = sorted(getattr(r, "path", "") for r in app.routes)
    assert paths == sorted([TEST_SECRET_PATH, "/health"])


# --------------------------------------------------------------------------- #
# The secret never reaches the logs
# --------------------------------------------------------------------------- #
def test_secret_is_masked_in_every_log_record(m):
    seen = []

    class Grab(logging.Handler):
        def emit(self, record):
            seen.append(record.getMessage())

    log = logging.getLogger("ci-secret-test")
    h = Grab()
    log.addHandler(h)
    log.setLevel(logging.INFO)
    try:
        log.info("POST %s HTTP/1.1", m.MCP_PATH)
        log.info(f"Uvicorn on http://0.0.0.0:10000{m.MCP_PATH}")
    finally:
        log.removeHandler(h)
    assert seen and all(TEST_SECRET_PATH not in s for s in seen)
    assert all("/mcp/***" in s for s in seen)


def test_errors_are_scrubbed(m):
    raw = ("fallo para persona@example.com token=AbCdEf0123456789AbCdEf0123456789xyz "
           "uuid 123e4567-e89b-12d3-a456-426614174000 url https://x.test/a?ticket=secret")
    out = m._scrub(raw)
    for leaked in ("persona@example.com", "AbCdEf0123456789AbCdEf0123456789xyz",
                   "123e4567-e89b-12d3-a456-426614174000", "ticket=secret"):
        assert leaked not in out


# --------------------------------------------------------------------------- #
# Skills: nothing outside the skill folders can be read
# --------------------------------------------------------------------------- #
ATTACKS = [
    "skill://garmin-run-coach/../../garmin_mcp_server.py",
    "skill://garmin-connect-basics/../../garmin_mcp_server.py",
    "skill://garmin-run-coach/%2e%2e/%2e%2e/requirements.txt",
    "skill://garmin-connect-basics/..%2F..%2FDockerfile",
    "skill://../garmin_mcp_server.py",
    "skill://garmin-run-coach/../../../proc/self/environ",
    "skill://garmin-connect-basics/%2E%2E/%2E%2E/%2E%2E/proc/self/environ",
    "skill://etc/passwd",
    "file:///etc/passwd",
    "skill://garmin-run-coach/.env",
]


@pytest.mark.parametrize("uri", ATTACKS)
def test_skill_paths_cannot_escape(m, uri):
    async def read():
        async with Client(m.mcp) as c:
            return await c.read_resource(uri)

    with pytest.raises(Exception):
        asyncio.run(read())


def test_only_expected_files_are_resources(m):
    async def listing():
        async with Client(m.mcp) as c:
            return [str(r.uri) for r in await c.list_resources()]

    uris = asyncio.run(listing())
    assert uris, "the server should publish at least one skill"
    assert all(u.startswith("skill://") for u in uris)
    assert all(u.endswith(("/SKILL.md", "/_manifest")) for u in uris)


def test_paid_coach_never_in_public_repo():
    """The public repo (it has build_exercise_catalog.py) must not ship the paid method."""
    if (ROOT / "build_exercise_catalog.py").exists():
        assert not (ROOT / "skills" / "garmin-run-coach").exists()
        assert not (ROOT / "coach_guide.md").exists()


# --------------------------------------------------------------------------- #
# Deleting workouts: the server asks, and "yes" only covers what was shown
# --------------------------------------------------------------------------- #
WORKOUTS = [{"workoutId": 111, "workoutName": "Thu - Threshold 4x8"},
            {"workoutId": 222, "workoutName": "Sat - Long run"}]


async def _yes(message, response_type, params, context):
    return response_type(value=True)


async def _no(message, response_type, params, context):
    return response_type(value=False)


def _delete(m, ids, **client_kwargs):
    async def run():
        async with Client(m.mcp, **client_kwargs) as c:
            if len(ids) == 1:
                r = await c.call_tool("garmin_delete_workout", {"workout_id": ids[0]})
            else:
                r = await c.call_tool("garmin_delete_workouts", {"workout_ids": ids})
            return r.structured_content
    return asyncio.run(run())


@pytest.mark.parametrize("mode", ["auto", "legacy"])
def test_delete_cancelled_when_user_says_no(m, fake_garmin, mode):
    calls = fake_garmin({"get_workouts": WORKOUTS, "delete_workout": None})
    out = _delete(m, ["111"], mode=mode, elicitation_handler=_no)
    assert out["cancelado"] is True and out["borrados"] == []
    assert not any(c[0] == "delete_workout" for c in calls)


@pytest.mark.parametrize("mode", ["auto", "legacy"])
def test_delete_runs_when_user_says_yes(m, fake_garmin, mode):
    calls = fake_garmin({"get_workouts": WORKOUTS, "delete_workout": None})
    out = _delete(m, ["111", "222"], mode=mode, elicitation_handler=_yes)
    assert out["confirmacion"] == "usuario"
    assert [c[1][0] for c in calls if c[0] == "delete_workout"] == ["111", "222"]


def test_delete_without_prompt_support_keeps_chat_rule(m, fake_garmin):
    fake_garmin({"get_workouts": WORKOUTS, "delete_workout": None})
    out = _delete(m, ["111"])
    assert out["confirmacion"] == "chat"


class _Answer:
    action, content = "accept", {"value": True}


class _Ctx:
    def __init__(self, state):
        self.input_responses = {"confirm_delete": _Answer()}
        self.request_state = state
        caps = type("Caps", (), {"elicitation": object()})()
        self.session = type("Session", (), {"client_capabilities": caps})()

    def _is_modern_protocol(self):
        return True


def test_yes_cannot_be_reused_for_other_workouts(m):
    ok = asyncio.run(m._confirm(_Ctx("delete:111"), "x", "delete:111"))
    replay = asyncio.run(m._confirm(_Ctx("delete:111"), "x", "delete:111,222"))
    unsealed = asyncio.run(m._confirm(_Ctx(None), "x", "delete:111"))
    assert ok == "si"
    assert isinstance(replay, mcp_types.InputRequiredResult)
    assert isinstance(unsealed, mcp_types.InputRequiredResult)


# --------------------------------------------------------------------------- #
# Expired Garmin session under load: exactly one new login
# --------------------------------------------------------------------------- #
def test_single_relogin_under_concurrency(m, monkeypatch):
    logins = []

    class Expired:
        def get_x(self):
            time.sleep(0.05)
            raise m.GarminConnectAuthenticationError("expired")

    class Fresh:
        def get_x(self):
            return "ok"

    def build(force_credentials=False):
        logins.append(1)
        time.sleep(0.2)
        return Fresh()

    monkeypatch.setattr(m, "_client", Expired())
    monkeypatch.setattr(m, "_build_client", build)
    results = []
    threads = [threading.Thread(target=lambda: results.append(m._call("get_x")))
               for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(logins) == 1
    assert results == ["ok"] * 8


# --------------------------------------------------------------------------- #
# Container runs without privileges
# --------------------------------------------------------------------------- #
def test_container_runs_as_unprivileged_user():
    docker = (ROOT / "Dockerfile").read_text()
    assert "USER app" in docker
    assert docker.index("USER app") < docker.index("CMD [")


def test_dependencies_are_pinned_with_hashes():
    req = (ROOT / "requirements.txt").read_text()
    pkgs = [ln for ln in req.splitlines() if ln and not ln.startswith((" ", "#", "-"))]
    assert pkgs, "requirements.txt is empty"
    assert all("==" in ln for ln in pkgs), "every dependency must be pinned with =="
    assert "--hash=sha256:" in req, "requirements.txt must carry hashes"


# --------------------------------------------------------------------------- #
# Rejected login: pause instead of hammering Garmin, and say why
# --------------------------------------------------------------------------- #
def test_login_pauses_after_rejection_and_reports_cause(m, monkeypatch):
    attempts = []

    def build(force_credentials=False):
        attempts.append(force_credentials)
        try:
            raise RuntimeError("429 Too Many Requests")
        except RuntimeError as inner:
            raise m.GarminConnectAuthenticationError("Failed to retrieve social profile") from inner

    monkeypatch.setattr(m, "_client", None)
    monkeypatch.setattr(m, "_build_client", build)
    monkeypatch.setattr(m, "_login_paused_until", 0.0)
    monkeypatch.setattr(m, "_login_pause_reason", "")

    with pytest.raises(m.GarminConnectAuthenticationError) as first:
        m._call("get_x")
    out = m._err(first.value)
    assert "429" in out["error"] and "429" in out["detail"]

    for _ in range(5):                      # every later call stays off Garmin
        with pytest.raises(m.GarminConnectAuthenticationError) as later:
            m._call("get_x")
    assert len(attempts) == 1
    assert "pausa" in m._err(later.value)["error"]


def test_login_pause_ends_and_success_clears_it(m, monkeypatch):
    class Fresh:
        def get_x(self):
            return "ok"

    monkeypatch.setattr(m, "_client", None)
    monkeypatch.setattr(m, "_build_client", lambda force_credentials=False: Fresh())
    monkeypatch.setattr(m, "_login_paused_until", 0.0)   # pause already over
    assert m._call("get_x") == "ok"
    assert m._login_paused_until == 0.0
