# pip-audit-html

Convert `pip-audit` JSON output into a standalone, readable HTML report.

## Why this package

- Easy CLI for local use and CI pipelines
- No runtime dependencies
- Generates a single HTML file you can archive or share

## Installation

Python version support:

- Base CLI and HTML conversion: Python `3.8+`
- MCP server and MCP Python API: Python `3.10+`

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

Python requirement for MCP support:

- MCP depends on the upstream `mcp` SDK, which requires Python `3.10+`
- If you are on Python `3.8` or `3.9`, the base `pip-audit-html` CLI still works, but MCP features are not available

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

This option requires Python `3.10+`.

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

### Option 2 — Command Line (no IDE required)

Use `pip-audit-html` directly from the command line. No AI assistant or IDE needed — just install and run.

#### Install

```bash
pip install pip-audit-html
```

This base install supports Python `3.8+`.

To also use the MCP Python API (optional):

This optional MCP install requires Python `3.10+`.

```bash
pip install "pip-audit-html[mcp]"
```

---

#### "Audit my Python environment and show me what's vulnerable."

This runs `pip-audit` against the currently active Python environment, converts the output to HTML, and opens the report. `pip-audit` must be installed separately.

```bash
pip install pip-audit
```

**Windows:**
```cmd
pip-audit --format json -o audit.json
pip-audit-html audit.json -o report.html
start report.html
```

**macOS / Linux:**
```bash
pip-audit --format json -o audit.json
pip-audit-html audit.json -o report.html
open report.html        # macOS
xdg-open report.html   # Linux
```

Or pipe directly without saving the JSON file:

```bash
pip-audit --format json | pip-audit-html - -o report.html
```

> `pip-audit` exits with code 1 when vulnerabilities are found — this is expected. The JSON and HTML are still produced correctly.

---

#### "Generate an HTML security report for my project at C:/myproject."

Audit a specific project directory (instead of the global/active environment):

**Windows:**
```cmd
pip-audit --format json --path C:\myproject -o audit.json
pip-audit-html audit.json -o report.html --title "My Project Security Report"
start report.html
```

**macOS / Linux:**
```bash
pip-audit --format json --path /path/to/myproject -o audit.json
pip-audit-html audit.json -o report.html --title "My Project Security Report"
```

> `--path` tells pip-audit to audit a specific project or virtualenv directory rather than the currently active Python environment.

---

#### "Summarize the vulnerabilities in this pip-audit JSON file."

If you already have a `pip-audit` JSON file and just want a quick text summary:

```bash
python -c "
import json
from pip_audit_html.server import get_summary
summary = json.loads(get_summary(open('audit.json').read()))
print('Packages audited :', summary['total_dependencies'])
print('Vulnerable        :', summary['total_vulnerabilities'])
print('Safe              :', summary['total_safe'])
print('Skipped           :', summary['total_skipped'])
print('Clean             :', summary['is_clean'])
"
```

Example output:

```
Packages audited : 42
Vulnerable        : 3
Safe              : 38
Skipped           : 1
Clean             : False
```

To see the full list of individual vulnerability findings:

```bash
python -c "
import json
from pip_audit_html.server import get_vulnerabilities
findings = json.loads(get_vulnerabilities(open('audit.json').read()))
for f in findings:
    print(f['package'], f['version'], '->', f['vuln_id'], f['aliases'])
"
```

---

#### "Audit my environment and ignore CVE-2024-1234, then save the report to report.html."

Some vulnerabilities may not apply to your usage, or you may have accepted the risk. Use `--ignore-vuln` to exclude them from the report:

```bash
pip-audit --format json | pip-audit-html - -o report.html --ignore-vuln CVE-2024-1234
```

Ignore multiple IDs in one command (repeat the flag or use comma-separated values):

```bash
pip-audit --format json | pip-audit-html - -o report.html \
  --ignore-vuln CVE-2024-1234 \
  --ignore-vuln PYSEC-2024-99
```

```bash
pip-audit --format json | pip-audit-html - -o report.html \
  --ignore-vuln "CVE-2024-1234,PYSEC-2024-99"
```

> Ignored IDs are matched against both the primary vulnerability ID and any aliases (e.g. a PYSEC ID that aliases a CVE). Matching is case-insensitive.

Also make CI exit 0 when all remaining (non-ignored) vulns are suppressed:

```bash
pip-audit --format json | pip-audit-html - -o report.html \
  --ignore-vuln CVE-2024-1234 \
  --fail-on-vulns
```

> `--fail-on-vulns` exits with code 1 only if vulnerabilities remain **after** the ignore list is applied. If everything is ignored, the exit code is 0.

---

#### One-step audit + report (Python API)

If you prefer Python scripting over shell pipes:

```bash
python -c "
import json
from pip_audit_html.server import audit_and_report
result = json.loads(audit_and_report(output_path='report.html'))
print('Report saved to :', result['html_path'])
print('Vulnerable       :', result['total_vulnerabilities'])
print('Clean            :', result['is_clean'])
"
```

For a specific project path:

```bash
python -c "
import json
from pip_audit_html.server import audit_and_report
result = json.loads(audit_and_report(target_path='C:/myproject', output_path='report.html'))
print(json.dumps(result, indent=2))
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


