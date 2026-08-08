"""Compare flattened JSON field paths during provider onboarding."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def collect_paths(value: Any, path: str = "$") -> set[str]:
    paths: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            paths.add(child_path)
            paths.update(collect_paths(child, child_path))
    elif isinstance(value, list):
        list_path = f"{path}[]"
        paths.add(list_path)
        if value:
            paths.update(collect_paths(value[0], list_path))
    return paths


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare JSON field coverage for provider onboarding.")
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    args = parser.parse_args()

    left_paths = collect_paths(load_json(args.left))
    right_paths = collect_paths(load_json(args.right))

    print(f"Only in {args.left.name}")
    for item in sorted(left_paths - right_paths):
        print(f"  {item}")

    print(f"\nOnly in {args.right.name}")
    for item in sorted(right_paths - left_paths):
        print(f"  {item}")

    print("\nSummary")
    print(f"  {args.left.name}: {len(left_paths)} paths")
    print(f"  {args.right.name}: {len(right_paths)} paths")
    print(f"  Shared: {len(left_paths & right_paths)} paths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
