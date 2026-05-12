"""Tests for Cisco config auditor."""

from __future__ import annotations

from salt_cisco_mcp.validate.cisco_audit import AuditResult, audit_config

_IOS_VALID = """\
hostname router1
!
interface GigabitEthernet0/0
 description WAN Link
 ip address 10.0.0.1 255.255.255.0
 no shutdown
!
ip ssh version 2
service password-encryption
!
ntp server 1.1.1.1
"""

_IOS_NO_HOSTNAME = """\
interface GigabitEthernet0/0
 description WAN
 ip address 10.0.0.1 255.255.255.0
"""

_IOS_TELNET_ENABLED = """\
hostname router1
!
line vty 0 4
 transport input telnet
"""

_NXOS_VALID = """\
hostname switch1
!
interface Ethernet1/1
  description Server Port
  switchport
  switchport mode access
  no shutdown
"""


def test_audit_returns_result() -> None:
    result = audit_config(_IOS_VALID, "ios")
    assert isinstance(result, AuditResult)


def test_audit_ios_valid_passes() -> None:
    result = audit_config(_IOS_VALID, "ios")
    assert result.passed is True or len(result.findings) == 0


def test_audit_ios_no_hostname_finding() -> None:
    result = audit_config(_IOS_NO_HOSTNAME, "ios")
    finding_text = " ".join(f["message"] for f in result.findings).lower()
    assert "hostname" in finding_text


def test_audit_ios_telnet_finding() -> None:
    result = audit_config(_IOS_TELNET_ENABLED, "ios")
    finding_text = " ".join(f["message"] for f in result.findings).lower()
    assert "telnet" in finding_text or "ssh" in finding_text


def test_audit_result_has_passed_field() -> None:
    result = audit_config(_IOS_VALID, "ios")
    assert hasattr(result, "passed")


def test_audit_result_has_findings_list() -> None:
    result = audit_config(_IOS_VALID, "ios")
    assert isinstance(result.findings, list)


def test_audit_result_has_vendor_field() -> None:
    result = audit_config(_IOS_VALID, "ios")
    assert result.vendor == "ios"


def test_audit_nxos_valid() -> None:
    result = audit_config(_NXOS_VALID, "nxos")
    assert isinstance(result, AuditResult)


def test_audit_findings_have_message_field() -> None:
    result = audit_config(_IOS_NO_HOSTNAME, "ios")
    for finding in result.findings:
        assert "message" in finding


def test_audit_findings_have_severity_field() -> None:
    result = audit_config(_IOS_NO_HOSTNAME, "ios")
    for finding in result.findings:
        assert "severity" in finding


def test_audit_unknown_vendor_returns_result() -> None:
    result = audit_config(_IOS_VALID, "unknown_vendor")
    assert isinstance(result, AuditResult)


def test_audit_result_is_serializable() -> None:
    result = audit_config(_IOS_VALID, "ios")
    d = result.to_dict()
    assert isinstance(d, dict)
    assert "passed" in d
    assert "findings" in d
    assert "vendor" in d


def test_audit_empty_config_has_findings() -> None:
    result = audit_config("", "ios")
    # Empty config should generate at least one finding (no hostname)
    assert len(result.findings) > 0
