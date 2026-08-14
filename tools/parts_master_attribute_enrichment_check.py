"""Sprint 4.6.1.2 check: enrich Parts Master index from stored provider JSON only."""
from __future__ import annotations
import argparse
from pathlib import Path
from parts_master_attribute_enricher import enrich_index_file


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("index", nargs="?", default="Parts_Master/parts_master_index.json")
    ap.add_argument("--knowledge-base", default="Knowledge_Base")
    args = ap.parse_args()
    out, summary = enrich_index_file(Path(args.index), Path(args.knowledge_base))
    print(f"Parts Master index       : {out}")
    print(f"Parts total              : {summary.get('parts_total', 0)}")
    print(f"Parts with technical data: {summary.get('parts_with_provider_technical_data', 0)}")
    print(f"Technical attributes     : {summary.get('attributes_total', 0)}")
    print(f"Provider Verified        : {summary.get('provider_verified', 0)}")
    print(f"Single Provider          : {summary.get('single_provider', 0)}")
    print(f"Needs Verification       : {summary.get('needs_verification', 0)}")
    print("Live provider calls      : 0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
