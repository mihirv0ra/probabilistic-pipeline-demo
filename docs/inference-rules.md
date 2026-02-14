# Inference Rules

This document captures the first deterministic rules that seed the Bayesian core.

## Score computation
1. Start with `basePrior` per service (default `0.10`).
2. For each signal, add `confidenceDelta`. Example: `basePrior + codeChurn.delta + fileHistory.delta`.
3. Clamp to `1.0` and convert to percentage for `confidenceScore` (`score = value * 100`).
4. If a signal is missing or `signalCompleteness < 0.6`, add the `pessimismBias` (e.g., 15 points) before clamping.
5. `confidenceScore` maps to lanes as defined below.
6. Always emit `hardFloor` true if `securityScanStatus != "passed"`.

## Risk reasoning rules
- Explain values in `reasoning` entries such as:
  - `"codeChurn: +0.18 (diff touches schema service, 240 lines)"`
  - `"authorPersona: -0.05 (module expert with 60% successful rollbacks)"`
  - `"systemHealth: +0.25 (3.4% error rate on current release, CPU > 85%)"`
  - `"fileHistory: +0.12 (two incidents in last 6 months)"`
- Mention missing data entries: `"lacking incident history -> applied pessimism bias"`.
- Maintain `reasoningOrder` so the top contributors appear first.

## Deployment lane mapping
| Confidence Score | Lane | Actions |
| --- | --- | --- |
| `< 20` | Low Risk | Auto-canary, smoke test, deploy to production via canary job |
| `20 - 70` | Medium Risk | Run full integration suite and pause for manual approval before deployment |
| `> 70` | High Risk | Require senior engineer review, longer soak time, notify incident response team |

If `hardFloor` is true, override lane to `High Risk` even if score is low, and append `"hard floor triggered: security/compliance scan"` to reasoning.

## Missing signal handling
- Missing `systemHealth`: add `+0.15` to score and add reasoning entry.
- Missing `CMDB` or asset-tag metadata: log warning, track event for future integration.
- Always apply pessimism bias when the dataset is stale (timestamp older than configured freshness). The bias should be prominent in `reasoning` to remind reviewers.
