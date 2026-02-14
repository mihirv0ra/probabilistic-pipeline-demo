# Presentation Script for Probabilistic Pipeline Demo

1. **Setup context** – Explain the problem: deterministic gates cause friction; we want a Bayesian risk score derived from commit/health/author signals and routed to deployment lanes with reasoning.
2. **Show the architecture** – Display `docs/architecture.md` mermaid flow and describe the context enrichers, inference core, router, FastAPI proxy, and feedback store.
3. **Generate traffic** – Run `python demo/mock_data.py --count 2` and show the payloads briefly so the audience sees the synthetic metadata (churn, health, author familiarity).
4. **Run FastAPI proxy** – Start `uvicorn prob_pipeline.api:app --reload --port 8001` (mention it calls `ContextEnricher`) and POST a payload (use `httpx` or `curl`) returned from the generator; highlight the JSON response, `confidence_score`, `risk_factors`, and recommended actions.
5. **Route lane decisions** – Save the response to `demo/traffic/response_demo.json` and run `python -m prob_pipeline.router demo/traffic/response_demo.json`; emphasize the printed triggers and that outcomes are appended to `demo/outcomes.jsonl`.
6. **Run traffic generator** – Demonstrate `python demo/traffic.py --count 3` to show the pipeline running end-to-end (payload generation, FastAPI call, router output) while the persistence log grows.
7. **Show the UI** – Launch `streamlit run demo/ui.py` and walk through the same enriched payload, showing the lane, risk factors, and persisted log entries without shell commands.
7. **Explain feedback loop** – Reference `docs/feedback.md` and show `demo/outcomes.jsonl`; describe how overrides/outcomes can tune priors or add signals.
8. **Next steps** – Mention integration with GitHub Actions, adding adapters (CMDB, incidents), and the platform’s extensibility.
