import json

from clarifi_cli import _extract_json, _normalize_delegated_payload, _sanitize_output


def test_cli_output_sanitizer_removes_emoji_and_ansi_sequences():
    payload = {"message": "\x1b[32mCompleted \u2705\x1b[0m", "nested": ["Target \U0001f3af"]}

    assert _sanitize_output(payload) == {"message": "Completed ", "nested": ["Target "]}


def test_non_json_engine_output_is_reported_as_an_error():
    payload = _normalize_delegated_payload("strategy", None, "legacy output")

    assert payload["status"] == "error"
    assert payload["code"] == "INVALID_ENGINE_OUTPUT"


def test_extract_json_requires_a_complete_json_object():
    assert _extract_json('{"status":"ok"}') == {"status": "ok"}
    assert _extract_json('{"status":"ok"') is None


def test_cli_help_is_serializable_without_emoji():
    payload = {"status": "ok", "engine": "cli", "data": {"help": "Strategy \U0001f3af"}}

    encoded = json.dumps(_sanitize_output(payload), ensure_ascii=True)

    assert "\\ud83c" not in encoded