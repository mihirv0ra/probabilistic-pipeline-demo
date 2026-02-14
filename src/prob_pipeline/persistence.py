from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .models import AssessmentResponse


class OutcomeLogger:
    def __init__(self, path: Path | str = Path("demo/outcomes.jsonl")):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, response: AssessmentResponse, triggers: Iterable[str]) -> None:
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "lane": response.assigned_lane,
            "confidence_score": response.confidence_score,
            "is_security_compliant": response.is_security_compliant,
            "triggers": list(triggers),
            "risk_factors": [factor.__dict__ for factor in response.risk_factors],
            "recommended_actions": response.recommended_actions,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
