# Roadmap for v0

## Week 1: Design & signal plumbing
- Define adapter contracts and create stub implementations for `codeChurn`, `systemHealth`, `authorPersona`, and `fileHistory`.
- Build the Bayesian scoring core that ingests signal deltas, applies biases, and emits `confidenceScore`, `lane`, `reasoning`, and `hardFloor`.
- Document the data model, inference rules, and architecture (covered by earlier docs).

## Week 2: Execution surface
- Implement CLI that reads metadata from files/env and prints a JSON scorecard plus colored summary.
- Package a GitHub Action that runs the engine against PR metadata, posts a status check, and optionally annotates the PR with reasoning.
- Add adapters for security/compliance scan status to enforce the hard floor.

## Week 3: Integration + polish
- Validate data ingestion by running against example repos (checkout, run `diff`, gather telemetry, etc.).
- Provide sample configuration templates for adding CMDB, incident history, and future ML-fed data.
- Establish automated tests for scoring and reasoning outputs.
- Draft a launch post showcasing how the engine calculates scores for a real repo and how it enables new lanes.

## Launch checklist
- Create a repo README with mission + quick start (done).
- Publish CLI + GitHub Action artifacts (npm/pypi + GitHub release).
- Share launch narrative on DevOps communities: blog post, Hacker News, r/devops, LinkedIn.
- Solicit early adopters by offering free onboarding sessions for their agentic pipelines.
- Track adoption with simple telemetry (deploy lane counts, score distribution) and embed badges/banners in README.
