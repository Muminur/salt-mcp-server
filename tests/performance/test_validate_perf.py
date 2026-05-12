"""Performance gate: validate_state under 100 ms for 1 KB SLS."""
from __future__ import annotations

import time

from salt_cisco_mcp.tools.validate_state import validate_state_logic

_SLS_1KB = """\
# 1 KB IOS interface configuration state
configure_interface_lo0:
  network.managed:
    - name: Loopback0
    - ip_address: 10.0.0.1
    - subnet_mask: 255.255.255.255
    - description: "Management loopback"
    - enabled: true

configure_interface_gi0:
  network.managed:
    - name: GigabitEthernet0/0
    - ip_address: 192.168.1.1
    - subnet_mask: 255.255.255.0
    - description: "Uplink to core"
    - enabled: true
    - mtu: 1500

configure_interface_gi1:
  network.managed:
    - name: GigabitEthernet0/1
    - ip_address: 10.10.10.1
    - subnet_mask: 255.255.255.252
    - description: "P2P link to distribution"
    - enabled: true
    - mtu: 1500

ntp_server_primary:
  ntp.managed:
    - servers:
      - 10.0.0.254
      - 10.0.0.253

enable_ospf:
  router.ospf:
    - router_id: 10.0.0.1
    - networks:
      - 10.0.0.0/24
      - 192.168.1.0/24
"""


def test_validate_state_under_100ms() -> None:
    """Single validate_state call must complete in under 100 ms."""
    t0 = time.perf_counter()
    result = validate_state_logic(_SLS_1KB)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    assert "valid" in result or "errors" in result
    assert elapsed_ms < 100.0, f"validate_state took {elapsed_ms:.1f} ms (gate: 100 ms)"


def test_validate_state_benchmark(benchmark: object) -> None:
    """pytest-benchmark baseline for validate_state regression tracking."""
    result = benchmark(validate_state_logic, _SLS_1KB)  # type: ignore[call-arg,operator]
    assert "valid" in result or "errors" in result


def test_validate_state_100_calls_under_1s() -> None:
    """100 sequential validate_state calls must complete in under 1 s."""
    t0 = time.perf_counter()
    for _ in range(100):
        validate_state_logic(_SLS_1KB)
    elapsed_s = time.perf_counter() - t0
    assert elapsed_s < 1.0, f"100 validate_state calls took {elapsed_s:.2f} s (gate: 1 s)"
