from __future__ import annotations

import argparse

from candidate_review import CandidateReviewStore
from engineering_action_handoff import proposals_from_current_acceptances


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Preview controlled engineering-action handoffs."
    )
    parser.add_argument(
        "review_file",
        help="candidate_reviews.jsonl created by Sprint 4.6.2b",
    )
    args = parser.parse_args()

    store = CandidateReviewStore(args.review_file)
    proposals = proposals_from_current_acceptances(review_store=store)

    if not proposals:
        print("No current Accepted candidate reviews available for handoff.")
        return 0

    for proposal in proposals:
        print(
            f"{proposal.bom_item_key}: "
            f"{proposal.manufacturer} {proposal.mpn} -> "
            f"{proposal.proposed_action.value}"
        )
        print(f"  {proposal.action_reason}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
