# Contributing to AI Employees Plugins

Thanks for your interest in contributing!

## How to Contribute

1. **Fork** the repository
2. **Create a branch** for your changes
3. **Make your changes** — plugins are just markdown and JSON files
4. **Submit a PR** with a clear description

## Plugin Structure

Each plugin follows the [knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) standard:

```
{plugin}/
├── .claude-plugin/plugin.json
├── .mcp.json
├── CONNECTORS.md
├── commands/
└── skills/
```

## SKILL.md Format

```yaml
---
name: skill-name
description: Use when <trigger>. <what it does>.
user_invocable: true
version: "1.0.0"
tags: [category, subcategory]
---

# Skill Title

Content here...
```

## Adding a New Plugin

1. Copy the structure from an existing plugin
2. Update `.claude-plugin/plugin.json` with your plugin name and description
3. Add your skills under `skills/` and commands under `commands/`
4. Update `marketplace.json` with the new plugin entry
5. Test with Hermes: `bash install-hermes.sh` then `/skill <name>`
6. Test with Codex: `bash install-codex.sh`

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
