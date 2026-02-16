from __future__ import annotations

from datetime import datetime, timedelta
import subprocess
from pathlib import Path
from typing import Iterable, List, Tuple

class ContextEnricher:
    def __init__(self, repo_path: Path | str = Path("."), history_days: int = 90):
        self.repo_path = Path(repo_path)
        self.history_days = history_days

    def enrich_payload(self, payload: dict) -> dict:
        data = payload.get("request", payload)
        author = data.setdefault("author", {})
        change = data.get("change_metadata", {})
        files = change.get("files_modified", [])
        familiarity, success_rate = self.derive_author_scores(author.get("id"), files)
        author.setdefault("domain_familiarity_score", familiarity)
        author.setdefault("past_success_rate", success_rate)
        return payload

    def derive_author_scores(self, author_id: str | None, files: Iterable[str]) -> Tuple[float, float]:
        if not author_id:
            return 0.2, 0.3
        commit_count = self._count_commits(author_id, files)
        familiarity = min(1.0, commit_count / 20)
        success_count = self._count_successful_commits(author_id, files)
        if commit_count:
            past_success = min(1.0, success_count / commit_count)
        else:
            past_success = 0.5
        return familiarity, past_success

    def _count_commits(self, author_id: str, files: Iterable[str]) -> int:
        since = (datetime.utcnow() - timedelta(days=self.history_days)).strftime("%Y-%m-%d")
        args = ["log", f"--since={since}", "--author", author_id, "--pretty=format:%H"]
        args.extend(self._file_args(files))
        output = self._run_git(args)
        return sum(1 for line in output.splitlines() if line)

    def _count_successful_commits(self, author_id: str, files: Iterable[str]) -> int:
        since = (datetime.utcnow() - timedelta(days=self.history_days)).strftime("%Y-%m-%d")
        args = ["log", f"--since={since}", "--author", author_id, "--pretty=format:%s"]
        args.extend(self._file_args(files))
        output = self._run_git(args)
        keywords = ("revert", "rollback")
        return sum(1 for line in output.splitlines() if line and not any(keyword in line.lower() for keyword in keywords))

    def _file_args(self, files: Iterable[str]) -> List[str]:
        args: List[str] = []
        files = [f for f in files if f]
        if files:
            args.append("--")
            args.extend(files)
        return args

    def _run_git(self, args: List[str]) -> str:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
            return result.stdout.strip()
        except Exception:
            return ""
