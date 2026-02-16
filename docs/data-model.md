# Data Model and Signal Schema

Every adapter produces the following structured object before it enters the inference core:

```json
{
  "signalId": "authorPersona",
  "confidenceDelta": 0.12,
  "signalCompleteness": 0.85,
  "reasonSnippet": "Module owner has 5 clean merges here",
  "metadata": { "source": "github", "module": "payment" }
}
```

## Signal fields
- `confidenceDelta` (float): The delta in risk (0-1) inferred solely from this source.
- `signalCompleteness` (0-1): How complete/trusted the data is; values below `0.6` trigger the pessimism bias.
- `reasonSnippet`: Human-readable text explaining the delta.
- `metadata`: Optional context (module, owner, incident reference, etc.).

## Priors and scoring
| Signal | Prior Risk Delta | Bias when missing |
| --- | --- | --- |
| `codeChurn` | 0.20 (large diffs, high complexity) | +0.15 |
| `systemHealth` | 0.25 (pre-existing degradation) | +0.15 |
| `authorPersona` | 0.10 (trusted authors) | +0.10 |
| `fileHistory` | 0.30 (hotspot multiplier) | +0.15 |

The inference core starts with a base prior (configurable per service) and multiplies it by `(1 + each confidenceDelta)`, clamping to 1.0.
If a signal is missing or below completeness, add the defined pessimism delta before fusion.

## Reasoning payload
The final output includes `reasoning` with entries like:
```
"reasoning": [
  "codeChurn: +0.15 (diff touches schema service)",
  "systemHealth: +0.20 (latency spike ongoing)",
  "authorPersona: -0.05 (veteran)"
]
```
This is important for developer transparency and surfaces how missing signals increased risk.

## Signal extensibility
Adapters for future sources must:
1. Name their `signalId` and document its semantics.
2. Define a prior and pessimism delta.
3. Maximize completeness and describe required permissions (e.g., CMDB read access, incident history API credentials).

Signals can be added by updating the adapter registry and merging their deltas into the Bayesian update pipeline.
