"""Keyword-based clause categorisation.

Rough by design: it gives the downstream agents (Phase 3) a strong prior
without spending a Vertex call per clause. The LLM extractor can override it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.models import Clause, ClauseCategory


@dataclass(frozen=True, slots=True)
class _Rule:
    category: ClauseCategory
    # Order rules from most-specific to most-general; first hit wins.
    patterns: tuple[re.Pattern[str], ...]


def _p(regex: str) -> re.Pattern[str]:
    return re.compile(regex, re.IGNORECASE)


_RULES: tuple[_Rule, ...] = (
    _Rule(
        ClauseCategory.NON_COMPETE,
        (_p(r"non[\s-]?compete"), _p(r"shall not.*(?:engage|work|compete)")),
    ),
    _Rule(
        ClauseCategory.NON_SOLICIT,
        (_p(r"non[\s-]?solicit"), _p(r"shall not (?:solicit|hire|poach)")),
    ),
    _Rule(
        ClauseCategory.IP_ASSIGNMENT,
        (
            _p(r"(?:intellectual property|inventions|works).{0,40}(?:assign|vest|belong)"),
            _p(r"work[\s-]?for[\s-]?hire"),
        ),
    ),
    _Rule(
        ClauseCategory.CONFIDENTIALITY,
        (_p(r"confidential(?:ity)?"), _p(r"non[\s-]?disclosure")),
    ),
    _Rule(
        ClauseCategory.ARBITRATION,
        (_p(r"arbitrat(?:ion|or)"), _p(r"binding arbitration")),
    ),
    _Rule(
        ClauseCategory.JURISDICTION,
        (
            _p(r"jurisdiction"),
            _p(r"governing law"),
            _p(r"courts? of [A-Z]"),
        ),
    ),
    _Rule(
        ClauseCategory.LIMITATION_OF_LIABILITY,
        (
            _p(r"limit(?:ation)? of liability"),
            _p(r"in no event shall.{0,40}(?:be liable|liability)"),
            _p(r"aggregate liability"),
        ),
    ),
    _Rule(
        ClauseCategory.INDEMNITY,
        (_p(r"indemnif(?:y|ication)"), _p(r"hold harmless")),
    ),
    _Rule(
        ClauseCategory.LIABILITY,
        (_p(r"liab(?:le|ility)"),),
    ),
    _Rule(
        ClauseCategory.TERMINATION,
        (
            _p(r"terminat(?:e|ion)"),
            _p(r"right to terminate"),
            _p(r"notice period"),
        ),
    ),
    _Rule(
        ClauseCategory.AUTO_RENEWAL,
        (
            _p(r"auto[\s-]?renew"),
            _p(r"automatically renew"),
            _p(r"renewal term"),
        ),
    ),
    _Rule(
        ClauseCategory.PAYMENT,
        (
            _p(r"\b(?:fees?|charges?|invoice|payment|payable|pricing)\b"),
            _p(r"\bdue (?:within|on)\b"),
        ),
    ),
    _Rule(
        ClauseCategory.DATA_PRIVACY,
        (
            _p(r"personal (?:data|information)"),
            _p(r"data (?:protection|processing|controller|processor)"),
            _p(r"GDPR|DPDP"),
        ),
    ),
    _Rule(
        ClauseCategory.FORCE_MAJEURE,
        (_p(r"force majeure"), _p(r"act of god")),
    ),
)


def categorize_text(text: str) -> ClauseCategory:
    """Return the first matching category, or OTHER if nothing hits."""
    for rule in _RULES:
        for pattern in rule.patterns:
            if pattern.search(text):
                return rule.category
    return ClauseCategory.OTHER


def categorize_clauses(clauses: list[Clause]) -> list[Clause]:
    """Mutates each clause's `category` in-place and returns the list."""
    for clause in clauses:
        clause.category = categorize_text(clause.text)
    return clauses
