"""Subprocess wrapper for salt-call and salt-key commands."""

from __future__ import annotations

import json
import subprocess
from typing import Any

import yaml


class AdapterError(Exception):
    """Raised when a salt-call/salt-key invocation fails."""


class SaltCallTimeoutError(AdapterError):
    """Raised when the subprocess exceeds the configured timeout."""


class ParseError(AdapterError):
    """Raised when output cannot be parsed as JSON or YAML."""


class SaltCallAdapter:
    """Thin subprocess wrapper for salt-call --local and salt-key --list-all."""

    def __init__(
        self,
        salt_call_cmd: list[str] | None = None,
        salt_key_cmd: list[str] | None = None,
        timeout: int = 30,
    ) -> None:
        self._salt_call: list[str] = salt_call_cmd or ["salt-call"]
        self._salt_key: list[str] = salt_key_cmd or ["salt-key"]
        self._timeout = timeout

    def call(self, func: str, *args: str) -> Any:
        """Run ``salt-call --local --out=json <func> [args]`` and return parsed output."""
        cmd = [*self._salt_call, "--local", "--out=json", func, *args]
        return self._run(cmd)

    def key_list(self) -> dict[str, list[str]]:
        """Run ``salt-key --list-all --out=json`` and return parsed output."""
        cmd = [*self._salt_key, "--list-all", "--out=json"]
        result: dict[str, list[str]] = self._run(cmd)
        return result

    def _run(self, cmd: list[str]) -> Any:
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise SaltCallTimeoutError(
                f"Command timed out after {self._timeout}s: {cmd[0]}"
            ) from exc

        if proc.returncode != 0:
            raise AdapterError(
                f"Command exited with code {proc.returncode}: {proc.stderr.strip()}"
            )

        return self._parse(proc.stdout)

    def _parse(self, output: str) -> Any:
        """Try JSON first, fall back to YAML."""
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            pass
        try:
            return yaml.safe_load(output)
        except Exception as exc:
            raise ParseError("Could not parse output as JSON or YAML") from exc
