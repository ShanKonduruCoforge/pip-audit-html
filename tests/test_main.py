import io
import json

import pytest

from pip_audit_html.cli import main
from pip_audit_html.converter import convert_json_to_html, load_report


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
    assert "CI Report" in output_path.read_text(encoding="utf-8")


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
