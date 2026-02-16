# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import dataclasses
import importlib
import json
import types
from enum import Enum
from typing import Any, Type, TypeVar, Union, cast, get_args, get_origin, get_type_hints

APIModel = TypeVar("APIModel")


class ValidatingParser:
    def __init__(self, converter: Any | None = None) -> None:
        self._converter = converter if converter is not None else _make_default_converter()

    def parse_and_validate(
        self,
        model_class: Type[APIModel],
        json_payload: bytes | str | dict[str, Any],
    ) -> APIModel:
        if isinstance(json_payload, dict):
            json_doc = json_payload
        else:
            json_doc = json.loads(json_payload)
        if self._converter is not None:
            return cast(APIModel, self._converter.structure(json_doc, model_class))
        return _structure_dataclass(model_class, json_doc)

    def dumps(self, model_instance: Any) -> str:
        if self._converter is not None:
            return cast(str, self._converter.dumps(model_instance, indent=2))
        assert dataclasses.is_dataclass(model_instance), f"{model_instance} is not a dataclass"
        return json.dumps(dataclasses.asdict(cast(Any, model_instance)), indent=2)


def _make_default_converter() -> Any | None:
    try:
        cattrs_preconf_json = importlib.import_module("cattrs.preconf.json")
    except ImportError:
        return None
    return cattrs_preconf_json.make_converter()


def _structure_dataclass(model_class: Type[Any], payload: dict[str, Any]) -> Any:
    if not isinstance(payload, dict):
        raise TypeError("Expected object payload")

    field_types = get_type_hints(model_class)
    kwargs: dict[str, Any] = {}

    for field in dataclasses.fields(model_class):
        field_name = field.name
        if field_name not in payload:
            has_default = field.default is not dataclasses.MISSING or field.default_factory is not dataclasses.MISSING
            if not has_default:
                raise KeyError(f"Missing required field: {field_name}")
            continue

        field_type = field_types.get(field_name, Any)
        kwargs[field_name] = _structure_value(payload[field_name], field_type)

    return model_class(**kwargs)


def _structure_value(value: Any, expected_type: Any) -> Any:
    if expected_type is Any:
        return value

    origin = get_origin(expected_type)
    if origin in (Union, types.UnionType):
        for member_type in get_args(expected_type):
            if member_type is type(None) and value is None:
                return None
            if member_type is type(None):
                continue
            try:
                return _structure_value(value, member_type)
            except (TypeError, ValueError, KeyError):
                continue
        raise TypeError(f"Cannot structure value {value!r} as {expected_type}")

    if isinstance(expected_type, type) and issubclass(expected_type, Enum):
        return expected_type(value)

    if isinstance(expected_type, type) and dataclasses.is_dataclass(expected_type):
        return _structure_dataclass(expected_type, value)

    if origin is list:
        if not isinstance(value, list):
            raise TypeError("Expected list")
        args = get_args(expected_type)
        if not args:
            return value
        item_type = args[0]
        return [_structure_value(item, item_type) for item in value]

    if origin is dict:
        if not isinstance(value, dict):
            raise TypeError("Expected object")
        args = get_args(expected_type)
        if len(args) < 2:
            return value
        key_type, value_type = args[0], args[1]
        return {
            _structure_value(key, key_type): _structure_value(item, value_type)
            for key, item in value.items()
        }

    if expected_type is float and isinstance(value, int):
        return float(value)

    if isinstance(expected_type, type) and not isinstance(value, expected_type):
        raise TypeError(f"Expected {expected_type.__name__}")

    return value
