"""Tests for the heuristic clause segmenter."""

from __future__ import annotations

from app.services.segmenter import segment


def test_empty_returns_empty() -> None:
    assert segment("") == []
    assert segment("   \n   ") == []


def test_numbered_clauses() -> None:
    text = (
        "1. The Employee shall serve faithfully and perform such duties as may be assigned.\n"
        "2. The Employee shall not engage in any competing business for a period of three years.\n"
        "3. Either party may terminate this agreement by giving thirty days written notice.\n"
        "4. All intellectual property created shall be assigned to the Company without compensation.\n"
    )
    clauses = segment(text)
    assert len(clauses) == 4
    assert all(c.text.startswith(str(i + 1) + ".") for i, c in enumerate(clauses))
    assert clauses[0].index == 0 and clauses[3].index == 3


def test_section_headings() -> None:
    text = (
        "TERMINATION.\n"
        "Either party may terminate this agreement upon thirty days written notice "
        "if the other party materially breaches the agreement and fails to cure.\n\n"
        "LIABILITY.\n"
        "In no event shall either party be liable for indirect, consequential, or "
        "incidental damages arising out of this agreement.\n\n"
        "CONFIDENTIALITY.\n"
        "Each party agrees to maintain in strict confidence all proprietary "
        "information received from the other party for a period of five years.\n"
    )
    clauses = segment(text)
    assert len(clauses) >= 2
    assert any("terminate" in c.text.lower() for c in clauses)
    assert any("liability" in c.text.lower() or "liable" in c.text.lower() for c in clauses)


def test_paragraph_fallback() -> None:
    text = (
        "We collect personal information that you provide when you create an account, "
        "use our services, or contact our support team.\n\n"
        "We share your information with third-party service providers who help us operate "
        "our business, including payment processors and analytics vendors.\n\n"
        "You can request deletion of your account at any time by contacting our privacy team."
    )
    clauses = segment(text)
    assert len(clauses) == 3
    assert clauses[0].index == 0
    # Offsets should be non-decreasing.
    for prev, nxt in zip(clauses, clauses[1:], strict=True):
        assert nxt.start_offset >= prev.start_offset


def test_clause_text_is_capped() -> None:
    text = "1. " + ("very long " * 1000) + "end."
    clauses = segment(text)
    assert clauses, "expected at least one clause"
    assert all(len(c.text) <= 4000 for c in clauses)
