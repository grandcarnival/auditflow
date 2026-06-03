from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Protocol


class FindingLike(Protocol):
    title: str
    risk_rating: str | None
    condition: str | None
    recommendation: str | None


@dataclass(frozen=True)
class ReplacementOperation:
    source_text: str
    target_text: str
    reason: str
    confidence: float
    source_fields: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DeckContentMap:
    replacements: list[ReplacementOperation]
    warnings: list[str]
    confidence: float
    blocked: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "replacements": [replacement.to_dict() for replacement in self.replacements],
            "warnings": self.warnings,
            "confidence": self.confidence,
            "blocked": self.blocked,
        }


def build_mvp_content_map(
    fiscal_year: int,
    findings: list[FindingLike],
) -> DeckContentMap:
    warnings: list[str] = []
    replacements = [
        ReplacementOperation(
            source_text="FY2025 Audit Committee",
            target_text=f"FY{fiscal_year} Audit Committee",
            reason="Update cover year from prior-year template.",
            confidence=1.0,
            source_fields=["fiscal_year"],
        )
    ]

    high_risk_open = [
        finding
        for finding in findings
        if (finding.risk_rating or "").strip().lower() == "high"
    ]
    if high_risk_open:
        replacements.append(
            ReplacementOperation(
                source_text="Three high-priority findings remain open.",
                target_text=_finding_count_phrase(len(high_risk_open)),
                reason="Update executive summary high-priority finding count from findings workbook.",
                confidence=0.95,
                source_fields=["findings.risk_rating"],
            )
        )
    else:
        warnings.append("No high-risk findings found; executive summary count was not replaced.")

    first = findings[0] if findings else None
    if first:
        replacements.extend([
            ReplacementOperation(
                source_text="Finding Detail | Access Governance",
                target_text=f"Finding Detail | {first.title}",
                reason="Map first MVP finding into the prior-year finding detail slide.",
                confidence=_field_confidence([first.title]),
                source_fields=["findings[0].title"],
            ),
            ReplacementOperation(
                source_text="Condition: Quarterly access reviews were not consistently evidenced.\nRisk: Unauthorized access may persist beyond acceptable timeframes.\nRecommendation: Standardize evidence capture and escalation.",
                target_text=_finding_body(first),
                reason="Replace prior-year finding body with current-year finding fields.",
                confidence=_field_confidence([first.condition, first.risk_rating, first.recommendation]),
                source_fields=["findings[0].condition", "findings[0].risk_rating", "findings[0].recommendation"],
            ),
        ])
    else:
        warnings.append("No findings provided; finding detail slide was not replaced.")

    confidence = round(min(operation.confidence for operation in replacements), 3) if replacements else 0.0
    blocked = confidence < 0.6
    if blocked:
        warnings.append("Content map confidence is below the deterministic execution threshold.")

    return DeckContentMap(replacements=replacements, warnings=warnings, confidence=confidence, blocked=blocked)


def _finding_body(finding: FindingLike) -> str:
    parts = [
        f"Condition: {finding.condition or 'Not provided.'}",
        f"Risk: {finding.risk_rating or 'Not rated.'}",
        f"Recommendation: {finding.recommendation or 'Not provided.'}",
    ]
    return "\n".join(parts)


def _number_word(value: int) -> str:
    words = {
        0: "No",
        1: "One",
        2: "Two",
        3: "Three",
        4: "Four",
        5: "Five",
    }
    return words.get(value, str(value))


def _finding_count_phrase(value: int) -> str:
    if value == 1:
        return "One high-priority finding remains open."
    return f"{_number_word(value)} high-priority findings remain open."


def _field_confidence(values: list[str | None]) -> float:
    present = sum(1 for value in values if value and value.strip())
    if not values:
        return 0.0
    return round(present / len(values), 3)
