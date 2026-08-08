"""Command-line runner for Sprint 4.4 Patch 3 qualified Knowledge Base population."""
from __future__ import annotations

import argparse
from pathlib import Path

from knowledge_base_population import (
    build_live_providers,
    populate_knowledge_base,
    write_population_outputs,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Populate the PDC Knowledge Base from a staging Parts Master CSV.")
    parser.add_argument("staging_csv", help="Path to the __STAGING.csv created by Sprint 4.4 Patch 1")
    parser.add_argument("--provider", action="append", choices=("DigiKey", "TME", "Mouser"),
                        help="Provider to run. Repeat to select more than one. Defaults to all three.")
    parser.add_argument("--limit", type=int, default=10,
                        help="Maximum staging records to process. Default 10. Use 0 for all records.")
    parser.add_argument("--force", action="store_true", help="Refresh even when current Knowledge Base data exists.")
    parser.add_argument("--knowledge-base", default="Knowledge_Base")
    parser.add_argument("--profiles", default="output/provider_profiles")
    parser.add_argument("--output", default="output/knowledge_base_population")
    args = parser.parse_args()

    providers = build_live_providers(args.knowledge_base, args.profiles, args.provider)
    print("=" * 68)
    print("PDC KNOWLEDGE BASE POPULATION")
    print("=" * 68)
    print(f"Staging file : {Path(args.staging_csv)}")
    print(f"Providers    : {', '.join(provider.name for provider in providers)}")
    print(f"Record limit : {'All' if args.limit == 0 else args.limit}")
    print(f"Force refresh: {'Yes' if args.force else 'No'}")
    print()

    run = populate_knowledge_base(
        args.staging_csv,
        providers,
        force=args.force,
        limit=args.limit,
        progress=True,
    )
    paths = write_population_outputs(run, args.output)
    summary = run.summary()
    print("\n" + "-" * 68)
    print("Run complete")
    print("-" * 68)
    for status, count in summary["status_counts"].items():
        print(f"{status:<20}: {count}")
    print("\nOutputs")
    for label, path in paths.items():
        print(f"{label:<10}: {path}")
    return 1 if summary["status_counts"].get("Provider Error", 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
