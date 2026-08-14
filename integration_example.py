from candidate_review import CandidateReviewStore, review_candidates

# Example only: substitute the actual candidate list returned by Sprint 4.6.2a.
bom_item = {
    "VTPN": "70001234",
    "Description": "CAP CER 10UF 10V X5R 0603",
}

candidates_from_462a = [
    {
        "manufacturer": "Samsung Electro-Mechanics",
        "mpn": "CL10A106MP8NNNC",
        "aipn": "CAP-00010-00",
        "match_score": 96.5,
        "matched_attributes": ["capacitance=10uF", "package=0603"],
        "differences": ["tolerance: BOM unspecified, candidate ±20%"],
        "warnings": [],
        "justification": "Meets all known hard constraints.",
    }
]

review_rows = review_candidates(
    bom_item=bom_item,
    candidates=candidates_from_462a,
)

for row in review_rows:
    print(row)

store = CandidateReviewStore("data/reviews/candidate_reviews.jsonl")
store.record_candidate_decision(
    bom_item=bom_item,
    candidate=candidates_from_462a[0],
    decision="Needs Verification",
    reviewer="KL",
    comment="Confirm voltage rating from manufacturer source before acceptance.",
)
