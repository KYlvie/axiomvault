from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def build_report(*, file_id: str, filename: str, extracted_text: str, analysis: dict) -> dict:
    preview = extracted_text[:5000]
    return {
        "meta": {
            "file_id": file_id,
            "filename": filename,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "text_preview_len": len(preview),
            "text_total_len": len(extracted_text),
        },
        "analysis": analysis,
        "text_preview": preview,
    }


def save_report(output_dir: str | Path, report: dict) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    file_id = report.get("meta", {}).get("file_id", "unknown")
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_id = f"{file_id}_{ts}"

    json_path = out / f"report_{report_id}.json"
    md_path = out / f"report_{report_id}.md"

    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_to_markdown(report), encoding="utf-8")

    return {
        "report_id": report_id,
        "json_path": str(json_path),
        "md_path": str(md_path),
    }


def _to_markdown(report: dict) -> str:
    meta = report.get("meta", {})
    analysis = report.get("analysis", {})
    findings = analysis.get("findings", [])

    lines: list[str] = []
    lines.append("# AxiomVault Report")
    lines.append("")
    lines.append("## Meta")
    lines.append("")
    lines.append(f"- file_id: {meta.get('file_id','')}")
    lines.append(f"- filename: {meta.get('filename','')}")
    lines.append(f"- generated_at: {meta.get('generated_at','')}")
    lines.append(f"- text_total_len: {meta.get('text_total_len','')}")
    lines.append("")
    lines.append("## Contradiction Analysis")
    lines.append("")
    lines.append(f"- sentences: {analysis.get('sentences', 0)}")
    lines.append(f"- findings: {len(findings)}")
    lines.append("")
    lines.append("### Findings")
    lines.append("")
    if not findings:
        lines.append("_No obvious contradictions found by heuristic analyzer._")
        lines.append("")
        return "\n".join(lines)

    for idx, f in enumerate(findings, start=1):
        lines.append(f"#### {idx}")
        lines.append("")
        lines.append(f"- reason: {f.get('reason','')}")
        lines.append("")
        lines.append("**A**")
        lines.append("")
        lines.append(f"> {str(f.get('a','')).strip()}")
        lines.append("")
        lines.append("**B**")
        lines.append("")
        lines.append(f"> {str(f.get('b','')).strip()}")
        lines.append("")
    return "\n".join(lines)

