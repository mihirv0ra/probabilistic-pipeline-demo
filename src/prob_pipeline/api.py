"""FastAPI proxy for the risk inference engine."""
from __future__ import annotations

from typing import List, Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .core import RiskInferenceEngine
from .enricher import ContextEnricher
from .models import AssessmentRequest, AssessmentResponse


class AuthorPayload(BaseModel):
    id: str
    domain_familiarity_score: float = Field(0.0, ge=0.0, le=1.0)
    past_success_rate: float = Field(0.0, ge=0.0, le=1.0)


class ChangeMetadataPayload(BaseModel):
    lines_added: int
    lines_removed: int
    files_modified: List[str]
    cyclomatic_complexity_delta: float


class EnvironmentHealthPayload(BaseModel):
    status: Literal["healthy", "degraded", "critical"]
    open_incidents: int


class RequestPayload(BaseModel):
    commit_id: str
    author: AuthorPayload
    change_metadata: ChangeMetadataPayload
    environment_health: EnvironmentHealthPayload


class AssessmentEnvelope(BaseModel):
    request: RequestPayload
    security_scan_passed: bool = True


class RiskFactorResponse(BaseModel):
    vector: str
    impact_percentage: float
    description: str


class AssessmentResponsePayload(BaseModel):
    confidence_score: float
    assigned_lane: Literal["low_risk", "medium_risk", "high_risk"]
    risk_factors: List[RiskFactorResponse]
    recommended_actions: List[str]
    is_security_compliant: bool


app = FastAPI(title="Probabilistic Pipeline Inference Proxy", version="0.1.0")
engine = RiskInferenceEngine()
enricher = ContextEnricher()


@app.post("/assess", response_model=AssessmentResponsePayload)
def assess(payload: AssessmentEnvelope) -> AssessmentResponsePayload:
    enriched = enricher.enrich_payload(payload.dict())
    request = AssessmentRequest.from_payload(enriched)
    response = engine.assess(request)
    return AssessmentResponsePayload(**_flatten_response(response))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "description": "Inference engine online"}


def _flatten_response(response: AssessmentResponse) -> dict:
    return {
        "confidence_score": response.confidence_score,
        "assigned_lane": response.assigned_lane,
        "risk_factors": [
            RiskFactorResponse(**factor.__dict__).dict()
            for factor in response.risk_factors
        ],
        "recommended_actions": response.recommended_actions,
        "is_security_compliant": response.is_security_compliant,
    }
