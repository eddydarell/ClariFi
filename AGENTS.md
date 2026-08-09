# ClariFi Agent Guide

## Trust These Sources

- Treat scripts and config as authoritative. The root README is stale about React, port 8000, and nonexistent tests; the active UI is Vue 3 in `frontend/clarifi/`.
- `frontend/ClariFi_backup/` is an older Vuetify app, not the active frontend.
- No Python packaging, lint, type-check, or test config exists. `pytest` is used by `tests/` but is not in `requirements.txt`.

## Runtime And Entrypoints

- `python3 run_clarifi.py` creates/uses root `venv/`, installs requirements, initializes SQLite, changes CWD to `backend/`, and starts `backend/server.py` on 8181.
- Direct `python3 backend/server.py` defaults to 8000; pass `--port 8181` when pairing it with Vite.
- `./start_clarifi.sh` installs Python and npm dependencies, builds the UI, then calls `run_clarifi.py`. Run it only from the repo root.
- `./clarifi.sh` invokes `core/main.py` with the shared `/Users/eddyntambwe/Dev/scripts-project/venv`, not root `venv/`; its absolute path makes it non-portable.
- `setup_venv.sh` deletes root `venv/` before recreating it.
- `backend/server.py` and `core/main.py` manipulate `sys.path` for sibling imports. Moving modules requires updating those path assumptions.
- SQLite, `data/`, and `models/` use relative paths. Because launchers use different CWDs, CLI and web runs can create different databases/artifacts (for example root versus `backend/`).

## Focused Verification

Run frontend commands from `frontend/clarifi/` (Node `^20.19.0 || >=22.12.0`):

```bash
npm run build                         # type-check and Vite build
npm run test:unit -- --run            # one-shot; bare script stays in watch mode
npm run test:unit -- --run src/__tests__/App.spec.ts
npm run type-check
```

- `npm run lint` and `npm run format` modify files; neither is a read-only check.
- `src/__tests__/App.spec.ts` currently fails because the mount does not install Pinia and does not resolve `RouterView`; do not treat that baseline failure as a regression from unrelated work.
- Vite runs on 3000 and proxies `/api` and `/ws` to 8181.
- Versioned JSON endpoints are under `/api/v1`: `/screener`, `/strategy`, `/predictions`, and `/analysis/comprehensive`; responses use `clarifi.result.v1` envelopes with `status`, `data`, `errors`, and `meta`.
- Playwright currently waits for 5173 in development while Vite is fixed to 3000. Fix that config mismatch before relying on `npm run test:e2e`.
- Python focused test: `venv/bin/python -m pytest tests/test_strategy_analyzer.py -q`; install `pytest` separately if absent. Single test example: `venv/bin/python -m pytest tests/test_strategy_analyzer.py::TestInsufficientData::test_returns_hold_with_low_confidence -q`.
- There is no CI or pre-commit configuration to provide additional verification.

## Prediction Paths

- Web `POST /api/strategy` downloads yfinance data, adds indicators, runs seasonality, then calls `StrategyAnalyzer.generate_strategy`; its 5/30/90-day prices are hand-weighted heuristic projections from `core/strategy_analyzer.py`, not AI/ML output.
- The frontend currently calls those strategy projections "AI-powered". Do not preserve or extend that claim unless the API is wired to a validated model.
- `core/ml_analyzer.py`, `core/rnn_analyzer.py`, and `core/transformer_analyzer.py` are separate experimental CLI paths. They have no dedicated API endpoints, and `/api/analysis/comprehensive` does not expose `include_ml` (the engine default is false).
- CLI model filters are computed but not honored: ML and RNN analyzers train every available model, and Transformer dispatch omits `enabled_models`. Expect unexpectedly expensive runs until fixed.
- TensorFlow is intentionally absent from `requirements.txt` for Python 3.14. RNN/Transformer commands are unavailable by default; `TransformerAnalyzer()` currently raises `NameError` rather than a clean dependency error when TensorFlow is missing.
- `models/`, CSV data, and databases are gitignored. Existing model filenames omit ticker/horizon/schema and can overwrite artifacts; scalers and feature schemas are not reliably persisted.

## Improve Predictions Safely

Fix correctness and measurement before adding models:

1. Preserve an unlabeled latest feature row for inference. ML currently shifts the target, drops the newest horizon rows, then predicts from `X.iloc[-1]`, so its "future" sample is historical.
2. Eliminate leakage: ML scales before time-series CV; RNN and Transformer scale before chronological splits. Fit preprocessing on each train fold only, and purge/embargo overlapping horizon labels.
3. Make RNN/Transformer recommendations true forward forecasts. RNN currently differences predictions from historical test windows without inverse scaling; Transformer compares a historical prediction with its known target and calls the residual a return. Add shape checks because Transformer MAPE and DeepAR loss currently broadcast mismatched `(N,)`/`(N,1)` arrays.
4. Build a timestamped prediction ledger and walk-forward evaluation with naive baselines. `compare_predictions_vs_actual` currently uses zero actuals and hard-codes 0.75 accuracy; current tests check heuristic shape/signal behavior, not forecast accuracy or leakage.
5. Repair the heuristic path: `SeasonalAnalyzer.analyze` returns a dataclass while strategy code calls `.get()`; trend slope is already per observation but is divided by 30; horizons mix calendar days, trading rows, and a 40-session statistic for the 90-day target.
6. Repair data loading before comparing models. Downloads write a normal one-row CSV header, but `StockVisualizer.load_stock_data` skips rows 1 and 2. Review outlier interpolation in `StockDownloader.clean_data` so legitimate gaps/corporate actions are not silently rewritten.
7. When persistence is added, key artifacts by ticker, horizon, feature schema, and training timestamp; save preprocessing with the model and test reload inference.

## Other Traps

- Source uses lowercase `frontend/clarifi`, while `start_clarifi.sh` and backend static serving use `frontend/ClariFi`. This works on the current case-insensitive macOS filesystem but fails on case-sensitive systems.
- The active backend build path is now `frontend/clarifi/dist`; keep launcher, Vite, and backend paths lowercase on case-sensitive systems.
- `.vscode/mcp.json` contains a plaintext Alpha Vantage credential. Never reproduce it in output or commits; rotate it and move it to environment configuration.
