"""Cisco config auditor — regex-based with optional ciscoconfparse2 enhancement."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_SEVERITY_HIGH = "high"
_SEVERITY_MEDIUM = "medium"
_SEVERITY_LOW = "low"


@dataclass
class AuditResult:
    vendor: str
    passed: bool
    findings: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "vendor": self.vendor,
            "passed": self.passed,
            "findings": self.findings,
        }


def _finding(message: str, severity: str = _SEVERITY_MEDIUM) -> dict[str, str]:
    return {"message": message, "severity": severity}


def _audit_ios(config: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if not re.search(r"^hostname\s+\S+", config, re.MULTILINE):
        findings.append(_finding("No hostname configured", _SEVERITY_HIGH))

    if re.search(r"transport input telnet", config, re.IGNORECASE):
        findings.append(_finding("Telnet enabled on VTY lines — use SSH only", _SEVERITY_HIGH))

    if not re.search(r"ip ssh version 2", config, re.IGNORECASE):
        findings.append(_finding("SSH version 2 not explicitly configured", _SEVERITY_MEDIUM))

    if re.search(r"^enable password\s", config, re.MULTILINE):
        findings.append(
            _finding("Plaintext enable password found — use 'enable secret'", _SEVERITY_HIGH)
        )

    if not re.search(r"service password-encryption", config, re.IGNORECASE):
        findings.append(_finding("service password-encryption not enabled", _SEVERITY_LOW))

    return findings


def _audit_nxos(config: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if not re.search(r"^hostname\s+\S+", config, re.MULTILINE):
        findings.append(_finding("No hostname configured", _SEVERITY_HIGH))

    if re.search(r"feature telnet", config, re.IGNORECASE):
        findings.append(_finding("Telnet feature enabled — disable and use SSH", _SEVERITY_HIGH))

    return findings


def audit_config(config: str, vendor: str) -> AuditResult:
    """Run audit rules for *vendor* against *config* text."""
    if vendor in ("ios", "iosxr"):
        findings = _audit_ios(config)
    elif vendor in ("nxos", "nxos_api"):
        findings = _audit_nxos(config)
    else:
        findings = [_finding(f"No audit rules defined for vendor '{vendor}'", _SEVERITY_LOW)]

    return AuditResult(
        vendor=vendor,
        passed=len(findings) == 0,
        findings=findings,
    )
