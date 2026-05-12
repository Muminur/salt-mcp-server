"""JSON Schema validation for Salt proxy pillar structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import jsonschema

SUPPORTED_PROXYTYPES = ("napalm", "nxos", "nxos_api", "cisconso")

_DOC_BASE = "https://docs.saltproject.io/en/3007/ref/proxy"

_PROXY_SCHEMAS: dict[str, dict[str, Any]] = {
    "napalm": {
        "type": "object",
        "required": ["proxytype", "driver", "host", "username", "password"],
        "properties": {
            "proxytype": {"type": "string", "const": "napalm"},
            "driver": {"type": "string", "minLength": 1},
            "host": {"type": "string", "minLength": 1},
            "username": {"type": "string", "minLength": 1},
            "password": {"type": "string"},
            "port": {"type": "integer"},
            "optional_args": {"type": "object"},
        },
        "additionalProperties": True,
        "_anchor": f"{_DOC_BASE}/all/salt.proxy.napalm.html",
    },
    "nxos": {
        "type": "object",
        "required": ["proxytype", "host", "username", "password"],
        "properties": {
            "proxytype": {"type": "string", "const": "nxos"},
            "host": {"type": "string", "minLength": 1},
            "username": {"type": "string", "minLength": 1},
            "password": {"type": "string"},
        },
        "additionalProperties": True,
        "_anchor": f"{_DOC_BASE}/all/salt.proxy.nxos.html",
    },
    "nxos_api": {
        "type": "object",
        "required": ["proxytype", "host", "username", "password"],
        "properties": {
            "proxytype": {"type": "string", "const": "nxos_api"},
            "host": {"type": "string", "minLength": 1},
            "username": {"type": "string", "minLength": 1},
            "password": {"type": "string"},
        },
        "additionalProperties": True,
        "_anchor": f"{_DOC_BASE}/all/salt.proxy.nxos_api.html",
    },
    "cisconso": {
        "type": "object",
        "required": ["proxytype", "host", "username", "password"],
        "properties": {
            "proxytype": {"type": "string", "const": "cisconso"},
            "host": {"type": "string", "minLength": 1},
            "username": {"type": "string", "minLength": 1},
            "password": {"type": "string"},
        },
        "additionalProperties": True,
        "_anchor": f"{_DOC_BASE}/all/salt.proxy.cisconso.html",
    },
}


@dataclass
class ValidationResult:
    valid: bool
    errors: list[dict[str, str]] = field(default_factory=list)


def validate_pillar_dict(pillar: dict[str, Any]) -> ValidationResult:
    """Validate a pillar dict against the appropriate proxy schema."""
    if "proxy" not in pillar:
        return ValidationResult(
            valid=False,
            errors=[{"message": "Missing required top-level key 'proxy'", "anchor_url": ""}],
        )

    proxy = pillar["proxy"]
    proxytype = proxy.get("proxytype", "")

    if proxytype not in SUPPORTED_PROXYTYPES:
        supported = ", ".join(SUPPORTED_PROXYTYPES)
        return ValidationResult(
            valid=False,
            errors=[
                {
                    "message": (
                        f"Unknown proxytype '{proxytype}'. "
                        f"Supported: {supported}"
                    ),
                    "anchor_url": "",
                }
            ],
        )

    schema = dict(_PROXY_SCHEMAS[proxytype])
    anchor = schema.pop("_anchor", "")

    validator = jsonschema.Draft7Validator(schema)
    errors = []
    for err in sorted(validator.iter_errors(proxy), key=lambda e: list(e.path)):
        errors.append(
            {
                "message": err.message,
                "anchor_url": anchor,
            }
        )

    return ValidationResult(valid=len(errors) == 0, errors=errors)
