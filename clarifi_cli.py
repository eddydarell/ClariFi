#!/usr/bin/env python3
"""Normalized ClariFi CLI entrypoint for machine-readable workflows."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
CORE_MAIN = ROOT / "core" / "main.py"
sys.path.append(str(ROOT))
from database.models import DatabaseManager  # noqa: E402


ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U0001FC00-\U0001FFFD\u2600-\u27BF\uFE0F\u200D]"
)


def _sanitize_output(value: Any) -> Any:
    """Remove terminal decoration and emoji from every CLI-visible value."""
    if isinstance(value, str):
        return EMOJI.sub("", ANSI_ESCAPE.sub("", value))
    if isinstance(value, list):
        return [_sanitize_output(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _sanitize_output(item) for key, item in value.items()}
    return value


def _emit(payload: dict[str, Any], *, indent: int | None = None, exit_code: int = 0) -> int:
    print(json.dumps(
        _sanitize_output(payload),
        indent=indent,
        separators=None if indent is not None else (",", ":"),
        ensure_ascii=True,
    ))
    return exit_code


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
        return _err(
            command,
            "INVALID_ENGINE_OUTPUT",
            "Engine did not produce a complete JSON result",
            {"stdout": raw_stdout.strip()},
        )
    return _err(command, "EMPTY_ENGINE_OUTPUT", "Engine produced no result")


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
    forwarded = list(command_args)

    if "--json" in forwarded:
        forwarded.remove("--json")
    if not pretty:
        cmd.append("--json")

    cmd.extend(forwarded)
    completed = subprocess.run(cmd, capture_output=True, text=True)
    return completed.returncode, completed.stdout, completed.stderr


def main() -> int:
    argv = sys.argv[1:]
    pretty = False
    graph = False
    indent: int | None = None
    delegated_args: list[str] = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--pretty":
            pretty = True
            index += 1
            continue
        if token == "--output":
            if index + 1 >= len(argv) or argv[index + 1] not in {"json", "text"}:
                return _emit(_err("cli", "INVALID_ARGUMENT", "--output must be json or text"), exit_code=2)
            pretty = argv[index + 1] == "text"
            index += 2
            continue
        if token == "--indent":
            indent = 2
            index += 1
            continue
        if token == "--graph":
            graph = True
            index += 1
            continue
        delegated_args.append(token)
        index += 1

    if not delegated_args:
        return _emit(_err("cli", "MISSING_COMMAND", "No command provided."), indent=indent, exit_code=2)

    command = delegated_args[0]
    delegated_args = _apply_graph_defaults(delegated_args, pretty=pretty, graph=graph)
    if delegated_args == ["__skip_visualize__"]:
        if pretty:
            print("Graph generation skipped (pass --graph to enable).")
            return 0
        return _emit(_ok("visualize", {"skipped": True, "reason": "graph_disabled"}), indent=indent)

    if command == "ingest":
        try:
            payload = _run_ingest(delegated_args[1:])
            if pretty:
                print(json.dumps(_sanitize_output(payload), indent=2))
                return 0
            return _emit(payload, indent=indent)
        except json.JSONDecodeError as exc:
            return _emit(_err("ingest", "INVALID_JSON", f"Invalid JSON payload: {exc}"), indent=indent, exit_code=2)
        except Exception as exc:
            return _emit(_err("ingest", "INGEST_ERROR", str(exc)), indent=indent, exit_code=5)

    rc, stdout, stderr = _delegate_to_legacy(delegated_args, pretty=pretty)
    if pretty:
        sys.stdout.write(_sanitize_output(stdout))
        sys.stderr.write(_sanitize_output(stderr))
        return rc

    parsed = _extract_json(stdout)
    if rc != 0:
        message = (stderr or stdout or "Command failed").strip()
        return _emit(_err(command, "ENGINE_ERROR", message), indent=indent, exit_code=5)
    if "--help" in delegated_args or "-h" in delegated_args:
        return _emit(_ok(command, {"help": stdout.strip()}), indent=indent)
    payload = _normalize_delegated_payload(command, parsed, stdout)
    return _emit(payload, indent=indent, exit_code=0 if payload["status"] == "ok" else 5)


if __name__ == "__main__":
    raise SystemExit(main())
