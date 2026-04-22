import io
import json
import unittest.mock as mock

import pytest

from pip_audit_html.cli import main
from pip_audit_html.converter import convert_json_to_html, load_report
mcp = pytest.importorskip("mcp", reason="mcp extra not installed")
from pip_audit_html.server import (  # noqa: E402
    audit_and_report,
    generate_report,
    get_summary,
    get_vulnerabilities,
)


@pytest.mark.unit
def test_convert_json_to_html_contains_dependency_data():
    sample = {
        "dependencies": [
            {
                "name": "requests",
                "version": "2.19.0",
                "vulns": [
                    {
                        "id": "PYSEC-TEST-1",
                        "aliases": ["CVE-2020-0001"],
                        "fix_versions": ["2.20.0"],
                        "description": "Example vulnerability",
                    }
                ],
            }
        ]
    }

    html = convert_json_to_html(json.dumps(sample), title="Security Report")

    assert "Security Report" in html
    assert "requests" in html
    assert "PYSEC-TEST-1" in html
    assert "2.20.0" in html


@pytest.mark.unit
def test_convert_json_to_html_includes_author_footer_link():
    sample = {"dependencies": [{"name": "requests", "version": "2.19.0", "vulns": []}]}

    html = convert_json_to_html(
        json.dumps(sample),
        title="Security Report",
        author_name="Ravi Konduru",
        author_url="https://www.linkedin.com/in/ravi-konduru",
    )

    assert "Designed and developed by" in html
    assert "Ravi Konduru" in html
    assert "https://www.linkedin.com/in/ravi-konduru" in html


@pytest.mark.unit
def test_convert_json_to_html_ignores_selected_vulns_and_aliases():
    sample = {
        "dependencies": [
            {
                "name": "requests",
                "version": "2.19.0",
                "vulns": [
                    {
                        "id": "PYSEC-TEST-1",
                        "aliases": ["CVE-2020-0001"],
                        "fix_versions": ["2.20.0"],
                        "description": "Should be hidden",
                    },
                    {
                        "id": "PYSEC-TEST-2",
                        "aliases": ["CVE-2020-0002"],
                        "fix_versions": ["2.21.0"],
                        "description": "Should remain",
                    },
                ],
            }
        ]
    }

    html = convert_json_to_html(
        json.dumps(sample),
        ignore_vuln_ids=["CVE-2020-0001"],
    )

    assert "PYSEC-TEST-1" not in html
    assert "Should be hidden" not in html
    assert "PYSEC-TEST-2" in html


@pytest.mark.edge
def test_load_report_invalid_json_raises_value_error():
    with pytest.raises(ValueError):
        load_report("{bad json}")


@pytest.mark.integration
def test_cli_from_file_writes_html(tmp_path):
    input_path = tmp_path / "audit.json"
    output_path = tmp_path / "report.html"
    input_path.write_text(
        json.dumps({"dependencies": [{"name": "flask", "version": "0.5", "vulns": []}]}),
        encoding="utf-8",
    )

    code = main([str(input_path), "-o", str(output_path), "--title", "CI Report"])

    assert code == 0
    assert output_path.exists()
    output_html = output_path.read_text(encoding="utf-8")
    assert "CI Report" in output_html
    assert "Shan Konduru" in output_html
    assert "https://www.linkedin.com/in/shankonduru/" in output_html


@pytest.mark.integration
def test_cli_from_stdin(monkeypatch, tmp_path):
    output_path = tmp_path / "stdin-report.html"
    payload = json.dumps({"dependencies": [{"name": "urllib3", "version": "1.26.0", "vulns": []}]})
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))

    code = main(["-", "-o", str(output_path)])

    assert code == 0
    assert output_path.exists()


@pytest.mark.integration
def test_cli_fail_on_vulns_returns_1(tmp_path):
    input_path = tmp_path / "audit-with-vulns.json"
    output_path = tmp_path / "report.html"
    input_path.write_text(
        json.dumps(
            {
                "dependencies": [
                    {
                        "name": "pkg",
                        "version": "1.0",
                        "vulns": [{"id": "PYSEC-1", "fix_versions": []}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    code = main([str(input_path), "-o", str(output_path), "--fail-on-vulns"])

    assert code == 1
    assert output_path.exists()


@pytest.mark.integration
def test_cli_ignore_vuln_changes_exit_code_and_output(tmp_path):
    input_path = tmp_path / "audit-with-vulns.json"
    output_path = tmp_path / "report.html"
    input_path.write_text(
        json.dumps(
            {
                "dependencies": [
                    {
                        "name": "pkg",
                        "version": "1.0",
                        "vulns": [
                            {
                                "id": "PYSEC-1",
                                "aliases": ["CVE-2026-1234"],
                                "fix_versions": [],
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    code = main(
        [
            str(input_path),
            "-o",
            str(output_path),
            "--fail-on-vulns",
            "--ignore-vuln",
            "CVE-2026-1234",
        ]
    )

    assert code == 0
    html = output_path.read_text(encoding="utf-8")
    assert "PYSEC-1" not in html


# ---------------------------------------------------------------------------
# MCP server tool tests
# ---------------------------------------------------------------------------

_SAMPLE_AUDIT_JSON = json.dumps(
    {
        "dependencies": [
            {
                "name": "requests",
                "version": "2.19.0",
                "vulns": [
                    {
                        "id": "PYSEC-TEST-1",
                        "aliases": ["CVE-2020-0001"],
                        "fix_versions": ["2.20.0"],
                        "description": "Example vulnerability",
                    }
                ],
            },
            {"name": "flask", "version": "2.0.0", "vulns": []},
        ]
    }
)


@pytest.mark.unit
def test_mcp_get_summary_returns_correct_counts():
    result = json.loads(get_summary(_SAMPLE_AUDIT_JSON))

    assert result["total_dependencies"] == 2
    assert result["total_vulnerabilities"] == 1
    assert result["total_safe"] == 1
    assert result["total_skipped"] == 0
    assert result["is_clean"] is False


@pytest.mark.unit
def test_mcp_get_vulnerabilities_returns_findings():
    result = json.loads(get_vulnerabilities(_SAMPLE_AUDIT_JSON))

    assert len(result) == 1
    finding = result[0]
    assert finding["package"] == "requests"
    assert finding["vuln_id"] == "PYSEC-TEST-1"
    assert "CVE-2020-0001" in finding["aliases"]
    assert "2.20.0" in finding["fix_versions"]


@pytest.mark.unit
def test_mcp_get_vulnerabilities_respects_ignore_vulns():
    result = json.loads(
        get_vulnerabilities(_SAMPLE_AUDIT_JSON, ignore_vulns="CVE-2020-0001")
    )

    assert result == []


@pytest.mark.unit
def test_mcp_get_summary_is_clean_when_all_ignored():
    result = json.loads(
        get_summary(_SAMPLE_AUDIT_JSON, ignore_vulns="PYSEC-TEST-1")
    )

    assert result["is_clean"] is True
    assert result["total_vulnerabilities"] == 0


@pytest.mark.integration
def test_mcp_generate_report_writes_html_file(tmp_path):
    out = tmp_path / "mcp_report.html"
    path = generate_report(
        json_input=_SAMPLE_AUDIT_JSON,
        output_path=str(out),
        title="MCP Test Report",
    )

    assert path == str(out.resolve())
    content = out.read_text(encoding="utf-8")
    assert "MCP Test Report" in content
    assert "requests" in content
    assert "Shan Konduru" in content


@pytest.mark.integration
def test_mcp_generate_report_uses_temp_file_when_no_output_path():
    path = generate_report(json_input=_SAMPLE_AUDIT_JSON)

    from pathlib import Path
    p = Path(path)
    assert p.exists()
    assert p.suffix == ".html"
    p.unlink()


@pytest.mark.integration
def test_mcp_audit_and_report_combines_audit_and_generate(tmp_path):
    out = tmp_path / "combined.html"
    fake_audit_json = _SAMPLE_AUDIT_JSON

    with mock.patch(
        "pip_audit_html.server.run_audit", return_value=fake_audit_json
    ):
        result = json.loads(
            audit_and_report(output_path=str(out), title="Combined Report")
        )

    assert result["total_dependencies"] == 2
    assert result["total_vulnerabilities"] == 1
    assert "html_path" in result
    assert out.exists()
