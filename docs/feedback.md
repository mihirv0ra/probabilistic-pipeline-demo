# Feedback Loop Framework

The Probabilistic Pipeline keeps itself honest through a closed feedback loop that ties deployment lanes back to real-world outcomes.

1. **Capture outcomes** – Every time the inference engine emits a `confidence_score` and `assigned_lane`, also record what happened next (auto-canary succeeded, manual rollback needed, senior review flagged a bug). These records can live in a simple CSV/log or be shipped to a data warehouse.
2. **Score disagreements** – Compare `assigned_lane` to the manual reviewer’s verdict (if one is required). When manual reviewers override the engine, log the delta and surface it in dashboards so analysts can detect biased priors.
3. **Adjust priors** – Aggregate historical lane assignments per service/module, then tune the `base_prior` or per-signal bias values. For example, if the `system_health` signal repeatedly underestimates latent degradations, increase its delta or add a new observability signal.
4. **Feed new sources** – Use the synthetic data generator (`demo/mock_data.py`) to test how new vectors (CMDB metadata, incident referencing) would move the score before wiring them into the pipeline.
5. **Explainability** – Persist the `risk_factors` list alongside each deployment so downstream stakeholders (QA, security, product) can see why decisions were made.

By collecting this telemetry and automating the tuning steps, the probabilistic inference engine evolves naturally as you add new data sources or as the system matures.
