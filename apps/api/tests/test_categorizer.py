"""Tests for the keyword-based clause categoriser."""

from __future__ import annotations

import pytest

from app.models import ClauseCategory
from app.services.categorizer import categorize_text


@pytest.mark.parametrize(
    "text,expected",
    [
        (
            "The Employee shall not engage in any non-compete activity for 3 years.",
            ClauseCategory.NON_COMPETE,
        ),
        (
            "The Employee shall not solicit any clients of the Company for 12 months.",
            ClauseCategory.NON_SOLICIT,
        ),
        (
            "All inventions and works shall be assigned to and belong to the Company.",
            ClauseCategory.IP_ASSIGNMENT,
        ),
        (
            "Each party agrees to maintain strict confidentiality of trade secrets.",
            ClauseCategory.CONFIDENTIALITY,
        ),
        (
            "Any disputes shall be resolved by binding arbitration in Mumbai.",
            ClauseCategory.ARBITRATION,
        ),
        (
            "This agreement shall be governed by the laws of the State of California.",
            ClauseCategory.JURISDICTION,
        ),
        (
            "In no event shall the Company's aggregate liability exceed the fees paid.",
            ClauseCategory.LIMITATION_OF_LIABILITY,
        ),
        (
            "The Customer shall indemnify and hold harmless the Company from all claims.",
            ClauseCategory.INDEMNITY,
        ),
        (
            "Either party may terminate this agreement upon thirty days notice.",
            ClauseCategory.TERMINATION,
        ),
        (
            "This subscription will automatically renew for successive one-year terms.",
            ClauseCategory.AUTO_RENEWAL,
        ),
        (
            "All fees are due within thirty days of invoice date.",
            ClauseCategory.PAYMENT,
        ),
        (
            "We process your personal data in accordance with GDPR and DPDP requirements.",
            ClauseCategory.DATA_PRIVACY,
        ),
        (
            "Neither party shall be liable for any delay caused by a force majeure event.",
            ClauseCategory.FORCE_MAJEURE,
        ),
        ("This is just some random filler text that matches nothing.", ClauseCategory.OTHER),
    ],
)
def test_categorize(text: str, expected: ClauseCategory) -> None:
    assert categorize_text(text) == expected
