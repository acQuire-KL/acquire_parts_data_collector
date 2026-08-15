from __future__ import annotations

import argparse
import json
from pathlib import Path

from candidate_review import CandidateReviewStore
from review_queue import build_review_queue, build_review_summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect current PDC candidate-review queue state."
    )
    parser.add_argument(
        "review_file",
        type=Path,
        help="Path to candidate_reviews.jsonl created by Sprint 4.6.2b.",
    )
    args = parser.parse_args()

    store = CandidateReviewStore(args.review_file)
    summary = build_review_summary(store)
    queue = build_review_queue(store)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    for item in queue:
        marker = "ATTENTION" if item.needs_attention else "OK"
        print(f"{marker:9} {item.bom_item_key}: {item.item_status}")
        for candidate in item.candidates:
            score = "" if candidate.score is None else f"{candidate.score:.1f}"
            print(
                f"  - {candidate.decision:18} "
                f"{candidate.manufacturer} {candidate.mpn} "
                f"score={score}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
