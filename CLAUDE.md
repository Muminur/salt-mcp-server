# CLAUDE.md

This file provides guidance to Claude Code when working on this project. Read this file at the start of every session and follow these rules without exception.

## Core Workflow Rules

Claude Code **must** follow these four rules on every session:

1. **Read `PLANNING.md` at the start of every new conversation.**
   Before doing anything else, open `PLANNING.md` and load the project's vision, architecture, technology stack, and tooling into context. Do not skip this step, even for small tasks.

2. **Check `TASKS.md` before starting any work.**
   Identify which task you are about to work on. If the user's request does not map to an existing task, pause and confirm with the user before proceeding.

3. **Mark completed tasks in `TASKS.md` immediately.**
   The moment a task is finished, update `TASKS.md` to mark it as complete (e.g., change `- [ ]` to `- [x]`). Do not batch updates — mark each task the moment it is done.

4. **Add newly discovered tasks to `TASKS.md` when found.**
   If during work you identify new tasks, sub-tasks, bugs, refactors, or follow-ups, append them to `TASKS.md` under the appropriate milestone before continuing.

## Session Lifecycle

### At the start of a session
- Read `PLANNING.md` (full file).
- Read `TASKS.md` to see what is done, in progress, and pending.
- Read any prior **Session Summary** sections at the bottom of this file to understand recent context.
- Confirm which task you will work on next before writing code.

### During a session
- Keep `TASKS.md` continuously up to date — mark items complete as you go and add new items as they surface.
- Reference architectural decisions in `PLANNING.md` rather than reinventing them. If a decision needs to change, update `PLANNING.md` and note why.

### Before clearing history / ending a session
- Append a **Session Summary** entry to the bottom of this file (see template below) describing what was done, what changed, and what is still open. This is how context is preserved across cleared histories.

## Session Summary Template

When adding a session summary, use this format and append under the `## Session Summaries` heading:

```markdown
### Session — YYYY-MM-DD

**Worked on:** Brief description of tasks tackled.

**Completed:**
- Item 1
- Item 2

**Changed / decided:**
- Any architectural or design decisions, file moves, dependency changes, etc.

**Open / next up:**
- What is unfinished or what the next session should pick up.

**Notes:**
- Anything non-obvious a future session needs to know (gotchas, blockers, links).
```

## File Reference

- `PLANNING.md` — vision, architecture, technology stack, required tools.
- `TASKS.md` — milestones and tasks (the single source of truth for work status).
- `CLAUDE.md` — this file (workflow rules + session summaries).

## Session Summaries

<!-- Append new session summaries below this line, newest at the bottom. -->

### Session — 2026-05-12

**Worked on:** Milestone 0, Tasks 1 & 2 — repo skeleton with `pyproject.toml` and `salt_cisco_mcp/` package stub.

**Completed:**
- Task 1: `pyproject.toml` with hatchling>=1.27 build backend, `requires-python = ">=3.10,<3.13"`, entry point `salt-cisco-mcp = "salt_cisco_mcp.cli:main"`, explicit wheel packages declaration
- Task 2: `salt_cisco_mcp/__init__.py` exposing `__version__ = "0.1.0"`, `salt_cisco_mcp/cli.py` stub `def main() -> None: pass`
- `tests/test_package.py`: 4 tests (import, semver version, cli callable, metadata/module version parity)
- Minimal `.gitignore` (to be expanded in Task 9)
- `README.md` stub (to be expanded in Task 8)
- Git repo initialized, branch `milestone0/repo-skeleton`

**Changed / decided:**
- `hatchling>=1.27` pinned (PEP 639 SPDX `license` string requires this version)
- `[tool.hatch.build.targets.wheel] packages = ["salt_cisco_mcp"]` declared explicitly
- Version regex in tests is PEP 440-permissive (`\d+\.\d+\.\d+(?:[a-zA-Z0-9.+\-]+)?`) to allow pre-releases

**Open / next up:**
- Task 3: Pin core deps (`mcp>=1.2.0`, `pydantic>=2`, etc.) in `pyproject.toml`
- Task 4: Pin dev deps (`pytest`, `mypy`, `ruff`, etc.)
- Task 5: Configure `ruff` and `mypy --strict` in `pyproject.toml`
- No remote repository set up yet — PR creation deferred until GitHub remote is available

**Notes:**
- `CLAUDE.md`, `PLANNING.md`, `TASKS.md`, `PRD-salt-cisco-mcp.md` are intentionally NOT committed yet (Task 10 scope)
- `black` is not in the project stack; ruff handles both linting and formatting
- CI workflow (Task 7) not yet created, so `ci-guard` was not applicable this session
