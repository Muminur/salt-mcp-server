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

_STATE_SHOW_SLS = {
    "deny_ssh_acl_|-deny-ssh-from-rfc1918_|-deny-ssh-from-rfc1918_|-managed": {
        "__id__": "deny-ssh-from-rfc1918",
        "__sls__": "cisco.acl.edge",
        "__run_num__": 0,
        "name": "deny-ssh-from-rfc1918",
        "state": "acl",
        "fun": "managed",
    }
}

_STATE_SLS_TEST = {
    "deny_ssh_acl_|-deny-ssh-from-rfc1918_|-deny-ssh-from-rfc1918_|-managed": {
        "name": "deny-ssh-from-rfc1918",
        "comment": "State would have been applied",
        "changes": {"new": "ACL entry deny SSH from 10.0.0.0/8 added"},
        "result": True,
        "duration": 12.5,
    }
}

_STATE_SLS_APPLY = {
    "deny_ssh_acl_|-deny-ssh-from-rfc1918_|-deny-ssh-from-rfc1918_|-managed": {
        "name": "deny-ssh-from-rfc1918",
        "comment": "Applied successfully",
        "changes": {"new": "ACL entry deny SSH from 10.0.0.0/8 added"},
        "result": True,
        "duration": 15.2,
    }
}

_NET_LOAD_CONFIG = {
    "result": True,
    "comment": "Merged successfully",
    "diff": "+hostname router1",
}

_NET_LOAD_REPLACE = {
    "result": True,
    "comment": "Replaced successfully",
    "diff": "+hostname router1\n-hostname old-router1",
}

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
elif func == "state.show_sls":
    print(json.dumps({"local": _STATE_SHOW_SLS}))
elif func == "state.sls":
    if "test=True" in func_args:
        print(json.dumps({"local": _STATE_SLS_TEST}))
    else:
        print(json.dumps({"local": _STATE_SLS_APPLY}))
elif func == "net.load_config":
    print(json.dumps({"local": _NET_LOAD_CONFIG}))
elif func == "net.load_replace_candidate":
    print(json.dumps({"local": _NET_LOAD_REPLACE}))
else:
    print(json.dumps({"local": None}))
