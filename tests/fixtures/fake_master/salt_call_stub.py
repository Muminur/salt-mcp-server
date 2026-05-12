#!/usr/bin/env python3
"""
Fake salt-call/salt-key stub for integration testing.

Usage:
  python salt_call_stub.py [--local] [--out=json] <function> [args...]
  python salt_call_stub.py --list-all [--out=json]        # salt-key mode
  python salt_call_stub.py --timeout-test                  # sleeps to trigger timeout
"""

import json
import sys
import time

_GRAINS = {
    "id": "salt-master",
    "os": "Ubuntu",
    "osrelease": "22.04",
    "kernel": "Linux",
    "saltversion": "3007.0",
    "cpuarch": "x86_64",
}

_PILLAR = {
    "proxy": {
        "proxytype": "napalm",
        "driver": "ios",
        "host": "192.168.1.1",
        "username": "admin",
        "password": "TOP_SECRET_PASSWORD",
        "enable_password": "ENABLE_SECRET",
    },
    "snmp": {
        "community": "public_community_string",
        "token": "auth_token_12345",
    },
    "description": "edge router",
}

_SYS_FUNCTIONS = [
    "config.get",
    "grains.get",
    "grains.items",
    "ntp.set_servers",
    "ntp.show_ntp_info",
    "pillar.get",
    "pillar.items",
    "state.apply",
    "state.highstate",
    "state.show_sls",
    "state.sls",
    "sys.argspec",
    "sys.doc",
    "sys.list_functions",
    "test.echo",
    "test.ping",
]

_ARGSPEC = {
    "ntp.set_servers": {
        "func": "ntp.set_servers",
        "args": ["servers"],
        "defaults": None,
        "kwargs": False,
        "doc": "Configure NTP servers.",
    }
}

args = sys.argv[1:]

# Timeout test hook
if "--timeout-test" in args:
    time.sleep(60)
    sys.exit(0)

# Salt-key mode: --list-all
if "--list-all" in args:
    data = {
        "minions": ["router1.example.com", "router2.example.com", "switch1.example.com"],
        "minions_pre": ["pending-device.example.com"],
        "minions_rejected": [],
    }
    print(json.dumps(data))
    sys.exit(0)

# Extract the function name (skip flags)
func = None
func_args: list[str] = []
skip_next = False
for i, arg in enumerate(args):
    if skip_next:
        skip_next = False
        continue
    if arg.startswith("-"):
        if arg in ("--out", "--config-dir"):
            skip_next = True
        continue
    if func is None:
        func = arg
    else:
        func_args.append(arg)

if func is None:
    print(json.dumps({"local": None}))
    sys.exit(0)

# Simulate error for unknown functions with "error." prefix
if func.startswith("error."):
    print("ERROR: function not found", file=sys.stderr)
    sys.exit(1)

# Dispatch
if func == "grains.items":
    print(json.dumps({"local": _GRAINS}))
elif func == "grains.get":
    key = func_args[0] if func_args else ""
    print(json.dumps({"local": _GRAINS.get(key, None)}))
elif func == "pillar.items":
    print(json.dumps({"local": _PILLAR}))
elif func == "sys.list_functions":
    print(json.dumps({"local": _SYS_FUNCTIONS}))
elif func == "sys.argspec":
    name = func_args[0] if func_args else ""
    print(json.dumps({"local": _ARGSPEC.get(name, {})}))
elif func == "test.ping":
    print(json.dumps({"local": True}))
else:
    print(json.dumps({"local": None}))
