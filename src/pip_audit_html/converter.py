"""Conversion logic from pip-audit JSON format to HTML output."""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from typing import Any, Dict, List


def _safe_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    return []


def _normalize_ignore_ids(ignore_vuln_ids: List[str] | None) -> set[str]:
    if not ignore_vuln_ids:
        return set()
    return {item.strip().upper() for item in ignore_vuln_ids if item and item.strip()}


def load_report(json_text: str, ignore_vuln_ids: List[str] | None = None) -> Dict[str, Any]:
    """Parse and normalize a pip-audit JSON payload."""
    try:
        raw = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON input: {exc}") from exc

    ignored_ids = _normalize_ignore_ids(ignore_vuln_ids)

    dependencies = _safe_list(raw.get("dependencies"))
    normalized_dependencies: List[Dict[str, Any]] = []
    total_vulns = 0
    total_skipped = 0

    for dep in dependencies:
        if not isinstance(dep, dict):
            continue

        name = str(dep.get("name", "unknown"))
        skip_reason = dep.get("skip_reason")

        if skip_reason is not None:
            total_skipped += 1
            normalized_dependencies.append(
                {
                    "name": name,
                    "version": None,
                    "skipped": True,
                    "skip_reason": str(skip_reason),
                    "vulnerabilities": [],
                }
            )
            continue

        version = str(dep.get("version", "unknown"))
        vulns = _safe_list(dep.get("vulns"))

        normalized_vulns: List[Dict[str, Any]] = []
        for vuln in vulns:
            if not isinstance(vuln, dict):
                continue

            vuln_id = str(vuln.get("id", "N/A"))
            aliases = [str(item) for item in _safe_list(vuln.get("aliases"))]
            fix_versions = [str(item) for item in _safe_list(vuln.get("fix_versions"))]
            description = str(vuln.get("description", ""))

            candidates = {vuln_id.upper(), *(alias.upper() for alias in aliases)}
            if ignored_ids.intersection(candidates):
                continue

            normalized_vulns.append(
                {
                    "id": vuln_id,
                    "aliases": aliases,
                    "fix_versions": fix_versions,
                    "description": description,
                }
            )

        total_vulns += len(normalized_vulns)
        normalized_dependencies.append(
            {
                "name": name,
                "version": version,
                "skipped": False,
                "skip_reason": None,
                "vulnerabilities": normalized_vulns,
            }
        )

    audited = len(normalized_dependencies) - total_skipped
    safe_count = audited - total_vulns

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dependencies": normalized_dependencies,
        "total_dependencies": len(normalized_dependencies),
        "total_vulnerabilities": total_vulns,
        "total_skipped": total_skipped,
        "total_safe": safe_count,
    }


def _vuln_badges(vulns: List[Dict[str, Any]]) -> str:
    if not vulns:
        return ""
    parts = []
    for v in vulns:
        vid = html.escape(str(v.get("id", "N/A")))
        parts.append(f'<span class="badge badge-vuln">{vid}</span>')
    return " ".join(parts)


def _alias_badges(aliases: List[str]) -> str:
    if not aliases:
        return '<span class="muted">—</span>'
    return " ".join(f'<span class="badge badge-alias">{html.escape(a)}</span>' for a in aliases)


def _fix_badges(fix_versions: List[str]) -> str:
    if not fix_versions:
        return '<span class="muted">None listed</span>'
    return " ".join(f'<span class="badge badge-fix">{html.escape(v)}</span>' for v in fix_versions)


def _description_cell(vulns: List[Dict[str, Any]]) -> str:
    if not vulns:
        return '<span class="muted">—</span>'
    parts = []
    for v in vulns:
        desc = html.escape(str(v.get("description", "")).strip())
        if desc:
            parts.append(f'<p class="desc">{desc}</p>')
    return "".join(parts) or '<span class="muted">—</span>'


def render_html(
  report: Dict[str, Any],
  title: str = "pip-audit HTML report",
  author_name: str | None = None,
  author_url: str | None = None,
) -> str:
    """Render normalized report data to a standalone HTML document."""
    total_dependencies = int(report.get("total_dependencies", 0))
    total_vulnerabilities = int(report.get("total_vulnerabilities", 0))
    total_skipped = int(report.get("total_skipped", 0))
    total_safe = int(report.get("total_safe", 0))
    generated_at = str(report.get("generated_at", ""))

    audited = total_dependencies - total_skipped
    score_pct = int((total_safe / audited) * 100) if audited > 0 else 100
    score_color = "#16a34a" if score_pct == 100 else ("#f59e0b" if score_pct >= 80 else "#dc2626")
    overall_status = "All Clear" if total_vulnerabilities == 0 else "Vulnerabilities Found"
    header_class = "header-ok" if total_vulnerabilities == 0 else "header-alert"

    dependency_rows: List[str] = []
    for dep in report.get("dependencies", []):
        dep_name = html.escape(str(dep.get("name", "unknown")))
        skipped = dep.get("skipped", False)
        vulns = dep.get("vulnerabilities", [])

        if skipped:
            skip_reason = html.escape(str(dep.get("skip_reason", "")))
            dependency_rows.append(
                f'<tr class="row-skip" data-status="skipped">'
                f'<td><span class="pkg-name">{dep_name}</span></td>'
                f'<td><span class="badge badge-skip">skipped</span></td>'
                f'<td colspan="4"><span class="muted">{skip_reason}</span></td>'
                f'</tr>'
            )
            continue

        dep_version = html.escape(str(dep.get("version", "unknown")))

        if not vulns:
            dependency_rows.append(
                f'<tr class="row-safe" data-status="safe">'
                f'<td><span class="pkg-name">{dep_name}</span></td>'
                f'<td><code class="version">{dep_version}</code></td>'
                f'<td><span class="badge badge-safe">&#10003; Safe</span></td>'
                f'<td><span class="muted">—</span></td>'
                f'<td><span class="muted">—</span></td>'
                f'<td><span class="muted">—</span></td>'
                f'</tr>'
            )
        else:
            all_aliases: List[str] = []
            all_fixes: List[str] = []
            for v in vulns:
                all_aliases.extend(v.get("aliases", []))
                all_fixes.extend(v.get("fix_versions", []))
            all_aliases = list(dict.fromkeys(all_aliases))
            all_fixes = list(dict.fromkeys(all_fixes))

            dependency_rows.append(
                f'<tr class="row-vuln" data-status="vulnerable">'
                f'<td><span class="pkg-name">{dep_name}</span></td>'
                f'<td><code class="version">{dep_version}</code></td>'
                f'<td>{_vuln_badges(vulns)}</td>'
                f'<td>{_alias_badges(all_aliases)}</td>'
                f'<td>{_fix_badges(all_fixes)}</td>'
                f'<td>{_description_cell(vulns)}</td>'
                f'</tr>'
            )

    rows_html = "\n".join(dependency_rows)
    escaped_title = html.escape(title)

    footer_attribution = ""
    if author_name:
      safe_name = html.escape(author_name)
      if author_url:
        safe_url = html.escape(author_url, quote=True)
        footer_attribution = f' &mdash; Designed and developed by <a href="{safe_url}" target="_blank" rel="noopener noreferrer">{safe_name}</a>'
      else:
        footer_attribution = f" &mdash; Designed and developed by {safe_name}"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escaped_title}</title>
  <style>
    /* ── Reset & base ── */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg:       #f0f4f9;
      --surface:  #ffffff;
      --border:   #dde4f0;
      --text:     #1a2433;
      --muted:    #64748b;
      --accent:   #2563eb;
      --ok:       #16a34a;
      --ok-bg:    #f0fdf4;
      --ok-bdr:   #bbf7d0;
      --warn:     #d97706;
      --danger:   #dc2626;
      --danger-bg:#fff1f2;
      --danger-bdr:#fecdd3;
      --skip-bg:  #f8fafc;
      --skip-bdr: #cbd5e1;
      --radius:   14px;
      --shadow:   0 4px 24px rgba(30,40,80,.10);
    }}
    body {{
      font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
    }}

    /* ── Header ── */
    .site-header {{
      padding: 0;
      margin-bottom: 32px;
    }}
    .header-ok  {{ background: linear-gradient(135deg, #1d4ed8 0%, #0891b2 100%); }}
    .header-alert {{ background: linear-gradient(135deg, #991b1b 0%, #b45309 100%); }}
    .header-inner {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 36px 32px 32px;
      display: flex;
      align-items: center;
      gap: 20px;
    }}
    .shield-icon {{
      width: 56px; height: 56px; flex-shrink: 0;
      background: rgba(255,255,255,.15);
      border-radius: 16px;
      display: flex; align-items: center; justify-content: center;
    }}
    .shield-icon svg {{ width: 32px; height: 32px; fill: white; }}
    .header-text h1 {{
      font-size: 26px; font-weight: 700;
      color: white; letter-spacing: -.3px;
    }}
    .header-text p {{
      color: rgba(255,255,255,.75);
      font-size: 13px; margin-top: 4px;
    }}
    .header-status {{
      margin-left: auto;
      background: rgba(255,255,255,.18);
      border: 1px solid rgba(255,255,255,.3);
      border-radius: 999px;
      padding: 6px 18px;
      color: white;
      font-weight: 600; font-size: 14px;
      white-space: nowrap;
    }}

    /* ── Layout ── */
    .container {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 0 32px 48px;
    }}

    /* ── Stat cards ── */
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }}
    .stat-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 20px 24px;
      position: relative;
      overflow: hidden;
    }}
    .stat-card::before {{
      content: "";
      position: absolute; top: 0; left: 0;
      width: 4px; height: 100%;
      background: var(--stat-color, var(--accent));
      border-radius: 4px 0 0 4px;
    }}
    .stat-label {{
      font-size: 11px; font-weight: 600;
      text-transform: uppercase; letter-spacing: .06em;
      color: var(--muted);
      margin-bottom: 6px;
    }}
    .stat-value {{
      font-size: 36px; font-weight: 800;
      color: var(--stat-color, var(--text));
      line-height: 1;
    }}
    .stat-sub {{
      font-size: 12px; color: var(--muted); margin-top: 4px;
    }}
    .stat-card.c-total  {{ --stat-color: #2563eb; }}
    .stat-card.c-safe   {{ --stat-color: #16a34a; }}
    .stat-card.c-vuln   {{ --stat-color: #dc2626; }}
    .stat-card.c-skip   {{ --stat-color: #94a3b8; }}

    /* ── Score bar ── */
    .score-row {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 20px 24px;
      margin-bottom: 28px;
      display: flex;
      align-items: center;
      gap: 20px;
    }}
    .score-label {{ font-size: 13px; font-weight: 600; white-space: nowrap; min-width: 110px; }}
    .bar-track {{
      flex: 1;
      height: 12px;
      background: #e2e8f0;
      border-radius: 999px;
      overflow: hidden;
    }}
    .bar-fill {{
      height: 100%;
      border-radius: 999px;
      transition: width .6s ease;
      background: {score_color};
      width: {score_pct}%;
    }}
    .score-pct {{
      font-size: 22px; font-weight: 800;
      color: {score_color};
      min-width: 56px; text-align: right;
    }}

    /* ── Controls ── */
    .controls {{
      display: flex; gap: 12px; flex-wrap: wrap;
      margin-bottom: 16px; align-items: center;
    }}
    .search-box {{
      flex: 1; min-width: 220px;
      padding: 9px 14px;
      border: 1px solid var(--border);
      border-radius: 8px;
      font-size: 14px;
      background: var(--surface);
      outline: none;
      color: var(--text);
    }}
    .search-box:focus {{ border-color: var(--accent); box-shadow: 0 0 0 3px rgba(37,99,235,.15); }}
    .filter-group {{ display: flex; gap: 6px; flex-wrap: wrap; }}
    .filter-btn {{
      padding: 8px 16px;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--surface);
      font-size: 13px; font-weight: 500;
      cursor: pointer; color: var(--text);
      transition: all .15s;
    }}
    .filter-btn:hover {{ background: #f1f5fd; border-color: var(--accent); }}
    .filter-btn.active {{
      background: var(--accent); color: white;
      border-color: var(--accent);
    }}
    .result-count {{ font-size: 13px; color: var(--muted); margin-left: auto; }}

    /* ── Table card ── */
    .table-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      overflow: hidden;
    }}
    .table-wrap {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; }}
    thead th {{
      position: sticky; top: 0; z-index: 1;
      background: #f8fafc;
      border-bottom: 2px solid var(--border);
      padding: 12px 16px;
      font-size: 12px; font-weight: 700;
      text-transform: uppercase; letter-spacing: .06em;
      color: var(--muted);
      text-align: left; white-space: nowrap;
    }}
    tbody tr {{
      border-bottom: 1px solid var(--border);
      transition: background .1s;
    }}
    tbody tr:last-child {{ border-bottom: none; }}
    tbody tr:hover {{ background: #f8fafc; }}
    td {{ padding: 12px 16px; vertical-align: top; font-size: 14px; }}

    /* ── Row states ── */
    .row-vuln {{ border-left: 4px solid var(--danger); }}
    .row-vuln td:first-child {{ padding-left: 12px; }}
    .row-safe {{ border-left: 4px solid var(--ok); }}
    .row-safe td:first-child {{ padding-left: 12px; }}
    .row-skip {{ border-left: 4px solid #94a3b8; opacity: .8; }}
    .row-skip td:first-child {{ padding-left: 12px; }}

    /* ── Inline elements ── */
    .pkg-name {{ font-weight: 600; }}
    .version {{
      font-family: "Cascadia Code", "Fira Code", monospace;
      font-size: 13px;
      background: #f1f5f9; border: 1px solid #e2e8f0;
      padding: 2px 7px; border-radius: 5px;
    }}
    .badge {{
      display: inline-block;
      font-size: 11px; font-weight: 600;
      padding: 3px 8px; border-radius: 5px;
      letter-spacing: .02em;
      white-space: nowrap;
    }}
    .badge-vuln  {{ background: var(--danger-bg); color: var(--danger); border: 1px solid var(--danger-bdr); }}
    .badge-alias {{ background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }}
    .badge-fix   {{ background: var(--ok-bg); color: #15803d; border: 1px solid var(--ok-bdr); }}
    .badge-safe  {{ background: var(--ok-bg); color: #15803d; border: 1px solid var(--ok-bdr); }}
    .badge-skip  {{ background: var(--skip-bg); color: var(--muted); border: 1px solid var(--skip-bdr); }}
    .muted {{ color: var(--muted); font-size: 13px; }}
    .desc {{ font-size: 13px; color: #374151; margin: 0 0 6px; line-height: 1.5; }}
    .desc:last-child {{ margin-bottom: 0; }}

    /* ── No results ── */
    .no-results {{
      text-align: center; padding: 48px 24px;
      color: var(--muted); display: none;
    }}

    /* ── Footer ── */
    .footer {{
      text-align: center; margin-top: 32px;
      font-size: 12px; color: var(--muted);
    }}
    .footer a {{
      color: var(--accent);
      text-decoration: none;
      font-weight: 600;
    }}
    .footer a:hover {{ text-decoration: underline; }}

    /* ── Print ── */
    @media print {{
      .site-header {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
      .controls {{ display: none; }}
    }}

    /* ── Responsive ── */
    @media (max-width: 700px) {{
      .container {{ padding: 0 16px 32px; }}
      .header-inner {{ padding: 24px 16px; flex-wrap: wrap; }}
      .header-status {{ margin-left: 0; }}
      .stats {{ grid-template-columns: repeat(2, 1fr); }}
      td, th {{ padding: 10px 12px; }}
    }}
  </style>
</head>
<body>

<header class="site-header {header_class}">
  <div class="header-inner">
    <div class="shield-icon">
      <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-1 14l-3-3 1.41-1.41L11 12.17l4.59-4.58L17 9l-6 6z"/>
      </svg>
    </div>
    <div class="header-text">
      <h1>{escaped_title}</h1>
      <p>Generated: {html.escape(generated_at)} &nbsp;|&nbsp; pip-audit-html</p>
    </div>
    <span class="header-status">{overall_status}</span>
  </div>
</header>

<div class="container">

  <!-- Stat cards -->
  <div class="stats">
    <div class="stat-card c-total">
      <div class="stat-label">Total Packages</div>
      <div class="stat-value">{total_dependencies}</div>
      <div class="stat-sub">{audited} audited</div>
    </div>
    <div class="stat-card c-safe">
      <div class="stat-label">Secure</div>
      <div class="stat-value">{total_safe}</div>
      <div class="stat-sub">No vulnerabilities</div>
    </div>
    <div class="stat-card c-vuln">
      <div class="stat-label">Vulnerable</div>
      <div class="stat-value">{total_vulnerabilities}</div>
      <div class="stat-sub">Known CVEs / advisories</div>
    </div>
    <div class="stat-card c-skip">
      <div class="stat-label">Skipped</div>
      <div class="stat-value">{total_skipped}</div>
      <div class="stat-sub">Not auditable</div>
    </div>
  </div>

  <!-- Security score bar -->
  <div class="score-row">
    <span class="score-label">Security Score</span>
    <div class="bar-track"><div class="bar-fill"></div></div>
    <span class="score-pct">{score_pct}%</span>
  </div>

  <!-- Controls -->
  <div class="controls">
    <input class="search-box" id="search" type="search" placeholder="Search packages..." aria-label="Search packages" />
    <div class="filter-group" id="filterGroup">
      <button class="filter-btn active" data-filter="all">All</button>
      <button class="filter-btn" data-filter="vulnerable">Vulnerable</button>
      <button class="filter-btn" data-filter="safe">Safe</button>
      <button class="filter-btn" data-filter="skipped">Skipped</button>
    </div>
    <span class="result-count" id="resultCount"></span>
  </div>

  <!-- Table -->
  <div class="table-card">
    <div class="table-wrap">
      <table id="depsTable">
        <thead>
          <tr>
            <th>Package</th>
            <th>Version</th>
            <th>Vulnerability ID</th>
            <th>Aliases</th>
            <th>Fix Versions</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody id="tableBody">
          {rows_html}
        </tbody>
      </table>
      <div class="no-results" id="noResults">No packages match your filter.</div>
    </div>
  </div>

  <div class="footer">pip-audit-html &mdash; standalone security report &mdash; {html.escape(generated_at)}{footer_attribution}</div>
</div>

<script>
  (function () {{
    const search = document.getElementById('search');
    const filterGroup = document.getElementById('filterGroup');
    const rows = Array.from(document.querySelectorAll('#tableBody tr'));
    const noResults = document.getElementById('noResults');
    const resultCount = document.getElementById('resultCount');
    let activeFilter = 'all';

    function applyFilters() {{
      const term = search.value.trim().toLowerCase();
      let visible = 0;
      rows.forEach(function(row) {{
        const status = row.dataset.status || '';
        const text = row.textContent.toLowerCase();
        const matchFilter = activeFilter === 'all' || status === activeFilter;
        const matchSearch = !term || text.includes(term);
        const show = matchFilter && matchSearch;
        row.style.display = show ? '' : 'none';
        if (show) visible++;
      }});
      noResults.style.display = visible === 0 ? 'block' : 'none';
      resultCount.textContent = visible + ' of ' + rows.length + ' packages';
    }}

    search.addEventListener('input', applyFilters);

    filterGroup.addEventListener('click', function(e) {{
      const btn = e.target.closest('.filter-btn');
      if (!btn) return;
      filterGroup.querySelectorAll('.filter-btn').forEach(function(b) {{ b.classList.remove('active'); }});
      btn.classList.add('active');
      activeFilter = btn.dataset.filter;
      applyFilters();
    }});

    applyFilters();
  }})();
</script>

</body>
</html>
"""


def convert_json_to_html(
    json_text: str,
    title: str = "pip-audit HTML report",
    author_name: str | None = None,
    author_url: str | None = None,
    ignore_vuln_ids: List[str] | None = None,
) -> str:
    """Convert pip-audit JSON string directly into HTML string."""
    report = load_report(json_text, ignore_vuln_ids=ignore_vuln_ids)
    return render_html(report, title=title, author_name=author_name, author_url=author_url)
