from pathlib import Path
from prob_pipeline.models import AssessmentResponse, RiskFactor
from prob_pipeline.persistence import OutcomeLogger


def test_logger_writes_jsonl(tmp_path: Path):
    logger = OutcomeLogger(path=tmp_path / "log.jsonl")
    response = AssessmentResponse(
        confidence_score=42.0,
        assigned_lane="medium_risk",
        risk_factors=[RiskFactor(vector="code_churn", impact_percentage=10.0, description="foo")],
        recommended_actions=["action"],
        is_security_compliant=True,
    )
    logger.log(response, ["trigger"])
    contents = (tmp_path / "log.jsonl").read_text().strip()
    assert contents
    assert "medium_risk" in contents
    assert "risk_factors" in contents
