"""
UA Test v8.0 — Per-model CSV splitter.

The run writes all models into one combined CSV (the resume/git source of
truth). After each model finishes, this writes a derived per-model file into
`<reports>/by_model/` so results are also available split by model. Derived
files can always be regenerated from the combined CSV, so they never put the
run's data at risk.
"""
import csv
import re
from pathlib import Path


def safe_name(model_id):
    """Filesystem-safe slug for a model id."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", model_id)


def write_model_csv(combined_csv, model_id):
    """Extract all rows for `model_id` from the combined CSV into a per-model
    file under `by_model/`. Returns the output path."""
    combined = Path(combined_csv)
    out_dir = combined.parent / "by_model"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{combined.stem}__{safe_name(model_id)}.csv"

    with open(combined, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = [r for r in reader if r and r[0] == model_id]

    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return out
