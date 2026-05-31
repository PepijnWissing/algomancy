# Release v{VERSION} Verification Checklist

> **Gating policy (see [§ Advisory vs. gated](#advisory-vs-gated)):**
> Publishing is currently **advisory** — the checklist is informational and a
> publish to PyPI can proceed without full checklist completion.
> After one or two release cycles, the policy will be re-evaluated and may
> move to a label-gated model.

## 1 Build sanity

- [ ] `uv lock --check` exits 0 (lockfile is up to date)
- [ ] `uv run python algomancy-version-bump.py --check` exits 0 (all packages at `{VERSION}`)
- [ ] `uv build --all-packages --wheel` succeeds for all 8 packages
- [ ] `pre-commit run --all-files` passes (ruff, sort-pyproject)

## 2 Automated test gate

- [ ] `uv run pytest tests packages/algomancy-data/tests packages/algomancy-scenario/tests -v` — all green
- [ ] `uv run pytest packages/algomancy-api/tests -v` — all green, including `test_smoke_live.py`
- [ ] `uv run pytest packages/algomancy-quickstart/tests -v` — all green
- [ ] Slow smoke matrix (`-m slow`) green on CI or local:
  - [ ] CLI smoke (`test_smoke_cli.py`)
  - [ ] Quickstart validate matrix (`test_smoke_quickstart.py`)
  - [ ] Persistence backend matrix (`tests/smoke/test_persistence_matrix.py`)

## 3 GUI manual walk

- [ ] `uv run python example/main.py` boots, sidebar shows: Home, Data, Scenarios, Compare, Overview
- [ ] Data accordion shows all tables without console errors
- [ ] Run **GreedySlotting** scenario → completes with non-NaN KPI values
- [ ] Run **SimulatedAnnealingSlotting** → progress bar increments during run
- [ ] Compare page shows side-by-side warehouse scatter for two completed scenarios
- [ ] Overview page renders slot scatter coloured by zone
- [ ] Run **LongProgressAlgorithm** (10 s) → progress bar advances → DELETE cancels within 2 s
- [ ] Run **FailureModesAlgorithm** `raise_value_error` → scenario shows failed state with error message
- [ ] Switch session (e.g. `test_session`) → no crash
- [ ] `uv run python example/main.py --backend database --database-url sqlite:///./tmp_test.db` boots end-to-end; delete `tmp_test.db` afterwards

## 4 CLI manual walk

- [ ] `uv run algomancy-cli --example` starts the shell
- [ ] `list-data` → lists example sessions' datasets
- [ ] `create-scenario smoke-cli default_session Slow {"duration":1}` + `run smoke-cli` → completes
- [ ] `exit` terminates cleanly

## 5 API manual walk

- [ ] `uv run algomancy-api --example` boots on port 8051
- [ ] `GET /health` → `{"status": "ok"}`
- [ ] `GET /docs` → Swagger UI renders
- [ ] End-to-end: create scenario via API → run → poll until complete → verify KPIs

## 6 Quickstart walk

For each combo of `(backend=json, interface=gui)` and at least one of `(backend=database, interface=api)`:
- [ ] Run quickstart wizard in a `tmp/` directory
- [ ] `python main.py --validate` exits 0
- [ ] `uv run pytest tests/` inside the generated project exits 0

## 7 Docs

- [ ] `uv run sphinx-build -b html docs/source docs/build/html` builds without errors or warnings
- [ ] CHANGELOG entry for `v{VERSION}` written
- [ ] README quickstart section reflects any new flags or interfaces

## 8 PyPI smoke

- [ ] In a fresh virtual environment: `pip install algomancy=={VERSION}` succeeds
- [ ] `python -c "import algomancy; print(algomancy.__version__)"` prints `{VERSION}`

## 9 Sign-off

- [ ] Reviewer 1: @____________ confirms items 1–8 complete
- [ ] Reviewer 2: @____________ confirms items 1–8 complete

---

## Advisory vs. gated

**Current policy: advisory.**
Publishing can proceed without waiting for checklist completion. The intent is
to prove the workflow over one or two release cycles before adding a hard gate.

Once the policy moves to **gated**, the plan is:
- `publish.yml` will wait for the `release-verified` label to be applied to
  the release-checklist issue before triggering the PyPI upload step.
- The label must be applied by a project maintainer after reviewing the issue.

The decision to switch will be recorded here with the version number at which
it takes effect.
