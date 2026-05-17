"""Tests for individual agent functions using the StubLLMClient."""

from __future__ import annotations

import pytest

from app.agents.defender import run_defender
from app.agents.judge import run_judge
from app.agents.negotiator import run_negotiator, should_negotiate
from app.agents.prosecutor import run_prosecutor
from app.agents.state import (
    ClauseState,
    DefenderOutput,
    JudgeOutput,
    NegotiatorOutput,
    ProsecutorOutput,
)
from app.models import Clause, ClauseCategory, DocumentType, Severity
from app.services.vertex import ModelTier
from tests.stubs import StubLLMClient


def _clause() -> Clause:
    return Clause(
        id="c1",
        index=0,
        text="The Employee shall not engage in any non-compete activity for 3 years.",
        category=ClauseCategory.NON_COMPETE,
        start_offset=0,
        end_offset=70,
    )


def _state() -> ClauseState:
    return {"clause": _clause(), "document_type": DocumentType.OFFER_LETTER}


@pytest.mark.asyncio
async def test_prosecutor_uses_flash() -> None:
    client = StubLLMClient()
    out = await run_prosecutor(_state(), client=client)
    assert isinstance(out["prosecutor"], ProsecutorOutput)
    assert client.calls[0]["tier"] == ModelTier.FLASH
    assert client.calls[0]["schema"] == "ProsecutorOutput"


@pytest.mark.asyncio
async def test_defender_reads_prosecutor() -> None:
    client = StubLLMClient()
    state = _state()
    state["prosecutor"] = ProsecutorOutput(
        preliminary_severity=Severity.HIGH,
        argument="Non-compete is unenforceable in India under §27.",
        concerns=["§27 ICA"],
    )
    out = await run_defender(state, client=client)
    assert isinstance(out["defender"], DefenderOutput)
    assert "Non-compete is unenforceable" in str(client.calls[0]["user"])


@pytest.mark.asyncio
async def test_judge_flash_by_default() -> None:
    client = StubLLMClient()
    state = _state()
    state["prosecutor"] = ProsecutorOutput(
        preliminary_severity=Severity.HIGH, argument="x" * 30
    )
    state["defender"] = DefenderOutput(argument="y" * 30)
    await run_judge(state, client=client)
    assert client.calls[-1]["tier"] == ModelTier.FLASH


@pytest.mark.asyncio
async def test_judge_pro_when_flagged() -> None:
    client = StubLLMClient()
    state = _state()
    state["prosecutor"] = ProsecutorOutput(
        preliminary_severity=Severity.CRITICAL, argument="x" * 30
    )
    state["defender"] = DefenderOutput(argument="y" * 30)
    state["use_pro_judge"] = True
    await run_judge(state, client=client)
    assert client.calls[-1]["tier"] == ModelTier.PRO


def test_should_negotiate_threshold() -> None:
    state: ClauseState = _state()
    assert should_negotiate(state) is False  # no judge yet
    for sev, expected in [
        (Severity.INFO, False),
        (Severity.LOW, False),
        (Severity.MEDIUM, True),
        (Severity.HIGH, True),
        (Severity.CRITICAL, True),
    ]:
        state["judge"] = JudgeOutput(
            severity=sev,
            risk_score=50,
            plain_english="x" * 30,
            reasoning="y" * 30,
        )
        assert should_negotiate(state) is expected, sev


@pytest.mark.asyncio
async def test_negotiator_returns_redline() -> None:
    client = StubLLMClient()
    state = _state()
    state["judge"] = JudgeOutput(
        severity=Severity.HIGH,
        risk_score=70,
        plain_english="This is a high-risk clause.",
        reasoning="x" * 40,
    )
    out = await run_negotiator(state, client=client)
    assert isinstance(out["negotiator"], NegotiatorOutput)
    assert out["negotiator"].suggested_redline
