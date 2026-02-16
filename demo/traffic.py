"""Drive traffic through the inference proxy and router for demos."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List

import httpx

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from demo.mock_data import generate

API_URL = "http://localhost:8001/assess"
OUTPUT_DIR = Path(__file__).parent / "traffic"
DEFAULT_COUNT = 3


def _send_payload(path: Path) -> Path:
    payload = json.loads(path.read_text())
    response = httpx.post(API_URL, json=payload, timeout=10.0)
    response.raise_for_status()
    OUTPUT_DIR.mkdir(exist_ok=True)
    response_path = OUTPUT_DIR / f"response_{path.stem}.json"
    response_path.write_text(response.text)
    return response_path


def _run_router(response_paths: Iterable[Path]) -> None:
    for path in response_paths:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(SRC_DIR)
        subprocess.run(
            ["python", "-m", "prob_pipeline.router", str(path)],
            check=True,
            env=env,
        )


def main(count: int = DEFAULT_COUNT) -> None:
    payloads = generate(count)
    responses: List[Path] = []
    for payload in payloads:
        print(f"Posting {payload.name} -> {API_URL}")
        responses.append(_send_payload(payload))
    _run_router(responses)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send enriched payloads through the inference proxy and router")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT, help="Number of payloads to emit and post")
    args = parser.parse_args()
    main(args.count)
