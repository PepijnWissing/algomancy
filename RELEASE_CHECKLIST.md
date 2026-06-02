# Release v{VERSION} Verification Checklist

> **Gating policy (see [§ Advisory vs. gated](#advisory-vs-gated)):**
> Publishing is currently **advisory** — the checklist is informational and a
> publish to PyPI can proceed without full checklist completion.
> After one or two release cycles, the policy will be re-evaluated and may
> move to a label-gated model.

> **Conventions used below**
> - **CWD** = the working directory each command must be run from.
> - `<repo>` = the cloned Algomancy repository root.
> - `<tmp>` = a scratch directory (e.g. `mktemp -d`) used by the quickstart walk.
> - `<fresh-venv>` = a brand-new virtual environment outside `<repo>` (e.g.
>   `python -m venv /tmp/algomancy-smoke && source /tmp/algomancy-smoke/bin/activate`).

## 1 Build sanity

**CWD: `<repo>`**

- [ ] `uv lock --check` exits 0 (lockfile is up to date)
- [ ] `uv run python algomancy-version-bump.py --check` exits 0 (all 8 `pyproject.toml` files at `{VERSION}`)
- [ ] `uv build --all-packages --wheel` succeeds for all 7 packages (artifacts land in `<repo>/dist/`)
- [ ] `pre-commit run --all-files` passes (ruff, sort-pyproject)

## 2 Automated test gate

**CWD: `<repo>`** (pytest discovers tests via `pyproject.toml` from here)

- [ ] `uv run pytest tests packages/algomancy-data/tests packages/algomancy-scenario/tests -v` — all green
- [ ] `uv run pytest packages/algomancy-api/tests -v` — all green, including `test_smoke_live.py`
- [ ] `uv run pytest packages/algomancy-quickstart/tests -v` — all green
- [ ] Slow smoke matrix (`-m slow`) green on CI or local:
  - [ ] Quickstart validate matrix (`uv run pytest -m slow packages/algomancy-quickstart/tests/test_smoke_quickstart.py`)
  - [ ] Persistence backend matrix (`uv run pytest -m slow tests/smoke/test_persistence_matrix.py`).
        The `database` case is `importorskip`-skipped unless `uv sync --extra database` is installed; install the extra and re-run if you want the SQLite leg green.

## 3 GUI manual walk

**CWD: `<repo>`** (the example wiring uses a relative `data_path="example/data"`)

- [ ] `uv run python -m example.main --interface gui` boots; browser at `http://127.0.0.1:8050` opens, sidebar shows: Home, Data, Scenarios, Compare, Overview
- [ ] Data accordion shows all tables without console errors
- [ ] Run **Greedy Slotting** scenario → completes with non-NaN KPI values for the warehouse KPIs (Travel Distance, Zone Balance, Reslot Cost)
- [ ] Run **SA Slotting** → progress bar increments during run
- [ ] Compare page shows side-by-side warehouse scatter for two completed slotting scenarios
- [ ] Overview page renders slot scatter coloured by zone
- [ ] Run **Long Progress** (10 s) → progress bar advances → DELETE cancels within 2 s
- [ ] Run **Failure Modes** with `mode=raise_value_error` → scenario shows failed state with error message
- [ ] Single-session wiring (`default_session`) loads without crash on the data page
- [ ] **Database backend** (requires `uv sync --extra database`):
      `uv run python -m example.main --interface gui --backend database --database-url sqlite:///./tmp_test.db`
      boots end-to-end; delete `<repo>/tmp_test.db` afterwards

## 4 API manual walk

**CWD: `<repo>`** (the API `--example` config also resolves `example/data` relative to here)

- [ ] `uv run algomancy-api --example` boots on port 8051 (override with `--port` if 8051 is busy)
- [ ] `curl http://127.0.0.1:8051/health` → `{"status": "ok", …, "sessions": [...]}`
- [ ] `curl http://127.0.0.1:8051/docs` → Swagger UI renders
- [ ] End-to-end: `POST /api/v1/sessions/default_session/scenarios` with body
      `{"tag":"smoke-api","dataset_key":"example_data","algo_name":"Instant","algo_params":{}}`
      then `POST .../scenarios/{id}/run` → poll `.../status` until `complete`; verify the full GET returns at least one KPI with a numeric value

## 5 Quickstart walk

**CWD: `<tmp>`** — a scratch directory **outside** `<repo>` so the generator can write a brand-new project layout without colliding with the repo.

For at least the combos `(backend=json, interface=gui)` and `(backend=database, interface=api)`:

- [ ] From `<tmp>`, invoke the wizard using the console script installed in `<repo>`'s venv. Pick the form that fits your shell:
      - POSIX: `<repo>/.venv/bin/algomancy-quickstart`
      - Windows: `<repo>\.venv\Scripts\algomancy-quickstart.exe`
      - Or activate the venv first (`source <repo>/.venv/bin/activate`) and run `algomancy-quickstart` directly.
- [ ] Answer the wizard prompts; it writes the generated project into `<tmp>/<project-name>/`.
- [ ] `cd <tmp>/<project-name> && python main.py --validate` exits 0.
- [ ] `cd <tmp>/<project-name> && uv run pytest tests/` exits 0.

## 6 Docs

**CWD: `<repo>`**

- [ ] `uv run sphinx-build -b html docs/source docs/build/html` builds without errors or warnings
- [ ] CHANGELOG entry for `v{VERSION}` written
- [ ] README quickstart section reflects any new flags or interfaces

## 7 PyPI smoke

**CWD: `<fresh-venv>`** — anywhere outside `<repo>`, in a clean venv so we exercise the published wheels, not the local workspace.

- [ ] `pip install algomancy=={VERSION}` succeeds
- [ ] `python -c "import algomancy; print(algomancy.__version__)"` prints `{VERSION}`
      (`__version__` is sourced from `importlib.metadata`, so it tracks the installed wheel automatically)

## 8 Sign-off

- [ ] Reviewer 1: @____________ confirms items 1–7 complete
- [ ] Reviewer 2: @____________ confirms items 1–7 complete

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
