"""MCP server for pip-audit-html.

Exposes pip-audit JSON → HTML conversion as local MCP tools usable from
Claude Desktop, VS Code Copilot, Cursor, and any other MCP-compatible client.

Transport: stdio (fully local, no network required).

Usage
-----
Run directly::

    pip-audit-html-mcp

Or configure in Claude Desktop (claude_desktop_config.json)::

    {
      "mcpServers": {
        "pip-audit-html": {
          "command": "pip-audit-html-mcp"
        }
      }
    }
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as _exc:  # pragma: no cover
    raise SystemExit(
        "The 'mcp' package is required to run the MCP server.\n"
        "Install it with:  pip install 'pip-audit-html[mcp]'"
    ) from _exc

from .cli import DEFAULT_AUTHOR_NAME, DEFAULT_AUTHOR_URL
from .converter import convert_json_to_html, load_report

mcp = FastMCP(
    "pip-audit-html",
    instructions=(
        "Tools for auditing Python package vulnerabilities. "
        "Use run_audit to scan an environment, generate_report to produce an HTML report, "
        "get_vulnerabilities to inspect findings, and get_summary for a quick overview."
    ),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_DEFAULT_AUDIT_TIMEOUT_SECONDS = 600.0
_AUDIT_TIMEOUT_ENV_VAR = "PIP_AUDIT_HTML_TIMEOUT_SECONDS"
_LEGACY_AUDIT_TIMEOUT_ENV_VAR = "PIP_AUDIT_HTML_AUDIT_TIMEOUT_SECONDS"


def _get_audit_timeout_seconds() -> float | None:
    """Return pip-audit timeout from environment.

    The default is 600 seconds. Set PIP_AUDIT_HTML_TIMEOUT_SECONDS to:
    - a positive number of seconds to override the timeout
    - 0, a negative number, "none", "off", or "disable" to disable timeout

    Legacy compatibility:
    - PIP_AUDIT_HTML_AUDIT_TIMEOUT_SECONDS is still accepted when the new
      variable is not set.
    """
    raw_value = os.getenv(_AUDIT_TIMEOUT_ENV_VAR)
    if raw_value is None:
        raw_value = os.getenv(_LEGACY_AUDIT_TIMEOUT_ENV_VAR)
    if raw_value is None:
        raw_value = str(_DEFAULT_AUDIT_TIMEOUT_SECONDS)
    raw_value = raw_value.strip()

    if raw_value.lower() in {"none", "off", "disable", "disabled"}:
        return None

    try:
        timeout = float(raw_value)
    except ValueError:
        return _DEFAULT_AUDIT_TIMEOUT_SECONDS

    if timeout <= 0:
        return None

    return timeout


def _run_pip_audit(target_path: str | None) -> Dict[str, Any]:
    """Run pip-audit against *target_path* (a venv or project directory).

    Returns the parsed JSON dict from pip-audit stdout.
    Raises RuntimeError if pip-audit is not installed or the run fails in an
    unexpected way (non-zero exit when *no* JSON was produced).
    """
    cmd = [sys.executable, "-m", "pip_audit", "--format", "json", "--output", "-"]
    if target_path:
        resolved = Path(target_path).resolve()
        cmd += ["--path", str(resolved)]

    timeout_seconds = _get_audit_timeout_seconds()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            "pip-audit timed out. "
            f"Increase {_AUDIT_TIMEOUT_ENV_VAR} (seconds) or set it to 0/none to disable timeout. "
            f"Current effective timeout: {timeout_seconds if timeout_seconds is not None else 'disabled'}"
        ) from exc
    except FileNotFoundError as exc:
        raise RuntimeError(
            "pip-audit is not installed. Run: pip install pip-audit"
        ) from exc

    stdout = result.stdout.strip()
    if not stdout:
        raise RuntimeError(
            f"pip-audit produced no output (exit {result.returncode}).\n"
            f"stderr: {result.stderr.strip()}"
        )

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"pip-audit output was not valid JSON: {exc}\nOutput: {stdout[:500]}"
        ) from exc


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def run_audit(target_path: str = "") -> str:
    """Run pip-audit on the current Python environment or a specific path.

    Parameters
    ----------
    target_path:
        Optional filesystem path to a virtual environment or project directory
        to audit. Leave empty to audit the currently active Python environment.

    Returns
    -------
    A JSON string containing the raw pip-audit findings.
    """
    raw = _run_pip_audit(target_path or None)
    return json.dumps(raw, indent=2)


@mcp.tool()
def generate_report(
    json_input: str,
    output_path: str = "",
    title: str = "pip-audit HTML report",
    ignore_vulns: str = "",
    author_name: str = DEFAULT_AUTHOR_NAME,
    author_url: str = DEFAULT_AUTHOR_URL,
) -> str:
    """Convert pip-audit JSON into a standalone HTML report file.

    Parameters
    ----------
    json_input:
        pip-audit JSON string (pass the output of run_audit or read a .json file).
    output_path:
        Where to save the HTML file. Defaults to a temp file if omitted.
    title:
        Title shown at the top of the HTML report.
    ignore_vulns:
        Comma-separated vulnerability IDs (PYSEC-*, CVE-*) to exclude from
        the report. Example: "PYSEC-2023-1,CVE-2022-1234"
    author_name:
        Name shown in the report footer.
    author_url:
        URL linked from the report footer.

    Returns
    -------
    Absolute path to the generated HTML file.
    """
    ignore_ids = [v.strip() for v in ignore_vulns.split(",") if v.strip()] if ignore_vulns else []

    html_content = convert_json_to_html(
        json_input,
        title=title,
        author_name=author_name,
        author_url=author_url,
        ignore_vuln_ids=ignore_ids,
    )

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
    else:
        fd, tmp = tempfile.mkstemp(suffix=".html", prefix="pip_audit_")
        import os
        os.close(fd)
        out = Path(tmp)

    out.write_text(html_content, encoding="utf-8")
    return str(out.resolve())


@mcp.tool()
def get_vulnerabilities(
    json_input: str,
    ignore_vulns: str = "",
) -> str:
    """Return a structured list of vulnerabilities found in a pip-audit JSON report.

    Parameters
    ----------
    json_input:
        pip-audit JSON string (pass the output of run_audit or read a .json file).
    ignore_vulns:
        Comma-separated vulnerability IDs to exclude from the results.

    Returns
    -------
    JSON array of objects, each with: package, version, vuln_id, aliases,
    fix_versions, description.
    """
    ignore_ids = [v.strip() for v in ignore_vulns.split(",") if v.strip()] if ignore_vulns else []
    report = load_report(json_input, ignore_vuln_ids=ignore_ids)

    findings: List[Dict[str, Any]] = []
    for dep in report.get("dependencies", []):
        if dep.get("skipped"):
            continue
        for vuln in dep.get("vulnerabilities", []):
            findings.append(
                {
                    "package": dep["name"],
                    "version": dep["version"],
                    "vuln_id": vuln["id"],
                    "aliases": vuln["aliases"],
                    "fix_versions": vuln["fix_versions"],
                    "description": vuln["description"],
                }
            )

    return json.dumps(findings, indent=2)


@mcp.tool()
def get_summary(
    json_input: str,
    ignore_vulns: str = "",
) -> str:
    """Return a concise summary of a pip-audit JSON report.

    Parameters
    ----------
    json_input:
        pip-audit JSON string (pass the output of run_audit or read a .json file).
    ignore_vulns:
        Comma-separated vulnerability IDs to exclude from the summary counts.

    Returns
    -------
    JSON object with: total_dependencies, total_vulnerabilities, total_safe,
    total_skipped, is_clean, generated_at.
    """
    ignore_ids = [v.strip() for v in ignore_vulns.split(",") if v.strip()] if ignore_vulns else []
    report = load_report(json_input, ignore_vuln_ids=ignore_ids)

    summary = {
        "total_dependencies": report["total_dependencies"],
        "total_vulnerabilities": report["total_vulnerabilities"],
        "total_safe": report["total_safe"],
        "total_skipped": report["total_skipped"],
        "is_clean": report["total_vulnerabilities"] == 0,
        "generated_at": report["generated_at"],
    }
    return json.dumps(summary, indent=2)


@mcp.tool()
def audit_and_report(
    target_path: str = "",
    output_path: str = "",
    title: str = "pip-audit HTML report",
    ignore_vulns: str = "",
) -> str:
    """Run pip-audit and immediately generate an HTML report in one step.

    Parameters
    ----------
    target_path:
        Optional path to a venv or project directory. Empty = current environment.
    output_path:
        Where to save the HTML file. Defaults to a temp file if omitted.
    title:
        Title shown at the top of the HTML report.
    ignore_vulns:
        Comma-separated vulnerability IDs to exclude.

    Returns
    -------
    JSON object with: html_path, total_dependencies, total_vulnerabilities,
    total_safe, total_skipped, is_clean.
    """
    raw_json = run_audit(target_path)
    html_path = generate_report(
        json_input=raw_json,
        output_path=output_path,
        title=title,
        ignore_vulns=ignore_vulns,
    )
    summary_json = get_summary(raw_json, ignore_vulns=ignore_vulns)
    summary = json.loads(summary_json)
    summary["html_path"] = html_path
    return json.dumps(summary, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:  # pragma: no cover
    mcp.run(transport="stdio")


if __name__ == "__main__":  # pragma: no cover
    main()
