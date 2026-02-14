from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Literal

LaneLiteral = Literal["low_risk", "medium_risk", "high_risk"]


class DeploymentLane(Enum):
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"


@dataclass
class Author:
    id: str
    domain_familiarity_score: float
    past_success_rate: float


@dataclass
class ChangeMetadata:
    lines_added: int
    lines_removed: int
    files_modified: List[str]
    cyclomatic_complexity_delta: float


@dataclass
class EnvironmentHealth:
    status: Literal["healthy", "degraded", "critical"]
    open_incidents: int


@dataclass
class SecurityScan:
    passed: bool


@dataclass
class AssessmentRequest:
    commit_id: str
    author: Author
    change_metadata: ChangeMetadata
    environment_health: EnvironmentHealth
    security_scan: SecurityScan

    @staticmethod
    def from_payload(payload: Dict) -> "AssessmentRequest":
        payload = payload.get("request", payload)
        author = payload["author"]
        change = payload["change_metadata"]
        health = payload["environment_health"]
        return AssessmentRequest(
            commit_id=payload["commit_id"],
            author=Author(
                id=author["id"],
                domain_familiarity_score=float(author.get("domain_familiarity_score", 0.0)),
                past_success_rate=float(author.get("past_success_rate", 0.0)),
            ),
            change_metadata=ChangeMetadata(
                lines_added=int(change.get("lines_added", 0)),
                lines_removed=int(change.get("lines_removed", 0)),
                files_modified=list(change.get("files_modified", [])),
                cyclomatic_complexity_delta=float(change.get("cyclomatic_complexity_delta", 0.0)),
            ),
            environment_health=EnvironmentHealth(
                status=health.get("status", "healthy"),
                open_incidents=int(health.get("open_incidents", 0)),
            ),
            security_scan=SecurityScan(
                passed=bool(payload.get("security_scan_passed", True))
            ),
        )


@dataclass
class RiskFactor:
    vector: str
    impact_percentage: float
    description: str


@dataclass
class AssessmentResponse:
    confidence_score: float
    assigned_lane: LaneLiteral
    risk_factors: List[RiskFactor]
    recommended_actions: List[str]
    is_security_compliant: bool
