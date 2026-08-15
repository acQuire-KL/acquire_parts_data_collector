from __future__ import annotations

import argparse
import json
from pathlib import Path

from datasheet_acquisition import acquire_datasheet, acquisition_result_to_dict


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Acquire one datasheet into the PDC static evidence archive."
    )
    parser.add_argument("url", help="Distributor or manufacturer datasheet URL")
    parser.add_argument("--via", required=True, help="Discovery provider name")
    parser.add_argument(
        "--source-type",
        default="DISTI",
        choices=["DISTI", "MFG"],
        help="How the URL was discovered",
    )
    parser.add_argument("--manufacturer", required=True)
    parser.add_argument("--manufacturer-domain", action="append", required=True)
    parser.add_argument("--mpn", required=True)
    parser.add_argument("--archive-root", default="datasheets")
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = parser.parse_args()

    result = acquire_datasheet(
        discovery_url=args.url,
        discovered_via=args.via,
        discovery_source_type=args.source_type,
        manufacturer_name=args.manufacturer,
        manufacturer_domains=args.manufacturer_domain,
        mpn=args.mpn,
        archive_root=Path(args.archive_root),
        retrieved_date=args.date,
    )
    print(json.dumps(acquisition_result_to_dict(result), indent=2))
    return 0 if result.evidence else 1


if __name__ == "__main__":
    raise SystemExit(main())
