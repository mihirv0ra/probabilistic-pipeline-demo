import os
import subprocess
from pathlib import Path

from prob_pipeline.enricher import ContextEnricher


def _run_git(commands, repo: Path):
    env = os.environ.copy()
    subprocess.run(["git", *commands], cwd=repo, check=True, env=env)


def test_enricher_defaults(tmp_path: Path):
    enricher = ContextEnricher(repo_path=tmp_path)
    payload = {"request": {"author": {"id": ""}, "change_metadata": {"files_modified": []}}}
    enriched = enricher.enrich_payload(payload)
    author = enriched["request"]["author"]
    assert author["domain_familiarity_score"] == 0.2
    assert author["past_success_rate"] == 0.3


def test_derive_author_scores_from_git(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(["init"], repo)
    _run_git(["config", "user.name", "Demo Dev"], repo)
    _run_git(["config", "user.email", "demo@example.com"], repo)
    file_path = repo / "module.py"
    for idx in range(3):
        file_path.write_text(f"pass {idx}\n")
        _run_git(["add", "module.py"], repo)
        _run_git([
            "commit",
            "-m",
            f"feat change {idx}",
            "--author",
            "Demo Dev <demo@example.com>",
        ], repo)
    enricher = ContextEnricher(repo_path=repo)
    familiarity, past_success = enricher.derive_author_scores("Demo Dev", ["module.py"])
    assert familiarity == 0.15
    assert past_success == 1.0
