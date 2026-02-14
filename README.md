# Probabilistic Pipeline

A lightweight risk inference engine that lives in CI/CD and decouples deployment gating from brittle boolean checks. The engine maintains a Bayesian Risk Score that drives deployment lane, exposes reasoning, and makes it easy to add new signal sources over time.

## Goals
- Consume structured and unstructured metadata (churn, telemetry, author history, hotspots, incidents, CMDB tags, etc.).
- Infer deployment risk via Bayesian fusion, applying a pessimism bias when signals are missing.
- Always obey hard policy floors (security/compliance) and surface why a score was assigned.
- Provide a flexible integration surface so the engine can grow beyond the MVP inputs without rewiring the whole pipeline.

## Repository layout
- `README.md` (this file) documents the mission and high-level structure.
- `docs/architecture.md` captures integration patterns, signal adapters, and the inference pipeline
- `docs/data-model.md` describes the signal schema, priors, and explanation fields.
- `docs/inference-rules.md` enumerates the first tipping rules plus confidence/reasoning conventions.
- `docs/roadmap.md` lists shipping steps, discovery loops, and go-to-market moves.
- `src/` will contain the engine implementation (pluggable adapters, Bayesian core, CLI/Action wrappers).

## Next steps
1. Agree on the MVP signals, priors, and reasoning conventions in `docs/data-model.md` and `docs/inference-rules.md`.
2. Define the architecture of adapters, policy evaluators, and deployment lane outputs in `docs/architecture.md`.
3. Ship the MVP engine, CLI, and GitHub Action before iterating on more signal sources and integration partners.

## Local demo

Use the provided JSON payloads to exercise the inference core locally and capture the reasoning that drives each lane.

1. Install dependencies: `python -m pip install .`
2. Run the bundled CLI directly: `python -m prob_pipeline.cli demo/sample_payload_medium.json`
3. Or run the convenience demo runner that iterates through all payloads: `python demo/run_demo.py`

## Synthetic data generator

Generate fresh commit and health metadata with `demo/mock_data.py` to see how the engine reacts to different speeds of change.

1. Run `python demo/mock_data.py --count 4`.
2. Feed any generated payload into the CLI (`python -m prob_pipeline.cli demo/synthetic/mock_payload_0.json`) or the FastAPI proxy.

## FastAPI inference proxy

Start `uvicorn prob_pipeline.api:app --reload --port 8001` and POST to `/assess` with the schema from `demo/sample_payload_medium.json` (or any synthetic version) to see the JSON response and reasoned `risk_factors`.

## Router CLI

After the FastAPI service produces a response, save it locally and run `python -m prob_pipeline.router path/to/response.json` to visualize which workflow would be triggered for each lane. This router can later call the real approval/soak jobs you wire into GitHub Actions.

The router appends every decision to `demo/outcomes.jsonl`, providing the persistence layer for your feedback loop. Inspect that JSONL file to trace how scores, risk factors, and recommended actions evolve as you add more sources.

## Traffic generator

Run `python demo/traffic.py --count 3` while `uvicorn prob_pipeline.api:app --reload --port 8001` is active to showcase the full stack. The script:

1. Uses `demo/mock_data.py` to emit synthetic payloads.
2. Posts each payload to `/assess`, picking up the enricher’s derived author metrics.
3. Saves the JSON responses under `demo/traffic/` and replays them through `prob_pipeline.router` to print the lane triggers and enrich the persistence log.

## Interactive UI demo

If you prefer a GUI walkthrough instead of shell commands, run `streamlit run demo/ui.py`. The UI:

1. Lets you select from sample or synthetic payloads, edit the JSON inline, and visualize the request metadata.
2. Has a “Generate random traffic payload and run inference” button that spins up new metadata, enriches context, and reruns the Bayesian engine automatically.
3. Displays the resulting `confidence_score`, `assigned_lane`, risk factors, and recommended actions alongside the router’s triggers and a mock continuation plan.
4. Persists decisions to `demo/outcomes.jsonl` and renders a live summary chart/table for the latest lane outcomes so the feedback loop is charted in front of your audience.

## Context enricher

The `ContextEnricher` module inspects the local repo history to generate the `domain_familiarity_score` and `past_success_rate` that feed the inference engine. When run inside a pipeline, it uses the current working tree, the author ID, and the touched files to derive normalized metrics before the payload reaches `RiskInferenceEngine`. The FastAPI entry point and CLI both invoke the enricher automatically, but you can use it manually via `python -m prob_pipeline.enricher` once we add an entry point later.

## Feedback loop

Capture each assessment’s `assigned_lane`, whether it was auto-approved, and the subsequent rollout outcome. See `docs/feedback.md` for how to loop that telemetry back into priors, bias adjustments, and signal additions.
