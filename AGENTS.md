# ClariFi Agent Guide

## Trust These Sources

- The root README is stale about React/port 8000; the active UI is Vue 3 in `frontend/clarifi/`.
- `frontend/ClariFi_backup/` is an older Vuetify app, not active.
- No Python packaging/lint/typecheck config. `pytest` used by `tests/` but not in `requirements.txt`.
- `backend/server.py` and `core/main.py` manipulate `sys.path` for sibling imports; moving modules requires updating path assumptions.
- SQLite, `data/`, and `models/` use relative paths. Different CWDs create different databases/artifacts.

## Runtime And Entrypoints

- `python3 run_clarifi.py` creates/uses root `venv/`, installs requirements, initializes SQLite, CWD to `backend/`, starts `backend/server.py` on **8181**.
- Direct `python3 backend/server.py` defaults to **8000**; pass `--port 8181` when pairing with Vite.
- `./start_clarifi.sh` installs Python and npm deps, builds UI, then calls `run_clarifi.py`. Run only from repo root.
- `./clarifi.sh` uses the repo-local `venv/`; `./clarifi.sh init` creates it and installs `requirements.txt`. Other commands fall back to system `python3` with a warning if `venv/` is missing.
- `setup_venv.sh` deletes root `venv/` before recreating it.

## Focused Verification

**Frontend (from `frontend/clarifi/`):**
- `npm run build` — type-check and Vite build
- `npm run lint` and `npm run format` modify files; neither is read-only
- Vite runs on **3000**; proxies `/api` and `/ws` to **8181**
- Playwright waits for **5173** in dev while Vite is fixed to 3000. Fix config mismatch before relying on `npm run test:e2e`.
- `src/__tests__/App.spec.ts` currently fails (no Pinia installed, `RouterView` not resolved); do not treat as regression.

**Python tests:**
- `venv/bin/python -m pytest tests/test_strategy_analyzer.py -q` for focused tests
- Example: `venv/bin/python -m pytest tests/test_strategy_analyzer.py::TestInsufficientData::test_returns_hold_with_low_confidence -q`
- No CI or pre-commit configuration

## Prediction Paths

- Web `POST /api/strategy` downloads yfinance data, adds indicators, runs seasonality, then calls `StrategyAnalyzer.generate_strategy`; **5/30/90-day prices are hand-weighted heuristic projections from `core/strategy_analyzer.py`, NOT AI/ML output**.
- The frontend currently calls those projections "AI-powered". Do not preserve or extend that claim unless the API is wired to a validated model.
- `core/ml_analyzer.py`, `core/rnn_analyzer.py`, `core/transformer_analyzer.py` are experimental CLI paths with no dedicated API endpoints; `/api/analysis/comprehensive` does not expose `include_ml` (default false).
- CLI model filters are computed but **not honored**: ML/RNN train every available model; Transformer dispatch omits `enabled_models`. Expect unexpectedly expensive runs.
- TensorFlow intentionally absent from `requirements.txt` for Python 3.14. RNN/Transformer commands unavailable by default; `TransformerAnalyzer()` raises `NameError` (not clean dependency error) when TensorFlow is missing.
- `models/`, CSV data, and databases are **gitignored**. Existing model filenames omit ticker/horizon/schema and can overwrite artifacts; scalers and feature schemas not reliably persisted.

## Other Traps

- Source uses lowercase `frontend/clarifi`, while `start_clarifi.sh` and backend static serving use `frontend/ClariFi`. Works on case-insensitive macOS but fails on case-sensitive systems. Keep all launcher, Vite, and backend paths **lowercase**.
- `.vscode/mcp.json` contains a plaintext Alpha Vantage credential (`ZF6CG2NDNXKUICEO`). **Never reproduce in output or commits**; rotate and move to environment configuration.