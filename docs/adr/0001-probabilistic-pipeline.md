# ADR 0001: Probabilistic pipeline context enrichment

## Status
Accepted

## Context
The system must consume CI/CD metadata, produce a Bayesian risk score, and recommend deployment lanes while keeping every decision explainable. Upstream tools may not provide enough domain context (familiarity, past success, hotspots) so the inference engine must run with self-generated signals while preserving flexibility to add future data sources.

## Decision
We split the platform into three layers:
1. **Context enrichers** derive domain familiarity, changelog statistics, hotspot indicators, and health metrics from repository/PR/incident history, packaging them according to the risk assessment contract.
2. **Inference core** (existing `RiskInferenceEngine`) remains a deterministic Bayesian score + reasoning emitter, enforcing pessimism bias and the security hard floor while mapping scores to lanes.
3. **Orchestration layer** exposes the engine via CLI/FastAPI, reads responses through a router, records the lane decisions, and feeds telemetry back to adjust priors.

Additionally, we document the feedback loop (docs/feedback.md) and supply mock data/diagrams so the platform can start locally and gradually absorb more data sources.

## Consequences
- New signal sources can be added by writing enrichers that produce `_SignalOutcome` objects; the inference layer requires no logic changes.
- Observability and outcome telemetry can be stored alongside router outputs to tune priors/biases, ensuring the engine evolves with the platform.
- Documentation and demos explain how the CLI/FastAPI router integrate, enabling stakeholders to understand and validate each lane before connecting to external CI/CD workflows.
