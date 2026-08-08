from __future__ import annotations

import argparse
from pathlib import Path

from knowledge_promotion import write_knowledge_outputs


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Promote completed candidate reviews into the immutable PDC Knowledge History."
    )
    parser.add_argument("review_file", help="Completed __CANDIDATE_REVIEW.csv file")
    parser.add_argument("--output-dir", help="Optional output folder")
    args = parser.parse_args()

    paths = write_knowledge_outputs(args.review_file, args.output_dir)
    print("PDC Knowledge Promotion - Sprint 4.5 Patch 2b")
    print("=" * 52)
    print(f"Review file : {Path(args.review_file)}")
    for name, path in paths.items():
        print(f"{name.replace('_', ' ').title():22}: {path}")
    print("\nKnowledge is stored once; current views are derived from Knowledge History.")
    print("No Parts Master was modified and no AIPNs were allocated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
