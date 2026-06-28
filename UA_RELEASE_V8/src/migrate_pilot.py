"""
Seed a fresh run CSV with clean, complete domains from a prior run.

Reuses already-computed rows (same prompts/parsers => comparable) so the new
run skips them on resume and only tests the gaps. Only domains that are both
COMPLETE and ERROR-FREE are carried over; anything with ERROR rows or short
counts is left out so it gets re-run cleanly.

The prior CSV may have the old 11-column schema; rows are padded with an empty
`latency_s` to match the current 12-column header.

Usage:
    python3 migrate_pilot.py SOURCE_CSV DEST_CSV [--tier standard]
"""
import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ua_v8 import config  # noqa: E402
from ua_v8.domains import DOMAINS  # noqa: E402
from ua_v8.passport import expected_rows_for_domain  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("dest")
    ap.add_argument("--tier", default="standard", choices=config.TIERS.keys())
    args = ap.parse_args()

    mc_runs = config.TIERS[args.tier]["mc_runs"]
    src = Path(args.source)
    dest = Path(args.dest)
    if dest.exists():
        sys.exit(f"dest already exists, refusing to overwrite: {dest}")

    n_cols = len(config.CSV_HEADER)  # 12 (incl. latency_s)
    by_key = defaultdict(list)
    with open(src, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip old header
        for row in reader:
            if len(row) < 8:
                continue
            by_key[(row[0], row[1])].append(row)

    kept = []
    carried = []
    for (model, domain), rows in by_key.items():
        if domain not in DOMAINS:
            continue
        exp = expected_rows_for_domain(domain, mc_runs)
        ok = sum(1 for r in rows if r[7] != "ERROR")
        has_error = any(r[7] == "ERROR" for r in rows)
        if ok >= exp and not has_error:
            for r in rows:
                # pad/truncate to current schema (append empty latency_s)
                r = r[:n_cols] + [""] * (n_cols - len(r))
                kept.append(r[:n_cols])
            carried.append((model, domain, len(rows)))

    with open(dest, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(config.CSV_HEADER)
        w.writerows(kept)

    print(f"carried {len(carried)} clean domain(s), {len(kept)} rows -> {dest}")
    for m, d, n in sorted(carried):
        print(f"  {m:<28} {d:<20} {n} rows")


if __name__ == "__main__":
    main()
