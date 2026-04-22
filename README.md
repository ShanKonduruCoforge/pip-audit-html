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

You can also run it as a module:

```bash
python -m pip_audit_html pip-audit-report.json -o report.html
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


