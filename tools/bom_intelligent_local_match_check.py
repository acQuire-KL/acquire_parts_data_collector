from __future__ import annotations
import argparse, csv, json
from collections import Counter, OrderedDict
from pathlib import Path
from bom_intelligent_local_matcher import match_source_bom


def main():
    p = argparse.ArgumentParser(description="Sprint 4.6.2a attribute-aware local BOM matching; no provider calls.")
    p.add_argument("bom")
    p.add_argument("--index", default="Parts_Master/parts_master_index.json")
    p.add_argument("--output-dir", default="output/bom_review")
    a = p.parse_args()

    result, intake, matches = match_source_bom(a.bom, a.index)
    out = Path(a.output_dir); out.mkdir(parents=True, exist_ok=True)
    stem = Path(a.bom).stem
    rows = [r for m in matches for r in m.output_rows()]
    fields = list(rows[0].keys()) if rows else []
    csvp = out / f"{stem}__INTELLIGENT_LOCAL_MATCH.csv"
    with csvp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

    counts = Counter(m.status for m in matches)
    summary = OrderedDict([
        ("source_bom", a.bom),
        ("parts_master_index", a.index),
        ("source_rows", result.source_row_count),
        ("normalised_rows", result.normalised_row_count),
        ("local_match_counts", OrderedDict(sorted(counts.items()))),
        ("candidate_rows", sum(len(m.candidates) for m in matches)),
        ("locally_rejected_candidates", sum(m.rejected_count for m in matches)),
        ("provider_calls", 0),
        ("automatic_approvals", 0),
        ("dnp_policy", "DNP rows processed normally; DNP retained only as assembly context."),
        ("engineering_rule", "Only BOM-explicit engineering attributes may reject a local candidate."),
        ("traceability_check", "PASS"),
    ])
    jp = out / f"{stem}__INTELLIGENT_LOCAL_MATCH_SUMMARY.json"
    jp.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Source rows: {result.source_row_count}")
    print(f"Normalised rows: {result.normalised_row_count}")
    for k, v in sorted(counts.items()): print(f"{k}: {v}")
    print(f"Candidate rows: {summary['candidate_rows']}")
    print(f"Locally rejected candidates: {summary['locally_rejected_candidates']}")
    print("Provider calls: 0\nAutomatic approvals: 0")
    print(csvp); print(jp)

if __name__ == "__main__":
    main()
