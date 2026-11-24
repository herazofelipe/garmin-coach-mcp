"""Core behaviour: tools, skills, tasks, HRV analysis. Garmin is mocked."""
import asyncio
import json
import math
import os
import random
from datetime import date, timedelta

import pytest
from fastmcp import Client

from conftest import ROOT

SNAPSHOT = ROOT / "tests" / "tool_schemas.json"


def _tools(m):
    async def run():
        async with Client(m.mcp) as c:
            return await c.list_tools()
    return asyncio.run(run())


def test_tool_parameters_match_snapshot(m):
    """Any change to tool names or parameters shows up here: after an intended change,
    regenerate with UPDATE_SNAPSHOT=1 and refresh the connector in claude.ai."""
    current = {t.name: t.input_schema for t in _tools(m)}
    if os.environ.get("UPDATE_SNAPSHOT") == "1" or not SNAPSHOT.exists():
        SNAPSHOT.write_text(json.dumps(current, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    assert current == json.loads(SNAPSHOT.read_text())


def test_no_tool_exposes_a_context_parameter(m):
    for t in _tools(m):
        assert "ctx" not in (t.input_schema or {}).get("properties", {}), t.name


def test_slow_tools_support_background_tasks(m):
    async def modes():
        return {n: (await m.mcp.get_tool(n)).task_config.mode
                for n in ("garmin_get_trend", "garmin_get_readiness_range", "garmin_hrv_analysis")}
    assert set(asyncio.run(modes()).values()) == {"optional"}


def test_published_skills_are_valid_and_match_digest(m):
    import hashlib

    from fastmcp.skills import SkillsClientExtension

    async def run():
        async with Client(m.mcp, extensions=[SkillsClientExtension()]) as c:
            listing = await c.list_skills_mcp()
            out = []
            for sk in listing.skills:
                body = (await c.read_resource(sk.uri))[0].text
                out.append((sk, body))
            return out

    skills = asyncio.run(run())
    assert skills
    for sk, body in skills:
        digest = "sha256:" + hashlib.sha256(body.encode()).hexdigest()
        assert sk.resources[0].digest == digest
        assert body.startswith("---\nname: ")


def test_coach_guide_tool_matches_skill_when_present(m):
    coach = ROOT / "skills" / "garmin-run-coach" / "SKILL.md"
    names = {t.name for t in _tools(m)}
    if not coach.exists():
        assert "garmin_coach_guide" not in names
        return
    out = m.garmin_coach_guide()
    assert "name: garmin-run-coach" not in out["text"]          # frontmatter stripped
    assert out["text"].strip() in coach.read_text()
    assert m.garmin_coach_guide(section="planning")["text"].startswith("## Appendix - Planning")


# --------------------------------------------------------------------------- #
# HRV analysis against the runner's own range (synthetic nights)
# --------------------------------------------------------------------------- #
END = date(2026, 11, 24)
_rnd = random.Random(7)
_n1 = {(END - timedelta(days=i)).isoformat(): _rnd.gauss(0, 1) for i in range(80)}
_n2 = {(END - timedelta(days=i)).isoformat(): _rnd.gauss(0, 1) for i in range(80)}


def _back(d):
    return (END - d).days


def _hrv(d):
    return 55 * math.exp(0.10 * _n1[d.isoformat()])


def _hr(d):
    return 50 - 1.5 * _n1[d.isoformat()] + 0.5 * _n2[d.isoformat()]


SCENARIOS = {
    "estable": (_hrv, _hr, ("estable", "inestable")),
    "fatiga": (lambda d: _hrv(d) * (0.78 if _back(d) < 7 else 1), _hr, ("fatiga_acumulada",)),
    "estres": (lambda d: _hrv(d) * (0.75 if _back(d) < 7 else 1),
               lambda d: _hr(d) + (6 if _back(d) < 7 else 0), ("estres_grande",)),
    "saturacion": (lambda d: 48 * math.exp(0.05 * _n2[d.isoformat()]) if _back(d) < 21 else _hrv(d),
                   lambda d: 45 + 0.8 * _n1[d.isoformat()] if _back(d) < 21 else _hr(d),
                   ("saturacion_o_fatiga",)),
    "alta": (lambda d: _hrv(d) * (1.3 if _back(d) < 7 else 1),
             lambda d: _hr(d) - (5 if _back(d) < 7 else 0), ("vfc_anormalmente_alta",)),
    "pocos_datos": (lambda d: _hrv(d) if _back(d) < 12 else None, _hr, ("sin_vfc",)),
    "sin_vfc": (lambda d: None, _hr, ("sin_vfc",)),
}


def _days(a, b):
    d = date.fromisoformat(a)
    while d <= date.fromisoformat(b):
        yield d
        d += timedelta(days=1)


@pytest.mark.parametrize("name", list(SCENARIOS))
def test_hrv_patterns(m, fake_garmin, name):
    hrv_fn, hr_fn, expected = SCENARIOS[name]

    def hrv_range(a, b):
        return {"hrvSummaries": [{"calendarDate": d.isoformat(), "lastNightAvg": round(v)}
                                 for d in _days(a, b) if (v := hrv_fn(d)) is not None]}

    fake_garmin({
        "get_hrv_data_range": hrv_range,
        "get_rhr_daily": lambda a, b: [{"calendarDate": d.isoformat(), "value": round(hr_fn(d))}
                                       for d in _days(a, b)],
        "get_hrv_data": {}, "get_rhr_day": {},
    })
    r = m.garmin_hrv_analysis(END.isoformat())
    assert "error" not in r, r
    assert r["pattern"] in expected
    assert r["disclaimer"]


def test_trend_runs_as_background_task(m, fake_garmin):
    from fastmcp_tasks import call_tool_task

    fake_garmin({"get_hrv_data_range": lambda a, b: {"hrvSummaries": [
        {"calendarDate": d.isoformat(), "lastNightAvg": 40} for d in _days(a, b)]}})
    args = {"metric": "hrv", "start_date": "2026-09-01", "end_date": "2026-10-30"}

    async def run():
        async with Client(m.mcp) as c:
            plain = (await c.call_tool("garmin_get_trend", args)).structured_content
            task = await call_tool_task(c, "garmin_get_trend", args)
            done = (await task.result()).structured_content
            return plain, done

    plain, done = asyncio.run(run())
    assert plain["count"] == done["count"] == 60
