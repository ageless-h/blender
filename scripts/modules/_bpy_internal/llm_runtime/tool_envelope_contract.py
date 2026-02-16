# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NormalizedErrorClass(StrEnum):
    VALIDATION = "validation"
    PERMISSION = "permission"
    RUNTIME = "runtime"
    TIMEOUT = "timeout"
    PROVIDER = "provider"


@dataclass
class ToolExecutionPolicy:
    risk_level: RiskLevel
    requires_confirmation: bool
    timeout_ms: int


@dataclass
class CanonicalToolCall:
    provider: str
    call_id: str
    tool_name: str
    arguments: dict[str, Any]
    raw_request: dict[str, Any]
    raw_response: dict[str, Any]
    received_at: str
    trace_id: str
    session_id: str
    policy: ToolExecutionPolicy


@dataclass
class CanonicalToolResult:
    provider: str
    call_id: str
    tool_name: str
    ok: bool
    result: dict[str, Any] | list[Any] | str | int | float | bool | None
    error_class: NormalizedErrorClass | None
    error_message: str | None
    trace_id: str
    session_id: str
