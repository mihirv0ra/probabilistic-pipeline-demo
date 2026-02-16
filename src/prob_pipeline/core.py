from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .models import (
    AssessmentRequest,
    AssessmentResponse,
    DeploymentLane,
    RiskFactor,
)


@dataclass
class _SignalOutcome:
    name: str
    delta: float
    completeness: float
    description: str
    requires_pessimism: bool = False


class RiskInferenceEngine:
    def __init__(self, base_prior: float = 0.1, pessimism_bias: float = 0.15):
        self.base_prior = base_prior
        self.pessimism_bias = pessimism_bias

    def assess(self, request: AssessmentRequest) -> AssessmentResponse:
        signals = self._collect_signals(request)
        score = self.base_prior
        risk_factors: List[RiskFactor] = []

        for signal in signals:
            delta = signal.delta
            if signal.requires_pessimism or signal.completeness < 0.6:
                score += self.pessimism_bias
                reason = f"{signal.name}: +{self.pessimism_bias:.2f} (missing or incomplete data)"
                risk_factors.append(
                    RiskFactor(
                        vector=signal.name,
                        impact_percentage=round(self.pessimism_bias * 100, 2),
                        description=reason,
                    )
                )
                continue

            score += delta
            risk_factors.append(
                RiskFactor(
                    vector=signal.name,
                    impact_percentage=round(delta * 100, 2),
                    description=signal.description,
                )
            )

        score = min(score, 1.0)
        confidence_score = round(score * 100, 2)
        lane = self._map_lane(score)
        recommended_actions = self._lookup_actions(lane)
        compliance = request.security_scan.passed

        if not compliance:
            lane = DeploymentLane.HIGH_RISK
            recommended_actions = [
                "Run security/compliance scans and wait for green",
                "Do not proceed until senior review signs off",
            ]
            risk_factors.append(
                RiskFactor(
                    vector="security_scan",
                    impact_percentage=100.0,
                    description="Security/compliance scan failed or missing; hard floor triggered",
                )
            )

        return AssessmentResponse(
            confidence_score=confidence_score,
            assigned_lane=lane.value,
            risk_factors=risk_factors,
            recommended_actions=recommended_actions,
            is_security_compliant=compliance,
        )

    def _collect_signals(self, request: AssessmentRequest) -> List[_SignalOutcome]:
        signals: List[_SignalOutcome] = []
        signals.append(self._code_churn_signal(request.change_metadata))
        signals.append(self._system_health_signal(request.environment_health))
        signals.append(self._author_persona_signal(request.author))
        signals.append(self._file_history_signal(request.change_metadata))
        return signals

    def _code_churn_signal(self, change) -> _SignalOutcome:
        total_changes = change.lines_added + change.lines_removed
        lines_component = min(0.35, total_changes / 1200)
        complexity_component = min(0.15, change.cyclomatic_complexity_delta * 0.08)
        churn_score = min(0.45, lines_component + complexity_component)
        description = (
            f"{total_changes} changed lines ({lines_component:.2f} risk) and complexity delta "
            f"{change.cyclomatic_complexity_delta:.2f} ({complexity_component:.2f} risk) "
            f"combine for {churn_score:.2f}"
        )
        explanation = (
            f"Line churn contributes {round(lines_component * 100, 2)}% risk; complexity delta "
            f"contributes {round(complexity_component * 100, 2)}% risk"
        )
        return _SignalOutcome(
            name="code_churn",
            delta=churn_score,
            completeness=1.0,
            description=f"+{round(churn_score * 100, 2)}% risk ({description}); {explanation}",
        )

    def _system_health_signal(self, health) -> _SignalOutcome:
        mapping = {"healthy": 0.0, "degraded": 0.25, "critical": 0.35}
        delta = mapping.get(health.status, 0.2)
        incident_penalty = min(0.1, health.open_incidents * 0.02)
        delta += incident_penalty
        description = (
            f"{health.status} environment with {health.open_incidents} open incidents"
        )
        return _SignalOutcome(
            name="system_health",
            delta=delta,
            completeness=1.0,
            description=f"+{round(delta * 100, 2)}% risk ({description})",
        )

    def _author_persona_signal(self, author) -> _SignalOutcome:
        expertise = (author.domain_familiarity_score + author.past_success_rate) / 2
        delta = max(-0.1, 0.18 - expertise * 0.18)
        description = (
            f"familiarity {author.domain_familiarity_score:.2f}, success {author.past_success_rate:.2f}"
        )
        return _SignalOutcome(
            name="author_persona",
            delta=delta,
            completeness=1.0,
            description=f"{round(delta * 100, 2)}% risk ({description})",
        )

    def _file_history_signal(self, change) -> _SignalOutcome:
        hotspots = [f for f in change.files_modified if "critical" in f or "hotspot" in f]
        if not change.files_modified:
            return _SignalOutcome(
                name="file_history",
                delta=0.0,
                completeness=0.0,
                description="No file history metadata provided",
                requires_pessimism=True,
            )

        delta = 0.25 if hotspots else 0.05
        description = (
            f"{'hotspot' if hotspots else 'regular'} files changed ({len(change.files_modified)} files)"
        )
        return _SignalOutcome(
            name="file_history",
            delta=delta,
            completeness=0.9,
            description=f"+{round(delta * 100, 2)}% risk ({description})",
        )

    def _map_lane(self, score: float) -> DeploymentLane:
        if score > 0.7:
            return DeploymentLane.HIGH_RISK
        if score >= 0.2:
            return DeploymentLane.MEDIUM_RISK
        return DeploymentLane.LOW_RISK

    def _lookup_actions(self, lane: DeploymentLane) -> List[str]:
        if lane == DeploymentLane.LOW_RISK:
            return ["Auto-canary deployment", "Monitor metrics for 15 minutes"]
        if lane == DeploymentLane.MEDIUM_RISK:
            return ["Run full integration suite", "Pause for manual approval", "Notify product owner"]
        return [
            "Request senior review",
            "Extend soak time before full rollout",
            "Create incident readiness alert",
        ]
