# pip-audit-html

Convert `pip-audit` JSON output into a standalone, readable HTML report.

## Why this package

- Easy CLI for local use and CI pipelines
- No runtime dependencies
- Generates a single HTML file you can archive or share

## Installation

From PyPI (after publish):

```bash
pip install pip-audit-html
```

From source during development:

```bash
pip install -e .[dev]
```

## CLI usage

Generate a report from file:

```bash
pip-audit-html pip-audit-report.json -o reports/security-report.html
```

Pipe input from stdin:

```bash
pip-audit --format json | pip-audit-html - -o reports/security-report.html
```

Set custom title and fail build if vulnerabilities exist:

```bash
pip-audit-html pip-audit-report.json -o report.html --title "Weekly Dependency Security" --fail-on-vulns
```

Default footer attribution is included in generated reports. You can override it if needed:

```bash
pip-audit-html pip-audit-report.json -o report.html --author-name "Your Name" --author-url "https://www.linkedin.com/in/your-profile/"
```

Hide specific vulnerabilities (IDs/CVEs) from rendered HTML output:

```bash
pip-audit-html pip-audit-report.json -o report.html --ignore-vuln PYSEC-2024-10 --ignore-vuln CVE-2024-12345
```

You can also pass comma-separated values:

```bash
pip-audit-html pip-audit-report.json -o report.html --ignore-vuln "PYSEC-2024-10,CVE-2024-12345"
```

You can also run it as a module:

```bash
python -m pip_audit_html pip-audit-report.json -o report.html
```

## MCP Server (AI Assistant Integration)

`pip-audit-html` ships an optional **MCP (Model Context Protocol) server** that exposes audit and report generation as local tools for AI assistants such as Claude Desktop, VS Code Copilot, and Cursor.

Everything runs **locally over stdio** — no cloud, no ports, no API keys.

### Install with MCP support

```bash
pip install "pip-audit-html[mcp]"
```

### MCP tools exposed

| Tool | Description |
|---|---|
| `run_audit` | Run pip-audit on the current or a target environment, returns JSON |
| `generate_report` | Convert pip-audit JSON into a standalone HTML file |
| `get_vulnerabilities` | Return a structured list of all vulnerability findings |
| `get_summary` | Return counts: total, vulnerable, safe, skipped |
| `audit_and_report` | Run audit and generate HTML report in one step |

All tools accept an optional `ignore_vulns` parameter (comma-separated IDs/CVEs).

### Configure Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pip-audit-html": {
      "command": "pip-audit-html-mcp"
    }
  }
}
```

Claude Desktop config is usually at:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS / Linux**: `~/.config/claude/claude_desktop_config.json`

### Run the MCP server manually

```bash
pip-audit-html-mcp
```

### Example AI prompts once connected

- *"Audit my Python environment and show me what's vulnerable."*
- *"Generate an HTML security report for my project at C:/myproject."*
- *"Summarize the vulnerabilities in this pip-audit JSON file."*
- *"Audit my environment and ignore CVE-2024-1234, then save the report to report.html."*

## Local development

Use existing helper scripts:

1. Create environment (`001_env.bat` or `001_env.sh`)
2. Activate environment (`002_activate.bat` or `002_activate.sh`)
3. Install package/dev deps (`003_setup.bat` or `003_setup.sh`)
4. Run CLI help (`004_run.bat` or `004_run.sh`)
5. Run tests (`005_run_test.bat` or `005_run_test.sh`)

## Publish to PyPI

1. Update `version` in `pyproject.toml`.
2. Build distributions:

```bash
python -m pip install --upgrade build twine
python -m build
```

3. Validate artifacts:

```bash
python -m twine check dist/*
```

4. Upload:

```bash
python -m twine upload dist/*
```


