import json
from pathlib import Path

from prob_pipeline.cli import main
from prob_pipeline.core import RiskInferenceEngine
from prob_pipeline.models import (
    AssessmentRequest,
    AssessmentResponse,
    Author,
    ChangeMetadata,
    EnvironmentHealth,
    SecurityScan,
)


def test_assessment_response_low_risk():
    request = AssessmentRequest(
        commit_id="abc",
        author=Author(id="dev", domain_familiarity_score=0.9, past_success_rate=0.95),
        change_metadata=ChangeMetadata(lines_added=5, lines_removed=2, files_modified=["lib.py"], cyclomatic_complexity_delta=0.01),
        environment_health=EnvironmentHealth(status="healthy", open_incidents=0),
        security_scan=SecurityScan(passed=True),
    )
    engine = RiskInferenceEngine()
    response = engine.assess(request)
    assert response.confidence_score < 20
    assert response.assigned_lane == "low_risk"
    assert response.is_security_compliant


def test_assessment_response_high_risk_when_security_missing():
    request = AssessmentRequest(
        commit_id="def",
        author=Author(id="dev", domain_familiarity_score=0.2, past_success_rate=0.3),
        change_metadata=ChangeMetadata(lines_added=200, lines_removed=40, files_modified=["critical/service.py"], cyclomatic_complexity_delta=2.0),
        environment_health=EnvironmentHealth(status="critical", open_incidents=4),
        security_scan=SecurityScan(passed=False),
    )
    engine = RiskInferenceEngine()
    response = engine.assess(request)
    assert response.assigned_lane == "high_risk"
    assert not response.is_security_compliant
