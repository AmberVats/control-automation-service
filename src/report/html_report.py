"""
HTML Exception and Control Run Report Generator for HSBC Product Control Analytics.
Produces standalone, corporate-formatted HTML reports for financial controls and breach investigations.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from sqlalchemy.orm import Session
from src.db.models import ControlRunModel, ControlExceptionModel


def render_html_report(run_record: ControlRunModel, exceptions: List[ControlExceptionModel]) -> str:
    """
    Render a self-contained, responsive HTML report for a specific control execution run.
    """
    status = run_record.status.upper()
    status_bg = "#d4edda" if status == "PASS" else "#f8d7da" if status == "BREACH" else "#fff3cd"
    status_color = "#155724" if status == "PASS" else "#721c24" if status == "BREACH" else "#856404"
    status_border = "#c3e6cb" if status == "PASS" else "#f5c6cb" if status == "BREACH" else "#ffeeba"

    # Format exceptions table rows
    exception_rows_html = ""
    if not exceptions:
        exception_rows_html = """
        <tr>
            <td colspan="8" style="text-align: center; padding: 24px; color: #28a745; font-weight: 600;">
                ✓ No exceptions or threshold breaches detected during this control execution.
            </td>
        </tr>
        """
    else:
        for idx, exc in enumerate(exceptions, start=1):
            diff_display = f"{exc.difference:,.2f}" if exc.difference is not None else "—"
            src_display = exc.source_val if exc.source_val is not None else "—"
            tgt_display = exc.target_val if exc.target_val is not None else "—"
            field_display = exc.field if exc.field else "—"
            key_display = exc.key_data if exc.key_data else "—"

            exception_rows_html += f"""
            <tr>
                <td style="font-weight: bold; text-align: center;">{idx}</td>
                <td><span class="badge badge-type">{exc.exception_type}</span></td>
                <td style="font-family: monospace; font-size: 12px; color: #333;">{key_display}</td>
                <td style="font-weight: 500;">{field_display}</td>
                <td style="text-align: right; font-family: monospace;">{src_display}</td>
                <td style="text-align: right; font-family: monospace;">{tgt_display}</td>
                <td style="text-align: right; font-family: monospace; font-weight: bold; color: #d9534f;">{diff_display}</td>
                <td style="font-size: 13px; color: #555;">{exc.message or ''}</td>
            </tr>
            """

    formatted_start = run_record.start_time.strftime("%Y-%m-%d %H:%M:%S UTC") if run_record.start_time else "—"
    formatted_duration = f"{run_record.duration_ms:,.2f} ms" if run_record.duration_ms else "—"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Control Run Report — {run_record.control_name} ({run_record.run_id[:8]})</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f4f6f9;
            color: #212529;
            line-height: 1.5;
            padding: 24px;
        }}
        .report-container {{
            max-width: 1200px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.06);
            overflow: hidden;
            border: 1px solid #e1e4e8;
        }}
        .header-bar {{
            background: #1e2229;
            color: #ffffff;
            padding: 20px 32px;
            border-bottom: 4px solid #db0011;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header-bar h1 {{
            font-size: 20px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}
        .header-bar .subtitle {{
            font-size: 12px;
            color: #a0aec0;
            margin-top: 4px;
        }}
        .header-badge {{
            background: rgba(255,255,255,0.1);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.5px;
            border: 1px solid rgba(255,255,255,0.2);
        }}
        .body-section {{
            padding: 32px;
        }}
        .cards-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }}
        .card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 16px 20px;
        }}
        .card-label {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            color: #64748b;
            margin-bottom: 6px;
            font-weight: 600;
        }}
        .card-value {{
            font-size: 22px;
            font-weight: 700;
            color: #0f172a;
        }}
        .status-pill {{
            display: inline-block;
            padding: 4px 14px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 16px;
            background-color: {status_bg};
            color: {status_color};
            border: 1px solid {status_border};
        }}
        .meta-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 32px;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            overflow: hidden;
        }}
        .meta-table td {{
            padding: 10px 16px;
            font-size: 13px;
            border-bottom: 1px solid #edf2f7;
        }}
        .meta-table td.label {{
            width: 22%;
            font-weight: 600;
            color: #475569;
            background: #f8fafc;
            border-right: 1px solid #edf2f7;
        }}
        .meta-table td.val {{
            font-family: monospace;
            color: #1e293b;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 16px;
            color: #1e293b;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .table-responsive {{
            overflow-x: auto;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
        }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        .data-table th {{
            background: #2d3748;
            color: #ffffff;
            font-weight: 600;
            padding: 12px 14px;
            text-align: left;
            font-size: 12px;
            letter-spacing: 0.5px;
        }}
        .data-table td {{
            padding: 10px 14px;
            border-bottom: 1px solid #e2e8f0;
        }}
        .data-table tr:nth-child(even) {{
            background: #f8fafc;
        }}
        .badge-type {{
            background: #e2e8f0;
            color: #334155;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            font-family: monospace;
        }}
        .footer {{
            background: #f8fafc;
            border-top: 1px solid #e2e8f0;
            padding: 16px 32px;
            text-align: center;
            font-size: 12px;
            color: #94a3b8;
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="header-bar">
            <div>
                <h1>HSBC Product Control Analytics</h1>
                <div class="subtitle">Citizen Developer Framework — Automated Control Run Report</div>
            </div>
            <div class="header-badge">Control Automation Service v1.0</div>
        </div>

        <div class="body-section">
            <div class="cards-grid">
                <div class="card">
                    <div class="card-label">Execution Status</div>
                    <div><span class="status-pill">{status}</span></div>
                </div>
                <div class="card">
                    <div class="card-label">Breaches Detected</div>
                    <div class="card-value" style="color: {'#dc3545' if run_record.breach_count > 0 else '#28a745'};">{run_record.breach_count}</div>
                </div>
                <div class="card">
                    <div class="card-label">Input Rows Evaluated</div>
                    <div class="card-value">{run_record.row_count_in:,}</div>
                </div>
                <div class="card">
                    <div class="card-label">Execution Duration</div>
                    <div class="card-value">{formatted_duration}</div>
                </div>
            </div>

            <div class="section-title">Control Execution Metadata</div>
            <table class="meta-table">
                <tr>
                    <td class="label">Control Name</td>
                    <td class="val">{run_record.control_name} (v{run_record.version})</td>
                    <td class="label">Run ID</td>
                    <td class="val">{run_record.run_id}</td>
                </tr>
                <tr>
                    <td class="label">As-Of Date</td>
                    <td class="val">{run_record.as_of_date or 'N/A'}</td>
                    <td class="label">Execution Timestamp</td>
                    <td class="val">{formatted_start}</td>
                </tr>
                <tr>
                    <td class="label">Triggered By</td>
                    <td class="val">{run_record.triggered_by}</td>
                    <td class="label">Configuration Hash</td>
                    <td class="val">{run_record.config_hash}</td>
                </tr>
            </table>

            <div class="section-title">
                <span>Detailed Exception Breaches</span>
                <span style="font-size: 13px; font-weight: normal; color: #64748b;">Total Breaches: {len(exceptions)}</span>
            </div>
            <div class="table-responsive">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th style="width: 40px; text-align: center;">#</th>
                            <th>Breach Type</th>
                            <th>Composite Key Data</th>
                            <th>Field</th>
                            <th style="text-align: right;">Source Value</th>
                            <th style="text-align: right;">Target Value</th>
                            <th style="text-align: right;">Difference</th>
                            <th>Diagnostic Message</th>
                        </tr>
                    </thead>
                    <tbody>
                        {exception_rows_html}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="footer">
            Generated automatically by Control Automation Service | HSBC Product Control Analytics &copy; 2026
        </div>
    </div>
</body>
</html>
"""
    return html_content


def generate_html_report_file(
    run_id: str,
    db: Session,
    output_dir: str = "reports"
) -> str:
    """
    Fetch run record and exceptions from database, generate HTML, and save to output directory.
    Returns generated file path.
    """
    run_record = db.query(ControlRunModel).filter(ControlRunModel.run_id == run_id).first()
    if not run_record:
        raise ValueError(f"Run ID '{run_id}' not found")

    exceptions = db.query(ControlExceptionModel).filter(
        ControlExceptionModel.run_id == run_id
    ).order_by(ControlExceptionModel.id).all()

    html = render_html_report(run_record, exceptions)

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    filename = f"report_{run_record.control_name}_{run_id[:8]}.html"
    file_full_path = out_path / filename

    with open(file_full_path, "w", encoding="utf-8") as f:
        f.write(html)

    return str(file_full_path)
