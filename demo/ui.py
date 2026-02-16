from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Tuple

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from demo.mock_data import generate
from prob_pipeline.core import RiskInferenceEngine
from prob_pipeline.enricher import ContextEnricher
from prob_pipeline.models import AssessmentRequest, AssessmentResponse
from prob_pipeline.persistence import OutcomeLogger

PAYLOAD_DIR = Path(__file__).resolve().parent
SAMPLE_FILES = sorted(PAYLOAD_DIR.glob("sample_payload_*.json"))
SYNTHETIC_DIR = PAYLOAD_DIR / "synthetic"

ENGINE = RiskInferenceEngine()
ENRICHER = ContextEnricher()
LOGGER = OutcomeLogger()

LANE_TRIGGERS = {
    "low_risk": [
        "Trigger auto-canary workflow",
        "Post green status to GitHub",
        "Start short-lived observability monitor",
    ],
    "medium_risk": [
        "Run full integration suite",
        "Pause pipeline and request manual approval",
        "Notify module maintainer via Slack",
    ],
    "high_risk": [
        "Gate deployment until senior review is complete",
        "Kick off extended soak job",
        "Alert incident response and page on-call",
    ],
}

MOCK_CONTINUATIONS = {
    "low_risk": [
        "Auto-canary deployment",
        "Light monitoring",
        "Full rollout if canary passes",
    ],
    "medium_risk": [
        "Run integration suite",
        "Pause for manual approval",
        "Notify module owner",
    ],
    "high_risk": [
        "Senior review + security sign-off",
        "Trigger incident response playbook",
        "Hold deployment until soak time passes",
    ],
}

def list_payload_paths() -> list[Path]:
    return sorted(SAMPLE_FILES) + sorted(SYNTHETIC_DIR.glob("mock_payload_*.json"))


def _run_inference(payload_text: str) -> Tuple[AssessmentRequest, AssessmentResponse, list[str]]:
    enriched = ENRICHER.enrich_payload(json.loads(payload_text))
    request = AssessmentRequest.from_payload(enriched)
    response = ENGINE.assess(request)
    lane_triggers = LANE_TRIGGERS.get(response.assigned_lane, [])
    return request, response, lane_triggers


def _load_feedback_log(path: Path) -> list[dict]:
    if not path.exists():
        return []
    lines = [line for line in path.read_text().splitlines() if line.strip()]
    return [json.loads(line) for line in lines]


def _summarize_lanes(entries: list[dict]) -> dict[str, int]:
    counter = Counter(entry.get("lane", "unknown") for entry in entries)
    return {lane: counter.get(lane, 0) for lane in ["low_risk", "medium_risk", "high_risk"]}


st.set_page_config(page_title="Probabilistic Pipeline Simulator", layout="wide")
st.title("Probabilistic Pipeline Simulation")

payload_paths = list_payload_paths()
if not payload_paths:
    st.error("No payload samples available. Run the mock data generator to create them.")

if "payload_select" not in st.session_state:
    st.session_state.payload_select = payload_paths[0].name if payload_paths else ""

generate_col, select_col = st.columns([1, 3])
with generate_col:
    if st.button("Generate random traffic payload and run inference"):
        new_payloads = generate(1)
        if new_payloads:
            st.session_state.payload_select = new_payloads[-1].name
            st.session_state.last_result = _run_inference(new_payloads[-1].read_text())
with select_col:
    payload_names = [path.name for path in payload_paths]
    selected_name = st.selectbox("Pick a payload", payload_names, key="payload_select")

payload_path = next((path for path in payload_paths if path.name == selected_name), payload_paths[0])
payload_text = payload_path.read_text()

st.subheader("Input payload")
st.code(payload_text, language="json")

custom_payload = st.expander("Edit payload before inference")
edited_payload = custom_payload.text_area("JSON payload", value=payload_text, height=240)

if st.button("Run inference"):
    try:
        st.session_state.last_result = _run_inference(edited_payload)
    except Exception as exc:
        st.error(f"Failed to run inference: {exc}")

last_result = st.session_state.get("last_result")
if last_result:
    request, response, lane_triggers = last_result
    st.success(
        f"Assigned lane: {response.assigned_lane} ({response.confidence_score}%) — "
        f"Security compliant: {response.is_security_compliant}"
    )

    with st.expander("Request metadata"):
        st.json(request.__dict__)

    st.write("### Risk factors")
    st.table(
        [
            {
                "Vector": rf.vector,
                "Impact %": rf.impact_percentage,
                "Description": rf.description,
            }
            for rf in response.risk_factors
        ]
    )

    st.write("### Recommended actions")
    for action in response.recommended_actions:
        st.markdown(f"- **{action}**")

    st.write("### Routing triggers")
    for trigger in lane_triggers:
        st.write(f"- {trigger}")

    st.write("### Mock continuation plan")
    for task in MOCK_CONTINUATIONS.get(response.assigned_lane, []):
        st.write(f"- {task}")

    if st.button("Persist to feedback log"):
        LOGGER.log(response, lane_triggers or response.recommended_actions)
        st.info(f"Appended entry to {LOGGER.path}")

    st.write("### Feedback log summary")
    log_entries = _load_feedback_log(LOGGER.path)
    if log_entries:
        lane_counts = _summarize_lanes(log_entries)
        st.bar_chart(lane_counts)
        st.write("Recent entries")
        st.table(
            [
                {"timestamp": entry["timestamp"], "lane": entry["lane"], "confidence": entry["confidence_score"]}
                for entry in log_entries[-5:]
            ]
        )
    else:
        st.info("Feedback log is empty; persist some runs to see summaries.")
