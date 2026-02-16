"""Generate synthetic payloads for the Probabilistic Pipeline."""
import argparse
import json
import random
import uuid
from pathlib import Path

STATUS_CHOICES = ["healthy", "degraded", "critical"]
CRITICAL_FILES = ["src/critical/auth.py", "src/critical/data.py", "src/critical/cache.py"]
MODULES = ["payment", "shipping", "user", "auth", "analytics"]
OUTPUT_DIR = Path(__file__).parent / "synthetic"


def _random_change() -> dict:
    files = random.choices(CRITICAL_FILES + [f"src/{random.choice(MODULES)}/module.py"], k=random.randint(1, 4))
    return {
        "lines_added": random.randint(5, 300),
        "lines_removed": random.randint(0, 120),
        "files_modified": files,
        "cyclomatic_complexity_delta": round(random.uniform(0.0, 3.5), 2),
    }


def _random_health() -> dict:
    status = random.choices(STATUS_CHOICES, weights=[0.6, 0.3, 0.1])[0]
    return {
        "status": status,
        "open_incidents": random.randint(0, 5 if status != "healthy" else 0),
    }


def _payload_template(index: int) -> dict:
    return {
        "request": {
            "commit_id": f"mock-{index}-{uuid.uuid4().hex[:6]}",
            "author": {
                "id": f"synthetic-{random.randint(1, 20)}",
                "domain_familiarity_score": round(random.uniform(0.25, 0.95), 2),
                "past_success_rate": round(random.uniform(0.2, 0.98), 2),
            },
            "change_metadata": _random_change(),
            "environment_health": _random_health(),
        },
        "security_scan_passed": random.choice([True, True, False]),
    }


def generate(count: int = 5) -> list[Path]:
    OUTPUT_DIR.mkdir(exist_ok=True)
    paths = []
    for index in range(count):
        payload = _payload_template(index)
        path = OUTPUT_DIR / f"mock_payload_{index}.json"
        path.write_text(json.dumps(payload, indent=2))
        paths.append(path)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic Probabilistic Pipeline payloads.")
    parser.add_argument("--count", type=int, default=5, help="Number of payloads to emit")
    args = parser.parse_args()
    generated = generate(args.count)
    print("Generated mock payloads:")
    for p in generated:
        print(f"  - {p}")


if __name__ == "__main__":
    main()
