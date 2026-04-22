"""Command line interface for pip-audit-html."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .converter import convert_json_to_html, load_report


DEFAULT_AUTHOR_NAME = "Shan Konduru"
DEFAULT_AUTHOR_URL = "https://www.linkedin.com/in/shankonduru/"


def _parse_ignore_ids(raw_values: list[str] | None) -> list[str]:
    if not raw_values:
        return []

    result: list[str] = []
    for raw in raw_values:
        parts = [item.strip() for item in raw.split(",")]
        result.extend(item for item in parts if item)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pip-audit-html",
        description="Convert pip-audit JSON reports into standalone HTML reports.",
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="Path to pip-audit JSON file. Use '-' or omit to read from stdin.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="pip_audit_report.html",
        help="Output HTML file path.",
    )
    parser.add_argument(
        "--title",
        default="pip-audit HTML report",
        help="Report title shown in the HTML output.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Text encoding for reading input and writing output.",
    )
    parser.add_argument(
        "--author-name",
        default=DEFAULT_AUTHOR_NAME,
        help="Name to show in report footer attribution.",
    )
    parser.add_argument(
        "--author-url",
        default=DEFAULT_AUTHOR_URL,
        help="Profile URL to link from footer attribution (for example LinkedIn).",
    )
    parser.add_argument(
        "--ignore-vuln",
        action="append",
        default=[],
        metavar="ID",
        help="Vulnerability ID/CVE to hide in report. Repeat or pass comma-separated values.",
    )
    parser.add_argument(
        "--fail-on-vulns",
        action="store_true",
        help="Return exit code 1 when vulnerabilities are found.",
    )
    return parser


def _read_input(input_path: str, encoding: str) -> str:
    if input_path == "-":
        return sys.stdin.read()
    return Path(input_path).read_text(encoding=encoding)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    ignore_ids = _parse_ignore_ids(args.ignore_vuln)

    try:
        json_text = _read_input(args.input, args.encoding)
    except OSError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2

    try:
        report = load_report(json_text, ignore_vuln_ids=ignore_ids)
        html_output = convert_json_to_html(
            json_text,
            title=args.title,
            author_name=args.author_name,
            author_url=args.author_url,
            ignore_vuln_ids=ignore_ids,
        )
    except ValueError as exc:
        print(f"Invalid report data: {exc}", file=sys.stderr)
        return 2

    try:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_output, encoding=args.encoding)
    except OSError as exc:
        print(f"Output error: {exc}", file=sys.stderr)
        return 2

    print(f"HTML report written to: {output_path}")
    print(f"Total dependencies: {report['total_dependencies']}")
    print(f"Total vulnerabilities: {report['total_vulnerabilities']}")

    if args.fail_on_vulns and int(report["total_vulnerabilities"]) > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
