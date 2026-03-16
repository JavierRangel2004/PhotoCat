"""
audit_summary.py — Quick review of a PhotoCat audit CSV.

Usage:
    python src/audit_summary.py output/audit.csv
    python src/audit_summary.py output/audit.csv --review-only
    python src/audit_summary.py output/audit.csv --genre "Portrait Photography"
"""

import argparse
import csv
import sys
from collections import Counter, defaultdict


def load(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def print_summary(rows):
    status_counts = Counter(r["review_status"] for r in rows)
    genre_counts = Counter(r["final_genre"] for r in rows)

    print(f"\n{'='*52}")
    print(f"  Audit summary — {len(rows)} images")
    print(f"{'='*52}")

    print("\nStatus breakdown:")
    for s in ("auto", "review", "title-inferred"):
        n = status_counts.get(s, 0)
        bar = "#" * (n // 3)
        print(f"  {s:<16} {n:>4}  {bar}")

    print("\nGenre breakdown:")
    for genre, n in genre_counts.most_common():
        bar = "#" * (n // 2)
        print(f"  {genre:<26} {n:>4}  {bar}")

    # Confidence stats per genre
    print("\nAverage model confidence per genre:")
    conf_by_genre = defaultdict(list)
    for r in rows:
        try:
            conf_by_genre[r["final_genre"]].append(float(r["model_1st_conf"]))
        except (ValueError, KeyError):
            pass
    for genre, confs in sorted(conf_by_genre.items(), key=lambda x: -sum(x[1])/len(x[1])):
        avg = sum(confs) / len(confs)
        low = min(confs)
        print(f"  {genre:<26} avg={avg:.2f}  min={low:.2f}  n={len(confs)}")


def print_review_rows(rows, genre_filter=None):
    targets = [r for r in rows if r["review_status"] != "auto"]
    if genre_filter:
        targets = [r for r in targets if r["final_genre"] == genre_filter]

    if not targets:
        print("No review/title-inferred rows" + (f" for genre '{genre_filter}'" if genre_filter else "") + ".")
        return

    label = f"genre='{genre_filter}'" if genre_filter else "all genres"
    print(f"\n{'='*72}")
    print(f"  Needs review — {len(targets)} images ({label})")
    print(f"{'='*72}")
    print(f"  {'File':<28} {'Status':<16} {'Genre':<26} {'Conf':>5}  {'Top-2 alternative'}")
    print(f"  {'-'*28} {'-'*16} {'-'*26} {'-'*5}  {'-'*24}")
    for r in targets:
        conf = r.get("model_1st_conf", "")
        try:
            conf_str = f"{float(conf):.2f}"
        except ValueError:
            conf_str = conf
        alt = f"{r.get('model_2nd','')} ({r.get('model_2nd_conf','')})"
        print(f"  {r['filename']:<28} {r['review_status']:<16} {r['final_genre']:<26} {conf_str:>5}  {alt}")


def main():
    parser = argparse.ArgumentParser(description="Summarise a PhotoCat audit CSV.")
    parser.add_argument("csv_path", help="Path to the audit CSV file.")
    parser.add_argument("--review-only", action="store_true",
                        help="Show only rows that need review (non-auto).")
    parser.add_argument("--genre", default=None,
                        help="Filter review rows to a specific genre name.")
    args = parser.parse_args()

    try:
        rows = load(args.csv_path)
    except FileNotFoundError:
        print(f"File not found: {args.csv_path}")
        sys.exit(1)

    if not args.review_only:
        print_summary(rows)

    if args.review_only or args.genre:
        print_review_rows(rows, genre_filter=args.genre)
    else:
        # Always show the review list after summary
        print_review_rows(rows)


if __name__ == "__main__":
    main()
