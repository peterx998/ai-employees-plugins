#!/usr/bin/env python3
"""
validate-contracts.py — Deep contract validator for plugin consistency.

Validates cross-references between:
  - SKILL.md → command output_schema → actual JSON Schema files
  - Schema required fields → SKILL.md examples coverage
  - .mcp.json → no placeholders
  - programs/ → listed files exist
  - .claude-plugin/plugin.json → commands exist

Usage:
  python install/validate-contracts.py [--plugin <name>] [--all]
  python install/validate-contracts.py --plugin customer-support

Exit codes:
  0 — All contracts valid
  1 — Warnings found
  2 — Errors found
"""

import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. pip install pyyaml", file=sys.stderr)
    sys.exit(2)


REPO = Path(__file__).parent.parent


def find_plugins():
    """Find all plugin directories (those with .claude-plugin/plugin.json)."""
    plugins = []
    for d in REPO.iterdir():
        if d.is_dir() and (d / ".claude-plugin" / "plugin.json").exists():
            plugins.append(d.name)
    return plugins


def validate_mcp_json(plugin_dir):
    """Validate .mcp.json has no placeholders."""
    errors = []
    warnings = []
    mcp_path = plugin_dir / ".mcp.json"

    if not mcp_path.exists():
        return errors, warnings

    try:
        with open(mcp_path) as f:
            mcp_data = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f".mcp.json: Invalid JSON: {e}")
        return errors, warnings

    servers = mcp_data.get("mcpServers", {})
    placeholder_patterns = [
        r"your-store", r"your-account", r"your-api-key",
        r"YOUR_", r"replace-me", r"example\.com",
    ]

    for server_name, config in servers.items():
        url = config.get("url", "")

        # Check for placeholder URLs
        for pattern in placeholder_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                errors.append(
                    f".mcp.json → {server_name}: URL contains placeholder '{pattern}' "
                    f"→ use env vars or .mcp.local.json instead"
                )

        # Warn if plain URL without auth
        if not config.get("auth") and url.startswith("https://"):
            warnings.append(
                f".mcp.json → {server_name}: No auth config — "
                f"credentials should be in .mcp.local.json or env vars"
            )

    return errors, warnings


def validate_skill_contracts(plugin_dir):
    """Validate SKILL.md contracts against schema files and command files."""
    errors = []
    warnings = []

    skills_dir = plugin_dir / "skills"
    if not skills_dir.exists():
        return errors, warnings

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue

        skill_path = skill_dir / "SKILL.md"
        if not skill_path.exists():
            warnings.append(f"skills/{skill_dir.name}: No SKILL.md")
            continue

        try:
            with open(skill_path, encoding="utf-8") as f:
                skill_content = f.read()
        except Exception:
            errors.append(f"skills/{skill_dir.name}/SKILL.md: Cannot read")
            continue

        # Check frontmatter
        if not skill_content.startswith("---"):
            errors.append(f"skills/{skill_dir.name}/SKILL.md: Missing YAML frontmatter")
            continue

        # Parse frontmatter
        end = skill_content.find("---", 3)
        if end < 0:
            errors.append(f"skills/{skill_dir.name}/SKILL.md: Malformed frontmatter")
            continue

        frontmatter = skill_content[3:end].strip()

        # Check for user_invocable
        if "user_invocable: true" not in frontmatter:
            errors.append(f"skills/{skill_dir.name}/SKILL.md: Missing 'user_invocable: true'")

        # Check output_schema references point to real files
        schema_refs = re.findall(r'output_schema:\s*["\']?([^"\'\n]+)["\']?', frontmatter)
        for ref in schema_refs:
            ref = ref.strip()
            if ref and not ref.startswith("http"):
                # Check if referenced schema exists
                schema_path = REPO / ref
                if not schema_path.exists():
                    schema_path = REPO / "schemas" / plugin_dir.name / ref
                    if not schema_path.exists():
                        errors.append(
                            f"skills/{skill_dir.name}/SKILL.md: "
                            f"output_schema '{ref}' — file not found"
                        )

        # Check that required schema fields appear in SKILL.md examples
        for ref in schema_refs:
            ref = ref.strip()
            if ref:
                schema_path = REPO / ref
                if not schema_path.exists():
                    schema_path = REPO / "schemas" / plugin_dir.name / ref
                if schema_path.exists():
                    try:
                        with open(schema_path) as sf:
                            schema = json.load(sf)
                        required_fields = set(schema.get("required", []))
                        # Check if SKILL.md mentions these fields
                        for field in required_fields:
                            if field not in skill_content:
                                warnings.append(
                                    f"skills/{skill_dir.name}/SKILL.md: "
                                    f"Schema required field '{field}' not mentioned in SKILL.md"
                                )
                    except (json.JSONDecodeError, OSError):
                        pass

    return errors, warnings


def validate_commands(plugin_dir):
    """Validate command files exist and are properly namespaced."""
    errors = []
    warnings = []

    # Check plugin.json commands
    plugin_json_path = plugin_dir / ".claude-plugin" / "plugin.json"
    if plugin_json_path.exists():
        try:
            with open(plugin_json_path) as f:
                plugin_data = json.load(f)
            commands = plugin_data.get("commands", [])
            for cmd_path in commands:
                full_path = plugin_dir / cmd_path
                if not full_path.exists():
                    errors.append(
                        f".claude-plugin/plugin.json: command '{cmd_path}' file not found"
                    )
        except (json.JSONDecodeError, OSError) as e:
            errors.append(f".claude-plugin/plugin.json: Cannot parse: {e}")

    # Check commands directory
    commands_dir = plugin_dir / "commands"
    if commands_dir.exists():
        for cmd_file in commands_dir.glob("*.md"):
            try:
                with open(cmd_file, encoding="utf-8") as f:
                    content = f.read()
                # Check namespace
                name_match = re.search(r'^name:\s*(.+)$', content, re.MULTILINE)
                if name_match:
                    cmd_name = name_match.group(1).strip()
                    if ":" not in cmd_name:
                        errors.append(
                            f"commands/{cmd_file.name}: "
                            f"Command '{cmd_name}' missing namespace prefix (e.g., 'plugin:command')"
                        )
            except Exception:
                pass

    return errors, warnings


def validate_programs(plugin_dir):
    """Validate programs/ references point to real files."""
    errors = []
    warnings = []

    programs_dir = REPO / "programs"
    if not programs_dir.exists():
        return errors, warnings

    plugin_name = plugin_dir.name
    program_files = [
        f"{plugin_name}-autoresearch.md",
    ]

    for prog_file in program_files:
        prog_path = programs_dir / prog_file
        if not prog_path.exists():
            continue  # Optional

        try:
            with open(prog_path, encoding="utf-8") as f:
                content = f.read()

            # Check for file references
            file_refs = re.findall(r'`([a-z_/.-]+\.[a-z]{2,4})`', content)
            for ref in file_refs:
                full_path = REPO / ref
                if not full_path.exists():
                    # Try relative to plugin
                    full_path = plugin_dir / ref
                    if not full_path.exists():
                        warnings.append(
                            f"programs/{prog_file}: Referenced file '{ref}' not found"
                        )
        except Exception:
            pass

    return errors, warnings


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Deep contract validator for plugins")
    parser.add_argument("--plugin", help="Validate a specific plugin")
    parser.add_argument("--all", action="store_true", help="Validate all plugins")
    args = parser.parse_args()

    plugins = []
    if args.plugin:
        plugins = [args.plugin]
    elif args.all:
        plugins = find_plugins()
    else:
        # Default: validate customer-support and agent-evaluation
        plugins = ["customer-support", "agent-evaluation"]

    total_errors = 0
    total_warnings = 0

    for plugin_name in plugins:
        plugin_dir = REPO / plugin_name
        if not plugin_dir.exists():
            print(f"⚠ Plugin not found: {plugin_name}")
            continue

        print(f"\n{'='*60}")
        print(f"  Validating: {plugin_name}")
        print(f"{'='*60}")

        # Run all validators
        checks = [
            ("MCP Config", validate_mcp_json(plugin_dir)),
            ("Skill Contracts", validate_skill_contracts(plugin_dir)),
            ("Commands", validate_commands(plugin_dir)),
            ("Programs", validate_programs(plugin_dir)),
        ]

        for check_name, (errors, warnings) in checks:
            for e in errors:
                print(f"  ❌ [{check_name}] {e}")
            for w in warnings:
                print(f"  ⚠  [{check_name}] {w}")

            if not errors and not warnings:
                print(f"  ✅ [{check_name}] OK")

            total_errors += len(errors)
            total_warnings += len(warnings)

    print(f"\n{'='*60}")
    print(f"  Total: {total_errors} errors, {total_warnings} warnings")
    if total_errors == 0:
        print(f"  ✅ All contracts valid")
    else:
        print(f"  ❌ {total_errors} contract violation(s) found")
    print(f"{'='*60}")

    sys.exit(2 if total_errors > 0 else (1 if total_warnings > 0 else 0))


if __name__ == "__main__":
    main()
