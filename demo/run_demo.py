"""Convenience runner for the demonstration payloads."""
import json
from pathlib import Path
from typing import Iterable

from prob_pipeline.core import RiskInferenceEngine
from prob_pipeline.models import AssessmentRequest


ENG = RiskInferenceEngine()
PAYLOAD_DIR = Path(__file__).parent


def _load_payload(path: Path) -> AssessmentRequest:
    payload = json.loads(path.read_text())
    return AssessmentRequest.from_payload(payload)


def _print_response(path: Path, response):
    print(f"--- Demo {path.name} ---")
    print(f"Assigned lane: {response.assigned_lane}  (Confidence: {response.confidence_score}%)")
    print("Reasoning:")
    for factor in response.risk_factors:
        print(f"  - {factor.vector}: {factor.impact_percentage}% -> {factor.description}")
    print("Recommended actions:")
    for action in response.recommended_actions:
        print(f"  * {action}")
    print(f"Security compliant: {response.is_security_compliant}\n")


def run_demo(paths: Iterable[Path]) -> None:
    for path in paths:
        request = _load_payload(path)
        response = ENG.assess(request)
        _print_response(path, response)


def main() -> None:
    payloads = sorted(PAYLOAD_DIR.glob("sample_payload_*.json"))
    run_demo(payloads)


if __name__ == "__main__":
    main()
