"""Generic raw-JSON inspection utility for provider onboarding."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterator


def iter_scalar_paths(value: Any, path: str = "$") -> Iterator[tuple[str, Any]]:
    if isinstance(value, dict):
        for key in sorted(value):
            yield from iter_scalar_paths(value[key], f"{path}.{key}")
    elif isinstance(value, list):
        if not value:
            yield path, []
        else:
            # Inspect one representative element so large arrays do not flood output.
            yield from iter_scalar_paths(value[0], f"{path}[0]")
    else:
        yield path, value


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect field paths in a raw provider JSON response.")
    parser.add_argument("json_file", type=Path)
    args = parser.parse_args()

    with args.json_file.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    for field_path, sample in iter_scalar_paths(payload):
        rendered = repr(sample)
        if len(rendered) > 120:
            rendered = rendered[:117] + "..."
        print(f"{field_path}: {rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
