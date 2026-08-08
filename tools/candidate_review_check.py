"""Command-line check for Sprint 4.5 Patch 1 candidate review generation."""
from __future__ import annotations

import argparse
from pathlib import Path

from candidate_review import write_review_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a human-editable review file from PDC candidates.")
    parser.add_argument("candidates", help="Path to a __CANDIDATES.csv file")
    parser.add_argument("--output", help="Optional explicit output path")
    args = parser.parse_args()
    target = write_review_file(Path(args.candidates), Path(args.output) if args.output else None)
    print(f"Candidate review file written: {target}")
    print("No Parts Master records were modified or approved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
