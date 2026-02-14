"""CLI router to react to inference responses."""
import json
import sys
from pathlib import Path
from typing import Iterable, Sequence

from .models import AssessmentResponse, RiskFactor
from .persistence import OutcomeLogger

LANE_TRIGGERS = {
    "low_risk": [
        "Trigger auto-canary workflow",
        "Post green status to GitHub",
        "Start short-lived observability monitor",
    ],
    "medium_risk": [
        "Run full integration suite",
        "Pause pipeline and request manual approval",
        "Notify module maintainer via Slack",
    ],
    "high_risk": [
        "Gate deployment until senior review is complete",
        "Kick off extended soak job",
        "Alert incident response and page on-call",
    ],
}


def _load_responses(paths: Iterable[Path]) -> Sequence[AssessmentResponse]:
    responses = []
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"Response file {path} does not exist")
        payload = json.loads(path.read_text())
        responses.append(_parse_response(payload))
    return responses


def _parse_response(payload: dict) -> AssessmentResponse:
    if "assigned_lane" not in payload:
        raise ValueError("Response payload must include `assigned_lane`")
    return AssessmentResponse(
        confidence_score=float(payload.get("confidence_score", 0.0)),
        assigned_lane=payload["assigned_lane"],
        risk_factors=[
            RiskFactor(**rf) for rf in payload.get("risk_factors", [])
        ],
        recommended_actions=list(payload.get("recommended_actions", [])),
        is_security_compliant=bool(payload.get("is_security_compliant", True)),
    )
logger = OutcomeLogger()


def _execute_lane(response: AssessmentResponse) -> Iterable[str]:
    triggers = LANE_TRIGGERS.get(response.assigned_lane, [])
    print(f"Assigned lane: {response.assigned_lane} ({response.confidence_score}% confidence)")
    print("Risk factors:")
    for factor in response.risk_factors:
        print(f"  - {factor.vector}: {factor.impact_percentage}% -> {factor.description}")
    print("Recommended triggers:")
    for action in triggers:
        print(f"  * {action}")
    print()
    return triggers


def main() -> int:
    args = sys.argv[1:] or ["response.json"]
    paths = [Path(arg) for arg in args]
    try:
        responses = _load_responses(paths)
    except Exception as exc:
        print(f"Failed to parse response: {exc}", file=sys.stderr)
        return 1
    for response in responses:
        triggers = _execute_lane(response)
        logger.log(response, triggers)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
