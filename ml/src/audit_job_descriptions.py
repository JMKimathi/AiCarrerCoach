"""Profile a large job-postings CSV without retaining contact or demographic fields.

Example:
  python ml/src/audit_job_descriptions.py "C:/Users/Mwiti/Downloads/Datasets/job_descriptions.csv"

The default is a bounded first-row scan. Pass --all-rows for a complete scan.
This script reports aggregate counts only and never copies source rows.
"""

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


REQUIRED_FIELDS = {"Role", "Country", "Job Posting Date", "skills"}


def audit(path: Path, max_rows: int | None) -> dict:
    role_counts: Counter[str] = Counter()
    country_counts: Counter[str] = Counter()
    type_counts: Counter[str] = Counter()
    years: Counter[str] = Counter()
    missing = Counter()
    rows_read = 0

    with path.open("r", encoding="utf-8-sig", newline="", errors="replace") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing_columns = sorted(REQUIRED_FIELDS - fields)
        if missing_columns:
            raise ValueError(f"Missing expected columns: {missing_columns}")

        for row in reader:
            if max_rows is not None and rows_read >= max_rows:
                break
            rows_read += 1
            role = (row.get("Role") or "").strip()
            country = (row.get("Country") or "").strip()
            work_type = (row.get("Work Type") or "").strip()
            date = (row.get("Job Posting Date") or "").strip()
            role_counts[role or "(missing)"] += 1
            country_counts[country or "(missing)"] += 1
            type_counts[work_type or "(missing)"] += 1
            years[date[:4] if len(date) >= 4 else "(missing)"] += 1
            for field in ("Job Description", "skills", "Responsibilities"):
                if not (row.get(field) or "").strip():
                    missing[field] += 1

    return {
        "file": path.name,
        "file_size_bytes": path.stat().st_size,
        "scan_scope": "complete file" if max_rows is None else f"first {max_rows:,} rows maximum; may not be representative",
        "rows_scanned": rows_read,
        "distinct_roles_scanned": len(role_counts) - int("(missing)" in role_counts),
        "top_roles": role_counts.most_common(30),
        "top_countries": country_counts.most_common(25),
        "kenya_rows_scanned": country_counts.get("Kenya", 0),
        "work_types": type_counts.most_common(20),
        "posting_years": sorted(years.items()),
        "missing_content_rows": dict(missing),
        "handling_note": "Only aggregate role, country, work type, date, and content-availability counts are retained. Contact, preference, company, salary, and profile fields are excluded.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--max-rows", type=int, default=50_000,
                        help="Bounded scan size; use --all-rows for a complete scan (default: 50000).")
    parser.add_argument("--all-rows", action="store_true", help="Scan the entire CSV file.")
    parser.add_argument("--output", type=Path, help="Optional JSON output path; otherwise print to stdout.")
    args = parser.parse_args()
    if not args.all_rows and args.max_rows < 1:
        parser.error("--max-rows must be a positive integer")
    result = audit(args.csv_path, None if args.all_rows else args.max_rows)
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Wrote aggregate audit to {args.output}")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
