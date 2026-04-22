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

`pip-audit-html` ships an optional **MCP (Model Context Protocol) server** that exposes audit and report generation as local tools. Everything runs **locally over stdio** — no cloud, no ports, no API keys.

### Available MCP tools

| Tool | Description |
|---|---|
| `run_audit` | Run pip-audit on the current or a target environment, returns JSON |
| `generate_report` | Convert pip-audit JSON into a standalone HTML file |
| `get_vulnerabilities` | Return a structured list of all vulnerability findings |
| `get_summary` | Return counts: total, vulnerable, safe, skipped |
| `audit_and_report` | Run audit and generate HTML report in one step |

All tools accept an optional `ignore_vulns` parameter (comma-separated IDs/CVEs).

---

### Option 1 — IDE / AI Assistant Integration (VS Code, Cursor, Claude Desktop)

Connect pip-audit-html as a local MCP server so your AI assistant can audit your Python environment and generate HTML reports on demand — no manual commands needed.

#### Step 1 — Install with MCP support

```bash
pip install "pip-audit-html[mcp]"
```

#### Step 2 — Configure your IDE or AI client

**VS Code (GitHub Copilot)**

Add to your VS Code `settings.json`:

```json
{
  "mcp": {
    "servers": {
      "pip-audit-html": {
        "type": "stdio",
        "command": "pip-audit-html-mcp"
      }
    }
  }
}
```

**Cursor**

Add to your Cursor MCP config (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "pip-audit-html": {
      "command": "pip-audit-html-mcp"
    }
  }
}
```

**Claude Desktop**

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

Claude Desktop config location:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS / Linux**: `~/.config/claude/claude_desktop_config.json`

#### Step 3 — Ask your AI assistant

Once configured, your AI can call the tools directly. Example prompts:

- *"Audit my Python environment and show me what's vulnerable."*
- *"Generate an HTML security report for my project at C:/myproject."*
- *"Summarize the vulnerabilities in audit.json."*
- *"Audit my environment, ignore CVE-2024-1234, and save the report to report.html."*

---

### Option 2 — Command Line (pip install + direct invocation)

Use the MCP tools directly from the command line without any IDE or AI client.

#### Step 1 — Install with MCP support

```bash
pip install "pip-audit-html[mcp]"
```

#### Step 2 — Run individual tools

Each tool accepts JSON input/output via the command line. Use the `mcp` CLI to call tools directly:

**Audit current environment:**

```bash
pip-audit-html-mcp
```

Or invoke tools via the `mcp` client:

```bash
# Audit the active environment and print JSON findings
python -c "
from pip_audit_html.server import run_audit, get_summary, generate_report
import json

# Step 1: run audit
audit_json = run_audit()

# Step 2: print summary
summary = json.loads(get_summary(audit_json))
print(f'Packages: {summary[\"total_dependencies\"]}  Vulnerable: {summary[\"total_vulnerabilities\"]}  Safe: {summary[\"total_safe\"]}')

# Step 3: generate report
path = generate_report(audit_json, output_path='audit_report.html')
print(f'Report saved to: {path}')
"
```

**One-step audit and report:**

```bash
python -c "
from pip_audit_html.server import audit_and_report
import json
result = json.loads(audit_and_report(output_path='audit_report.html'))
print(result)
"
```

**Audit a specific virtualenv or project path:**

```bash
python -c "
from pip_audit_html.server import audit_and_report
import json
result = json.loads(audit_and_report(target_path='C:/myproject', output_path='report.html'))
print(result)
"
```

**Ignore specific CVEs:**

```bash
python -c "
from pip_audit_html.server import audit_and_report
import json
result = json.loads(audit_and_report(ignore_vulns='CVE-2024-1234,PYSEC-2024-99', output_path='report.html'))
print(result)
"
```

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


