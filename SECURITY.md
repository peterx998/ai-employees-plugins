# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public issue.

Instead, report it privately to the repository maintainers. We take security seriously and will respond as quickly as possible.

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest (main branch) | ✅ |

## Security Considerations

This project contains plugin configurations (markdown, JSON, YAML schemas) and supporting Python/shell scripts for local quality gates and CI. Security risks include:

- Malicious MCP server URLs in `.mcp.json` files — review before connecting
- Prompt injection in SKILL.md files — validate contributed content

Always review third-party plugin contributions before installing.
