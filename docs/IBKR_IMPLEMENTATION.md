# IBKR-Based Autonomous Trading Agent — Implementation Plan

> **Version:** 1.0
> **Date:** 2026-09-08
> **Broker:** Interactive Brokers (IBKR) via IB Gateway + TWS API
> **Purpose:** An autonomous agent that ingests trading signals from an external analysis engine (or user input), monitors market prices with the lowest practical latency, executes orders programmatically (including bracket/stop-loss/take-profit), and produces a comprehensive, auditable action log.

---

## 1. Objectives & Scope

### 1.1 Primary goals

| Goal | Description |
| --- | --- |
| **Autonomous order execution** | Agent places, modifies, and cancels orders based on signals from an external analysis engine or manual user input. No human in the loop during normal operation. |
| **Low-latency price monitoring** | Stream live ticker prices (IBKR market data subscriptions, WebSocket/streaming callbacks) rather than polling. |
| **Bracket/risk orders** | Every position opened by the agent should be protected with stop-loss and take-profit legs (IBKR bracket / OCO orders) unless explicitly overridden. |
| **Comprehensive logging** | Every external input, internal decision, API call, order event, fill, error, and heartbeat is logged with structured, timestamped records in JSON — persisted to PostgreSQL, not just files. |
| **Auditability** | Full replay of any decision: "why did the agent buy 100 VOLV-B.ST at 312.40 on 2026-09-08 09:31:12?" must be answerable from the log store alone. |

### 1.2 Markets

The agent targets securities on **Nasdaq Stockholm (.ST)**, **Toronto (.TO)**, **Xetra (.DE)**, and **US (.NYSE/.NASDAQ)** — all supported by IBKR (170 markets, 40 countries).

### 1.3 Non-goals (explicitly out of scope for v1)

- No strategy research / alpha generation inside the agent (it consumes signals).
- No options/futures/complex multi-leg spreads (stocks and ETFs only in v1).
- No real money in v1 (paper trading mandatory, see §9).
- No web UI (v1 exposes a REST/WebSocket control API; dashboards are Grafana-based).

---

## 2. High-Level Architecture

```javascript
                        ┌───────────────────────────────┐
                        │   Signal Sources (external)   │
                        │                               │
                        │  ┌─────────────────────────┐  │
                        │  │ Analysis Engine (LLM /  │  │
                        │  │ quant pipeline)         │  │
                        │  └────────────┬────────────┘  │
                        │  ┌────────────┴────────────┐  │
                        │  │ Manual user input       │  │
                        │  │ (CLI / REST / Telegram) │  │
                        │  └────────────┬────────────┘  │
                        └───────────────┼───────────────┘
                                        │  REST / WebSocket  (authenticated)
                                        ▼
                        ┌───────────────────────────────┐
                        │        Control API            │
                        │  (FastAPI, auth, validation)  │
                        └───────────────┬───────────────┘
                                        │
                                        ▼
┌──────────────┐   ┌───────────────┐   ┌───────────────────────────────┐   ┌───────────────┐
│ Market Data  │──▶│  Redis        │   │        TRADING AGENT          │──▶│ PostgreSQL    │
│ Ingestor     │   │  (live state) │──▶│                               │   │ (audit trail, │
│ (IBKR stream)│   │               │   │  ┌─────────────┐              │   │  positions,   │
└──────────────┘   └───────────────┘   │  │ Signal      │              │   │  trade ledger)│
                                       │  │ Processor   │              │   └───────────────┘
                                       │  ├─────────────┤              │
                                       │  │ Risk Engine │              │   ┌───────────────┐
                                       │  ├─────────────┤              │──▶│ Alerting      │
                                       │  │ Order       │              │   │ (Telegram /   │
                                       │  │ Manager     │              │   │  email / ntfy)│
                                       │  ├─────────────┤              │   └───────────────┘
                                       │  │ Reconciler  │              │
                                       │  └─────────────┘              │
                                       └───────────────┬───────────────┘
                                                       │  TWS API (TCP 7497/4001 paper,
                                                       ▼   7496/4000 live)
                                       ┌───────────────────────────────┐
                                       │        IB GATEWAY             │
                                       │  (headless, 24/7, auto-login) │
                                       └───────────────┬───────────────┘
                                                       │
                                                       ▼
                                               ┌─────────────┐
                                               │     IBKR    │
                                               └─────────────┘
```

**Key design decision: market data and execution are decoupled.** The agent uses IBKR for *execution* and, where subscribed, for *market data* — but the ingestor is an isolated component that can be swapped to Finnhub/Yahoo/etc. for delayed data if real-time exchange subscriptions are not purchased (see §5.3). Signals flow in through the Control API; nothing the broker does can directly mutate strategy state.

---

## 3. Tech Stack

| Layer | Choice | Rationale |
| --- | --- | --- |
| Language | **Python 3.12** | First-class IBKR client libraries; ecosystem for quant/finance. |
| IBKR client | **`ib_async`** (successor to `ib_insync`) | High-level async wrapper over TWS API; event-driven callbacks; battle-tested. |
| Async runtime | **asyncio** | Single event loop handles streaming callbacks, REST server, timers. |
| API framework | **FastAPI** (with uvicorn) | Async-native; automatic OpenAPI docs for the signal endpoint; easy auth via API keys. |
| Live state cache | **Redis 7** | Pub/sub for price ticks and order events; hot state (positions, open orders, last prices) with TTLs. |
| Persistent store | **PostgreSQL 16** | Source of truth for audit log, order/fill ledger, positions, daily snapshots. |
| Task/heartbeat | **APScheduler** (in-process) or cron-style container | Kill-switch checks, reconciler, periodic DB snapshots. |
| Containerization | **Docker + docker-compose** | Reproducible homelab/server deployment; IB Gateway as its own service. |
| Observability | **Prometheus + Grafana** | Metrics: latency histograms, order counts, errors, P&L, connection state. |
| Structured logging | **`structlog`** → JSON | Every log line is machine-parseable; correlation IDs tie signals → decisions → orders → fills. |
| Config/secrets | **pydantic-settings** + `.env` + Docker secrets | Typed config; no secrets in code. |
| Alerting | **Telegram Bot API** / **ntfy.sh** / SMTP | Human notified on fills, errors, kill-switch triggers. |
| Time sync | **chrony/ntp** on host | Millisecond-accurate local timestamps for latency measurement. |

### 3.1 Repository layout

```javascript
trading-agent/
├── docker-compose.yml
├── .env.example
├── README.md
├── ibkr-trading-agent/
│   ├── pyproject.toml
│   ├── src/
│   │   ├── main.py                  # entrypoint: boots all components
│   │   ├── config.py                # pydantic settings
│   │   ├── api/
│   │   │   ├── server.py            # FastAPI app
│   │   │   ├── auth.py              # API-key auth, rate limiting
│   │   │   └── schemas.py           # Signal/order request models
│   │   ├── broker/
│   │   │   ├── gateway.py           # IB Gateway connection, reconnect logic
│   │   │   ├── market_data.py       # tick/quote streaming handlers
│   │   │   └── orders.py            # order builders, bracket/OCO helpers
│   │   ├── core/
│   │   │   ├── signals.py           # ingest + validate external signals
│   │   │   ├── risk.py              # risk engine (§7)
│   │   │   ├── portfolio.py         # position/PNL tracking
│   │   │   └── reconcile.py         # broker-vs-local state reconciliation
│   │   ├── storage/
│   │   │   ├── db.py                # SQLAlchemy/asyncpg session
│   │   │   ├── models.py            # tables: signals, decisions, orders, fills, audit_log
│   │   │   └── redis_client.py
│   │   ├── observability/
│   │   │   ├── logging.py           # structlog setup
│   │   │   ├── metrics.py           # Prometheus counters/histograms
│   │   │   └── alerts.py            # Telegram/ntfy notifications
│   │   └── utils/
│   │       └── time.py              # UTC handling, latency timestamps
│   └── tests/
├── ib-gateway/
│   ├── Dockerfile                   # IBC + IB Gateway auto-login
│   └── config.ini                   # IBC config (credentials via env/secrets)
└── grafana/ / prometheus/           # provisioning configs
```

---

## 4. IBKR Integration Details

### 4.1 Gateway choice: IB Gateway, not TWS

|  | TWS | **IB Gateway** ✅ |
| --- | --- | --- |
| Headless-friendly | No (GUI) | Yes |
| Memory footprint | ~1–2 GB | ~300–500 MB |
| API port | 7496/7497 | 4000/4001 (or 7496/7497) |
| Auto-restart | Manual | Automated with **IBC** |

Use **IBC (IB Controller)** to auto-start IB Gateway, handle login, and auto-restart after daily maintenance (~00:45–01:00 ET). Host the gateway in its own container with restart-policy `unless-stopped`.

```yaml
# docker-compose.yml (excerpt)
services:
  ib-gateway:
    image: ghcr.io/quantconnect/ibgateway:latest   # or official + IBC
    environment:
      TWS_USERID: ${IBKR_USERNAME}
      TWS_PASSWORD: ${IBKR_PASSWORD}
      TRADING_MODE: paper            # 'live' only after sign-off
      VNC_SERVER_PASSWORD: ${VNC_PASSWORD}
    ports:
      - "4001:4001"                  # paper API (4002 live)
    restart: unless-stopped
```

### 4.2 Connection strategy (agent side)

- Connect via `ib_async.IB()` to `host=ib-gateway, port=4001, clientId=<unique>`.
- **Supervision loop:** watch `ib.isConnected()`; on disconnect → exponential backoff reconnect (1s → 2s → 5s → max 30s). IBKR allows one reconnect without restarting Gateway.
- **Event-driven handlers** registered once at startup:
- `ib.tickEvent` / `ib.pendingTickersEvent` → price updates (see §6)
- `ib.orderStatusEvent` → order lifecycle (Submitted → Filled → Cancelled)
- `ib.execDetailsEvent` → fill details (price, qty, commission)
- `ib.accountValueEvent` / `ib.positionEvent` → NAV, positions
- `ib.errorEvent` → structured error logging (IBKR error codes: 2104/2106 connectivity, 1100/1102 disconnect/reconnect, etc.)
- Every event handler is **async and non-blocking**; heavy work (DB writes) is queued via `asyncio.Queue` with a background writer so a slow DB never stalls the event loop and increases latency.

### 4.3 Order types (all available via API)

- Market / Limit / Stop / Stop-Limit
- **Bracket order** (parent + take-profit child + stop-loss child) — the default for any agent-initiated entry
- **Trailing stop**
- OCO (one-cancels-other) groups for scaling out
- Attached/adjustable orders

Example — signal "buy 100 VOLV-B.ST if below 315, TP 330, SL 300" becomes one bracket transmitted atomically:

```python
from ib_async import Stock, LimitOrder, StopOrder

contract = Stock('VOLV-B', 'SFB', 'SEK')          # Stockholm: exchange SFB, currency SEK
bracket = ib.bracketOrder(
    action='BUY', quantity=100,
    limitPrice=315.0,          # entry
    takeProfitPrice=330.0,     # child 1
    stopLossPrice=300.0,       # child 2
)
for o in bracket:
    o.tif = 'GTC'
    o.transmit = (o is bracket[-1])     # transmit all at once on last leg
trade = ib.placeOrder(contract, bracket[0])
for child in bracket[1:]:
    child.parentId = trade.order.orderId
    ib.placeOrder(contract, child)
```

> **Currency/exchange mapping table** (verify at startup against `ib.reqContractDetails`):
> `.ST` → `exchange='SFB'` (or `OMXSTO`), currency `SEK` · `.TO` → `exchange='TSE'`, currency `CAD` · `.DE` → `exchange='SMART', primaryExchange='IBIS'`, currency `EUR` · US → `exchange='SMART'`, currency `USD`.

### 4.4 Contract validation before every order

1. `ib.reqContractDetails(contract)` → confirm tradable, get conId.
2. Check market hours for the instrument's exchange (IBKR `reqMarketRule`, or a local calendar table for XSTO/TSX/IBIS/NYSE).
3. Check agent has market-data permission for the symbol (`reqMktDataType` + error 354 handling → log clearly if delayed data is being used).

---

## 5. Market Data & Latency Plan

### 5.1 Hard constraints

- IBKR **TWS API tick streaming** is the lowest-latency path available without FIX/CTCI (retail-grade; realistically tens of ms from exchange to callback, dominated by network to IBKR's servers and the Gateway itself — this is **not** HFT, and the plan doesn't pretend to be).
- There is **no free real-time exchange data** at IBKR. Real-time L1/L2 for XSTO, TSX, IBIS, NYSE/NASDAQ requires per-exchange subscriptions (roughly USD 4–20/exchange/month, waivable with commissions for some).

### 5.2 Latency optimization measures (in priority order)

1. **Stream, never poll.** Use `reqMktData` subscriptions with `genericTickList` and event callbacks. One subscription per watched symbol; IBKR caps simultaneous streams (~100 per Gateway session by default — request a bump if needed).
2. **Colocate logically:** run the agent container and IB Gateway on the **same Docker network/host** → intra-datacenter hop only. Optionally run on a VPS in the same region as IBKR's servers (e.g., Europe: Sweden/Germany VPS for XSTO/IBIS data) — the Stockholm exchange data then enters IBKR's EU infrastructure with less transatlantic lag than a US-hosted homelab. (Live in v1: homelab + same-host containers; VPS is an easy migration since everything is containerized.)
3. **Keep the event loop clean:** all event handlers < 1 ms of CPU; DB writes via queue; batch Redis pipelines.
4. **Timestamps at three points:** `t_exchange` (IBKR tick timestamp where available) → `t_received` (agent event loop, `time.time_ns()`) → `t_processed`. Histogram (`prometheus_client.Histogram`) of `t_processed − t_received` per symbol; alert if p99 > 500 ms.
5. **Deduplicate & batch:** IBKR aggregates ticks; use `ib.pendingTickersEvent` and read the last quote for each ticker rather than per-tick work.
6. **Market-data type:** `ib.reqMarketDataType(1)` (real-time) when subscribed; fall back to type 3 (delayed) with a loud warning if not subscribed.
7. **Snapshots in Redis only; truth in PostgreSQL.** Redis holds `{symbol: {bid, ask, last, ts}}` with short TTL; every N seconds (configurable, default 5 s) a writer persists snapshots for P&L/audit; full tick history optional and off by default (volume is huge; keep `last` + VWAP-ish aggregates).

### 5.3 Fallback / decoupled design

- If a market-data subscription lapses or is missing: the ingestor can switch that symbol's feed to **Finnhub/Yahoo delayed** via an adapter interface `MarketDataAdapter` (methods: `subscribe(symbol)`, `unsubscribe(symbol)`, callback `on_quote`). The rest of the agent (risk engine, order manager) never knows the difference — quotes are normalized to `{symbol, bid, ask, last, ts, source}` in Redis.
- Signal payloads may carry the analysis engine's own price estimate; the agent always validates against its live quote (configurable max staleness, default 2 s) before market orders, and re-prices limit orders if stale.

---

## 6. Signal Ingestion (External Analysis Engine / User Input)

### 6.1 Signal schema (REST `POST /v1/signals`, API-key authenticated)

```json
{
  "signal_id": "ae-2026-09-08-000114",          // idempotency key (required)
  "symbol": "VOLV-B.ST",
  "action": "BUY",                              // BUY | SELL | CLOSE | REDUCE
  "quantity": 100,
  "order_type": "LIMIT",                        // MARKET | LIMIT | STOP
  "limit_price": 315.0,
  "take_profit": 330.0,
  "stop_loss": 300.0,
  "valid_until": "2026-09-08T15:00:00Z",        // signal expiry
  "source": "analysis-engine",
  "rationale": "momentum breakout, vol expansion",  // free text, stored verbatim
  "confidence": 0.78,                           // optional, stored, can gate sizing
  "client_tag": "strategy-x/v3.2"
}
```

### 6.2 Pipeline

```javascript
POST /v1/signals
   │
   ▼
┌─────────────────┐
│ 1. Auth (API key│──401 on failure──▶ audit_log
│    + rate limit)│
└────────┬────────┘
         ▼
┌─────────────────┐
│ 2. Validate     │──422──▶ audit_log (schema errors)
│    (pydantic)   │
└────────┬────────┘
         ▼
┌─────────────────┐
│ 3. Idempotency  │──duplicate signal_id → return prior decision──▶ audit_log
└────────┬────────┘
         ▼
┌─────────────────┐
│ 4. Persist      │──audit_log: signal_received
│    signal (DB)  │
└────────┬────────┘
         ▼
┌─────────────────┐
│ 5. Risk engine  │──rejected → 200 {status:"rejected", reasons:[...]}──▶ audit_log
│    evaluation   │
└────────┬────────┘
         ▼
┌─────────────────┐
│ 6. Order manager│──order events──▶ audit_log
│    (bracket)    │
└────────┬────────┘
         ▼
   Response 202 {status:"accepted", decision_id}
         +
   WebSocket push to subscribers
```

**Idempotency:** `signal_id` unique in DB; retries from the analysis engine return the original decision. **Exactly-once execution** on the agent side; at-least-once delivery tolerated from sources.

### 6.3 User input channel

- Same schema via CLI (`agent-cli signal --symbol AC.TO --action BUY ...`) calling the local API.
- Telegram bot (read-only status + a "confirm-to-trade" channel): signals from chat require explicit confirmation unless `--auto` mode is on. Every confirmation is logged.
- Manual overrides: `POST /v1/positions/{symbol}/flatten` (close now), `POST /v1/orders/{id}/cancel`, `POST /v1/kill` (kill switch, §7.4).

---

## 7. Risk Engine

Risk checks run **synchronously inside the signal pipeline** before any order is built. All checks are pure functions over: signal, live quotes (Redis), current positions (broker + local), account NAV (broker), and config.

| # | Check | Default limit (configurable) | On failure |
| --- | --- | --- | --- |
| R1 | Max position value per symbol | 5% of NAV | reject |
| R2 | Max total gross exposure | 60% of NAV | reject |
| R3 | Max daily loss | 3% of NAV → **kill switch** | flatten optional + halt |
| R4 | Max open orders | 20 | reject |
| R5 | Max orders / minute | 10 | reject + alert |
| R6 | Price sanity | signal price vs live quote within ±2% | reject (stale/missing data) |
| R7 | Market-hours check | symbol's exchange must be open (or allow extended-hours flag per signal) | reject |
| R8 | Symbol whitelist | agent may only trade configured tickers | reject |
| R9 | Duplicate exposure | same-symbol same-direction open signal within T minutes | reject or merge |
| R10 | Kill-switch state | any active halt blocks all new orders | reject |

**Position sizing:** v1 = fixed quantity from the signal, clamped by R1/R2. Optional later: volatility-based sizing from analysis engine `confidence` field.

### 7.1 Stop-loss discipline

- Every opening order **must** carry a bracket (TP + SL) unless the signal sets `stop_loss: null` **and** config `allow_unprotected=false`… v1 simply forbids unprotected entries.
- Agent-side protective monitor: independent of IBKR server-side stops, a watchdog compares live prices against in-memory stop levels every tick; if a server-side stop is missed (fill gap, disconnect), it fires an emergency market order. Belt and suspenders.

### 7.2 Reconciler (runs every 60 s and on reconnect)

1. Pull open orders + positions from IBKR.
2. Compare with local PostgreSQL state.
3. Discrepancy classes: *missing locally* (broker has order we don't) → adopt or cancel per policy; *missing remotely* (we think open, broker closed) → mark closed, investigate fills; *qty/price mismatch* → alert + quarantine symbol (block new orders) pending human review.
4. All reconciliation actions → `audit_log` entries with `actor=reconciler`.

### 7.3 Failure modes & responses

| Failure | Detection | Response |
| --- | --- | --- |
| IB Gateway down / disconnected | connection watchdog | stop new orders; attempt reconnect; alert after 60 s |
| Agent container crash | Docker restart policy | auto-restart; on boot: load state from DB, run reconciler, **resume monitoring stops** before accepting signals |
| Partial bracket (entry filled, child failed) | order status events | immediate alert + auto-place protective stop; symbol quarantined |
| Duplicate fill (retry storm) | idempotency on client order ref | dedupe via `client_order_ref = f"{signal_id}-{leg}"` |
| Clock drift | chrony monitor | alert; reject latency-sensitive ops if > 250 ms |

### 7.4 Kill switch

- `POST /v1/kill` (API key or Telegram) → set `state=HALTED` in Redis + DB, **cancel all open orders**, optional `flatten=true` market-close of all positions, alert to all channels.
- Auto-triggers: daily-loss limit (R3), 3 consecutive risk rejections, reconciler unresolvable mismatch.
- Resume: `POST /v1/kill/clear` + requires reason string (logged).

---

## 8. Logging & Audit Trail (the "logs everything" requirement)

### 8.1 Principles

- **Structured JSON everywhere** via structlog: `{"ts": "2026-09-08T07:31:12.482113Z", "level": "info", "event": "order_submitted", "correlation_id": "...", ...fields}`.
- **Correlation ID** end-to-end: `signal_id` → `decision_id` → `order_id`/`permId`/`client_order_ref` → `exec_id`. Every log line and DB row in the chain carries it.
- **Dual writes:** application logs (JSONL, rotated daily, stdout for Docker) **and** audit tables in PostgreSQL (queryable, durable). Never one without the other for order-related events.
- **Secrets redaction** at the formatter level (API keys, IBKR creds never logged).
- **Clock:** all timestamps UTC ISO-8601 with milliseconds; `latency_ms` fields computed and stored for every broker round trip.

### 8.2 Audit tables (PostgreSQL)

| Table | Key rows | Purpose |
| --- | --- | --- |
| `audit_log` | id, ts, event_type, actor, correlation_id, payload jsonb, severity | **Append-only** master log of every notable event |
| `signals` | signal_id, received_at, payload, validation_result | Raw + validated external input |
| `decisions` | decision_id, signal_id, risk_checks jsonb, outcome (accepted/rejected), reasons | Why the agent did/didn't act |
| `orders` | order_id, perm_id, parent_id, con_id, symbol, action, qty, type, lmt/stp prices, status, submitted_at, updated_at | Full order lifecycle mirror |
| `fills` | exec_id, order_id, ts, qty, price, commission, exchange | Immutable fill ledger |
| `positions` | con_id, symbol, qty, avg_cost, unrealized_pnl, as_of | Point-in-time positions |
| `account_snapshots` | ts, nav, cash, margin_used | Daily/hourly NAV for R3 + reporting |
| `system_events` | ts, component, event (connect, disconnect, restart, kill) | Ops trace |

Events that MUST create `audit_log` rows: signal received/invalid/duplicate, decision made, order submitted/modified/cancelled/filled/rejected, risk rejection, reconciler action, kill-switch trigger/clear, reconnects, errors, config changes.

### 8.3 Metrics (Prometheus)

`ticks_received_total{symbol,source}`, `signal_to_order_latency_seconds` histogram, `broker_request_latency_seconds`, `orders_total{status}`, `fills_total`, `rejections_total{reason}`, `pnl_gauge{symbol}`, `ib_connected`, `redis_up`, `position_value_ratio`, `daily_loss_ratio`.

### 8.4 Alerting rules (examples)

- Fill on any order → Telegram summary (symbol, qty, price, P&L impact).
- Kill switch triggered → immediate alert.
- IBKR disconnect > 60 s → alert.
- Daily loss > 50% of limit → warning.
- Reconciler finds mismatch → alert + quarantine.

---

## 9. Deployment Plan

### 9.1 Environments

| Env | Broker endpoint | Purpose |
| --- | --- | --- |
| **dev** | `ib-gateway` paper (4001) | Unit tests, contract mapping tables, order-builder dry runs |
| **staging/paper** | `ib-gateway` paper (4001) | Full integration: real streaming data, simulated fills, 2–4 weeks soak |
| **live** | `ib-gateway` live (4002) | Only after paper sign-off checklist (§11) |

`TRADING_MODE` is an env var — flipping to live also requires `ENABLE_LIVE=true` in the agent config (two-key ignition, prevents accidents).

### 9.2 docker-compose services

| Service | Image | Notes |
| --- | --- | --- |
| `ib-gateway` | official IB Gateway + IBC | auto-login, restart unless-stopped, healthcheck on port 4001/4002 |
| `agent` | built from repo | depends_on gateway healthy; restart unless-stopped; read-only root fs |
| `postgres` | postgres:16 | named volume `pgdata`; daily `pg_dump` cron sidecar to host dir |
| `redis` | redis:7 | AOF persistence; appendonly yes |
| `prometheus` | prom/prometheus | scrape agent `/metrics` |
| `grafana` | grafana/grafana | provisioned dashboards: positions, orders, latency, P&L, system health |
| `backup` | offen/docker-volume-backup (optional) | nightly DB + config backup to S3/Backblaze |

### 9.3 Secrets

- `.env` (git-ignored): IBKR username/password, API keys, DB password, Telegram token. In production use Docker secrets or a vault; never bake into images.
- API keys for signal sources: hashed at rest, rotatable via `POST /v1/keys`.

### 9.4 Host requirements

- Any always-on x86_64 machine (homelab NUC / VPS): 2 vCPU, 4 GB RAM (Gateway ~0.5 GB, agent <0.5 GB, DB/Redis/Grafana ~1.5 GB), SSD.
- Stable internet; wired preferred. UPS if homelab.
- Chrony NTP. Host TZ = UTC.

---

## 10. Implementation Phases

| Phase | Scope | Exit criteria |
| --- | --- | --- |
| **0 — Foundations (wk 1)** | Repo skeleton, docker-compose (Postgres/Redis), config, structlog, CI lint/tests | `make up` boots infra; log pipeline writes JSON to stdout + DB |
| **1 — Broker connectivity (wk 2)** | Gateway container + IBC auto-login, `ib_async` connection with supervision/reconnect, contract-details cache incl. .ST/.TO/.DE mapping | 24 h stable connection incl. IBKR daily restart; error events logged |
| **2 — Market data (wk 3)** | Streaming subscriptions, Redis quote cache, latency histograms, delayed-data fallback adapter | p99 tick→process latency measured & reported; Grafana latency dashboard |
| **3 — Order execution (wk 3–4)** | Order builders incl. bracket/OCO, idempotent order refs, status/exec handlers, position tracker | Paper trades execute with brackets; every event lands in audit tables |
| **4 — Signals API + risk engine (wk 5)** | FastAPI auth'd endpoints, schema, idempotency, R1–R10 checks, kill switch | Full pipeline signal→decision→order in paper; rejection paths tested |
| **5 — Observability & alerts (wk 6)** | Prometheus/Grafana dashboards, Telegram alerting, log queries runbook | Alert test matrix passes (disconnect, fill, kill, reconciler mismatch) |
| **6 — Reconciler & hardening (wk 6–7)** | Reconciler, watchdog protective stops, crash-recovery path, chaos tests (kill -9 agent mid-order, gateway restart mid-fill) | Recovery drills pass; no duplicate orders in any drill |
| **7 — Paper soak (wk 8–10)** | Run live-signal replay + real signals against paper, tune limits, weekly reviews | 2–4 weeks clean, latency SLO met, zero unreconciled states |
| **8 — Live go-live (wk 11+)** | Two-key enable, tiny size caps (R1 ≤ 1%), human supervision window, rollback plan | First live week: daily reviews, then gradual ramp |

---

## 11. Sign-off Checklist Before Live Trading

- [ ] Paper environment ran ≥ 2 weeks with zero unreconciled discrepancies
- [ ] Kill switch tested live in paper (cancel + flatten)
- [ ] Crash-recovery drills passed (agent killed mid-bracket, gateway killed mid-fill)
- [ ] Contract mapping verified for every whitelisted ticker across all four markets
- [ ] Market-data subscriptions active for all traded exchanges (or delayed mode explicitly acknowledged in writing)
- [ ] Alerting verified end-to-end (Telegram reachable from host)
- [ ] DB backups tested (restore from dump)
- [ ] Risk limits reviewed and set conservatively (R1 ≤ 1% of NAV for first live week)
- [ ] `ENABLE_LIVE=true` documented procedure requiring manual two-key activation

---

## 12. Open Questions / Decisions to Record

| Question | Default answer (decide before Phase 4) |
| --- | --- |
| Real-time exchange subscriptions: which exchanges? | Start with XSTO + TSX if those are the primary markets (~USD 10–20/mo total); US stocks need NYSE/NASDAQ bundles if traded |
| Tick persistence: full tick store? | No in v1 (last-quote snapshots every 5 s). Add TimescaleDB later if backtests need intraday data |
| Signal auth model | Static API keys, one per source, IP allow-list optional |
| Where is the host? | v1 homelab; evaluate EU VPS after measuring end-to-end tick latency |
| Second broker for redundancy? | Out of scope; IBKR is single point of execution failure (mitigated by kill switch + alerts) |
