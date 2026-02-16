# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import importlib
import pathlib
import sys
import unittest


THIS_DIR = pathlib.Path(__file__).resolve().parent
SCRIPTS_MODULES_DIR = THIS_DIR.parents[1] / "scripts" / "modules"
sys.path.append(str(SCRIPTS_MODULES_DIR))

contract = importlib.import_module("_bpy_internal.llm_runtime.tool_envelope_contract")
json_parsing = importlib.import_module("_bpy_internal.llm_runtime.tool_envelope_json_parsing")


class CanonicalToolCallContractTest(unittest.TestCase):
    def test_parse_valid_tool_call_payload(self) -> None:
        parser = json_parsing.ValidatingParser()
        payload = {
            "provider": "openai",
            "call_id": "call-1",
            "tool_name": "get_weather",
            "arguments": {"location": "Boston"},
            "raw_request": {},
            "raw_response": {},
            "received_at": "2026-02-16T00:00:00Z",
            "trace_id": "trace-1",
            "session_id": "session-1",
            "policy": {
                "risk_level": "low",
                "requires_confirmation": False,
                "timeout_ms": 120000,
            },
        }
        model = parser.parse_and_validate(contract.CanonicalToolCall, payload)
        self.assertEqual(model.call_id, "call-1")
        self.assertEqual(model.policy.risk_level, contract.RiskLevel.LOW)

    def test_missing_required_field_fails(self) -> None:
        parser = json_parsing.ValidatingParser()
        payload = {
            "provider": "openai",
            "tool_name": "get_weather",
            "arguments": {"location": "Boston"},
            "raw_request": {},
            "raw_response": {},
            "received_at": "2026-02-16T00:00:00Z",
            "trace_id": "trace-1",
            "session_id": "session-1",
            "policy": {
                "risk_level": "low",
                "requires_confirmation": False,
                "timeout_ms": 120000,
            },
        }
        with self.assertRaises(Exception):
            parser.parse_and_validate(contract.CanonicalToolCall, payload)

    def test_unknown_fields_are_tolerated(self) -> None:
        parser = json_parsing.ValidatingParser()
        payload = {
            "provider": "openai",
            "call_id": "call-1",
            "tool_name": "get_weather",
            "arguments": {"location": "Boston"},
            "raw_request": {},
            "raw_response": {},
            "received_at": "2026-02-16T00:00:00Z",
            "trace_id": "trace-1",
            "session_id": "session-1",
            "future_field": "ignored",
            "policy": {
                "risk_level": "low",
                "requires_confirmation": False,
                "timeout_ms": 120000,
                "future_policy_field": 1,
            },
        }
        model = parser.parse_and_validate(contract.CanonicalToolCall, payload)
        self.assertEqual(model.call_id, "call-1")

    def test_missing_required_policy_field_fails(self) -> None:
        parser = json_parsing.ValidatingParser()
        payload = {
            "provider": "openai",
            "call_id": "call-1",
            "tool_name": "get_weather",
            "arguments": {"location": "Boston"},
            "raw_request": {},
            "raw_response": {},
            "received_at": "2026-02-16T00:00:00Z",
            "trace_id": "trace-1",
            "session_id": "session-1",
            "policy": {
                "risk_level": "low",
                "requires_confirmation": False,
            },
        }
        with self.assertRaises(Exception):
            parser.parse_and_validate(contract.CanonicalToolCall, payload)

    def test_invalid_risk_level_fails(self) -> None:
        parser = json_parsing.ValidatingParser()
        payload = {
            "provider": "openai",
            "call_id": "call-1",
            "tool_name": "get_weather",
            "arguments": {"location": "Boston"},
            "raw_request": {},
            "raw_response": {},
            "received_at": "2026-02-16T00:00:00Z",
            "trace_id": "trace-1",
            "session_id": "session-1",
            "policy": {
                "risk_level": "LOW",
                "requires_confirmation": False,
                "timeout_ms": 120000,
            },
        }
        with self.assertRaises(Exception):
            parser.parse_and_validate(contract.CanonicalToolCall, payload)


class CanonicalToolResultContractTest(unittest.TestCase):
    def test_parse_valid_tool_result_payload(self) -> None:
        parser = json_parsing.ValidatingParser()
        payload = {
            "provider": "openai",
            "call_id": "call-1",
            "tool_name": "get_weather",
            "ok": False,
            "result": None,
            "error_class": "validation",
            "error_message": "missing required arg",
            "trace_id": "trace-1",
            "session_id": "session-1",
        }
        model = parser.parse_and_validate(contract.CanonicalToolResult, payload)
        self.assertEqual(model.error_class, contract.NormalizedErrorClass.VALIDATION)

    def test_parse_all_normalized_error_classes(self) -> None:
        parser = json_parsing.ValidatingParser()
        base_payload = {
            "provider": "openai",
            "call_id": "call-1",
            "tool_name": "get_weather",
            "ok": False,
            "result": None,
            "error_message": "error",
            "trace_id": "trace-1",
            "session_id": "session-1",
        }
        cases = [
            ("validation", contract.NormalizedErrorClass.VALIDATION),
            ("permission", contract.NormalizedErrorClass.PERMISSION),
            ("runtime", contract.NormalizedErrorClass.RUNTIME),
            ("timeout", contract.NormalizedErrorClass.TIMEOUT),
            ("provider", contract.NormalizedErrorClass.PROVIDER),
        ]
        for error_class_value, expected in cases:
            with self.subTest(error_class=error_class_value):
                payload = dict(base_payload)
                payload["error_class"] = error_class_value
                model = parser.parse_and_validate(contract.CanonicalToolResult, payload)
                self.assertEqual(model.error_class, expected)

    def test_invalid_error_class_fails(self) -> None:
        parser = json_parsing.ValidatingParser()
        payload = {
            "provider": "openai",
            "call_id": "call-1",
            "tool_name": "get_weather",
            "ok": False,
            "result": None,
            "error_class": "unknown",
            "error_message": "error",
            "trace_id": "trace-1",
            "session_id": "session-1",
        }
        with self.assertRaises(Exception):
            parser.parse_and_validate(contract.CanonicalToolResult, payload)


class ValidatingParserBackendCompatibilityTest(unittest.TestCase):
    class _FakeConverter:
        def __init__(self, sentinel: object) -> None:
            self._sentinel = sentinel

        def structure(self, json_doc: dict[str, object], model_class: object) -> object:
            return self._sentinel

        def dumps(self, model_instance: object, indent: int = 2) -> str:
            del model_instance
            del indent
            return '{"backend": "fake"}'

    def test_injected_converter_is_used_for_parse_and_dumps(self) -> None:
        sentinel = object()
        parser = json_parsing.ValidatingParser(converter=self._FakeConverter(sentinel))
        parsed = parser.parse_and_validate(contract.CanonicalToolCall, {})
        self.assertIs(parsed, sentinel)
        dumped = parser.dumps(sentinel)
        self.assertEqual(dumped, '{"backend": "fake"}')


if __name__ == "__main__":
    argv = [sys.argv[0]]
    if "--" in sys.argv:
        argv += sys.argv[sys.argv.index("--") + 1:]
    unittest.main(argv=argv)
