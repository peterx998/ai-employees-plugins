# AI Employees — Agent Instructions

You are working inside the **ai-employees-plugins** pack — an enterprise AI employee implementation system built on the knowledge-work-plugins architecture, adapted for **Hermes Agent** and **Codex CLI**.

## Plugin Structure (per knowledge-work-plugins standard)
Each plugin contains: `.claude-plugin/plugin.json`, `.mcp.json`, `CONNECTORS.md`, `commands/`, `skills/`.

## SKILL.md Format (Hermes + Codex compatible)
```yaml
---
name: skill-name
description: Use when <trigger>.
user_invocable: true
version: "1.0.0"
---
```

## Working Here
- SKILL.md files must have `user_invocable: true` for Codex compatibility
- Keep descriptions under 1024 characters (Hermes limit)
- Use `~~placeholder` syntax for tool-agnostic connector references
