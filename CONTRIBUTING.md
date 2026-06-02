# Contributing to Algomancy

## Running tests

```bash
# Fast suite (no slow or GUI tests) — same as CI on a PR:
uv run pytest tests packages/ -m "not slow and not gui" -v

# Full suite including slow tests — same as CI on push to main:
uv run pytest tests packages/ -m "not gui" -v

# GUI smoke tests (requires 'playwright install chromium'):
uv run pytest -m "gui" -v
```

## Pytest markers

Two custom markers are registered to split the test suite by speed and
infrastructure requirements.

### `@pytest.mark.slow`

Tests marked `slow` take more than a few seconds, typically because they:
- Start a real subprocess (API server, CLI shell).
- Wait for a scenario to run end-to-end.
- Restart a process to verify persistence.

**CI behaviour:** `slow` tests are excluded from PR builds (`-m "not slow"`)
for fast feedback. They run on every push to `main`.

**When to use:** Apply to any test that starts a live process, waits on
real I/O, or takes more than ~3 s.

### `@pytest.mark.gui`

Tests marked `gui` require a running Dash application and a Playwright
browser. They are excluded from all unit/integration runs.

**CI behaviour:** GUI tests run only on push to `main`, in a dedicated job
(`test-gui-smoke`) that installs Playwright with cached Chromium binaries.

**When to use:** Apply to any Playwright-based test that spins up the GUI
server and navigates the browser.

## Release process

See [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) for the pre-release
verification checklist. The gating policy (advisory vs. label-gated) is
documented there.
