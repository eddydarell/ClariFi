#!/usr/bin/env python3
"""Normalized ClariFi CLI entrypoint for machine-readable workflows."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
CORE_MAIN = ROOT / "core" / "main.py"
sys.path.append(str(ROOT))
from database.models import DatabaseManager  # noqa: E402


def _emit(payload: dict[str, Any]) -> int:
    print(json.dumps(payload, separators=(",", ":"), ensure_ascii=True))
    return 0


def _ok(engine: str, data: Any) -> dict[str, Any]:
    return {"status": "ok", "engine": engine, "data": data}


def _err(engine: str, code: str, message: str, details: Any = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"status": "error", "engine": engine, "code": code, "message": message}
    if details is not None:
        payload["details"] = details
    return payload


def _extract_json(stdout: str) -> Any | None:
    text = stdout.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    idx = 0
    last = None
    while idx < len(text):
        next_start = text.find("{", idx)
        if next_start == -1:
            break
        try:
            parsed, end = decoder.raw_decode(text[next_start:])
            last = parsed
            idx = next_start + end
        except json.JSONDecodeError:
            idx = next_start + 1
    return last


def _normalize_delegated_payload(command: str, delegated: Any, raw_stdout: str) -> dict[str, Any]:
    if isinstance(delegated, dict):
        if delegated.get("status") == "error":
            return _err(
                command,
                delegated.get("code", "ENGINE_ERROR"),
                delegated.get("message", "Engine returned an error"),
                delegated,
            )
        if "errors" in delegated and delegated.get("errors"):
            return _err(command, "ENGINE_ERROR", "Engine reported errors", delegated)
        return _ok(command, delegated)
    if delegated is not None:
        return _ok(command, delegated)
    if raw_stdout.strip():
        return _ok(command, {"raw_output": raw_stdout.strip()})
    return _ok(command, {})


def _apply_graph_defaults(args: list[str], pretty: bool, graph: bool) -> list[str]:
    if graph:
        return args

    if not args:
        return args
    cmd = args[0]
    amended = list(args)

    if cmd == "quick" and "--no-visualize" not in amended:
        amended.append("--no-visualize")
    if cmd == "analyze" and "--no-advanced-viz" not in amended:
        amended.append("--no-advanced-viz")
    if cmd == "screen" and "--no-graphs" not in amended:
        amended.append("--no-graphs")

    # visualize exists only for chart generation; skip entirely when graph is off.
    if cmd == "visualize":
        return ["__skip_visualize__"]

    # In pretty mode for chart-heavy commands, disable plots by forcing JSON code paths.
    if pretty and cmd in {"patterns", "correlations", "events", "volatility"} and "--json" not in amended:
        amended = ["--json", *amended]
    return amended


def _parse_ingest_payload(ingest_args: list[str]) -> tuple[list[dict[str, Any]], str]:
    parser = argparse.ArgumentParser(prog="clarifi ingest", add_help=False)
    parser.add_argument("payload", nargs="?")
    parser.add_argument("--file")
    parser.add_argument("--db-path", default=os.environ.get("CLARIFI_DB_PATH", "clarifi.db"))
    ns, _ = parser.parse_known_args(ingest_args)

    raw_input = None
    if ns.file:
        raw_input = Path(ns.file).read_text(encoding="utf-8")
    elif ns.payload:
        if ns.payload == "-":
            raw_input = sys.stdin.read()
        else:
            raw_input = ns.payload
    elif not sys.stdin.isatty():
        raw_input = sys.stdin.read()

    if not raw_input:
        raise ValueError("No ingest payload supplied. Use clarifi ingest '<json>', --file, or stdin.")

    parsed = json.loads(raw_input)
    if isinstance(parsed, dict):
        if "events" in parsed and isinstance(parsed["events"], list):
            events = parsed["events"]
        else:
            events = [parsed]
    elif isinstance(parsed, list):
        events = parsed
    else:
        raise ValueError("Ingest payload must be a JSON object or array.")
    return events, ns.db_path


def _run_ingest(ingest_args: list[str]) -> dict[str, Any]:
    events, db_path = _parse_ingest_payload(ingest_args)
    db = DatabaseManager(db_path)
    inserted: list[dict[str, str]] = []
    for idx, event in enumerate(events):
        if not isinstance(event, dict):
            raise ValueError(f"Event at index {idx} must be a JSON object.")
        event_date = event.get("date") or event.get("event_date")
        title = event.get("event")
        if not event_date or not title:
            raise ValueError(f"Event at index {idx} is missing required fields: date and event.")
        event_id = str(uuid.uuid4())
        db.insert_event(
            event_date=str(event_date),
            event=str(title),
            category=str(event.get("category", "uncategorized")),
            impact=str(event.get("impact", "neutral")),
            summary=str(event.get("summary", "")),
            link=str(event.get("link", "")),
            event_id=event_id,
        )
        inserted.append({"id": event_id, "event_date": str(event_date), "event": str(title)})
    return _ok("ingest", {"inserted_count": len(inserted), "rows": inserted})


def _delegate_to_legacy(command_args: list[str], pretty: bool) -> tuple[int, str, str]:
    cmd = [sys.executable, str(CORE_MAIN)]
    if not pretty and "--json" not in command_args:
        cmd.append("--json")
    cmd.extend(command_args)
    completed = subprocess.run(cmd, capture_output=True, text=True)
    return completed.returncode, completed.stdout, completed.stderr


def main() -> int:
    argv = sys.argv[1:]
    pretty = False
    graph = False
    delegated_args: list[str] = []
    for token in argv:
        if token == "--pretty":
            pretty = True
            continue
        if token == "--graph":
            graph = True
            continue
        delegated_args.append(token)

    if not delegated_args:
        return _emit(_err("cli", "MISSING_COMMAND", "No command provided."))

    command = delegated_args[0]
    delegated_args = _apply_graph_defaults(delegated_args, pretty=pretty, graph=graph)
    if delegated_args == ["__skip_visualize__"]:
        if pretty:
            print("Graph generation skipped (pass --graph to enable).")
            return 0
        return _emit(_ok("visualize", {"skipped": True, "reason": "graph_disabled"}))

    if command == "ingest":
        try:
            payload = _run_ingest(delegated_args[1:])
            if pretty:
                print(json.dumps(payload, indent=2))
                return 0
            return _emit(payload)
        except json.JSONDecodeError as exc:
            return _emit(_err("ingest", "INVALID_JSON", f"Invalid JSON payload: {exc}"))
        except Exception as exc:
            return _emit(_err("ingest", "INGEST_ERROR", str(exc)))

    rc, stdout, stderr = _delegate_to_legacy(delegated_args, pretty=pretty)
    if pretty:
        sys.stdout.write(stdout)
        sys.stderr.write(stderr)
        return rc

    parsed = _extract_json(stdout)
    if rc != 0:
        message = (stderr or stdout or "Command failed").strip()
        return _emit(_err(command, "ENGINE_ERROR", message))
    payload = _normalize_delegated_payload(command, parsed, stdout)
    return _emit(payload)


if __name__ == "__main__":
    raise SystemExit(main())
