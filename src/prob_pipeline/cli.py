"""CLI entry point for the probabilistic pipeline regression."""
import json
import sys
from pathlib import Path

from .core import RiskInferenceEngine
from .enricher import ContextEnricher
from .models import AssessmentRequest


def main() -> int:
    payload = _read_payload()
    enricher = ContextEnricher()
    enriched = enricher.enrich_payload(payload)
    request = AssessmentRequest.from_payload(enriched)
    engine = RiskInferenceEngine()
    response = engine.assess(request)
    print(json.dumps(response, default=lambda o: o.__dict__, indent=2))
    return 0


def _read_payload():
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        return json.loads(path.read_text())
    return json.load(sys.stdin)
