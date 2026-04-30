"""
restore.py — Move photos from genre subdirectories back to the root input directory.

Use this before re-running the pipeline on a directory that was previously
organized with --organize, or to start fresh.

Usage:
    python src/restore.py --input-dir "F:/Disco2 PORTFOLIO/WebSIte/lr"
    python src/restore.py --input-dir "F:/Disco2 PORTFOLIO/WebSIte/lr" --dry-run
"""

import argparse
import os
import shutil
import sys

# Must match cli.py CATEGORY_DIRS exactly.
CATEGORY_DIRS = {
    "Street Photography",
    "Music Photography",
    "Nature Photography",
    "Portrait Photography",
    "Product Photography",
    "Wedding Photography",
    "Architecture Photography",
    "Event Photography",
    "Sports Photography",
    "Other Photography",
}


def restore(input_dir: str, dry_run: bool = False) -> None:
    if not os.path.isdir(input_dir):
        print(f"[ERROR] Directory not found: {input_dir}")
        sys.exit(1)

    moved = 0
    conflicts = 0
    removed_dirs = 0

    for cat_name in CATEGORY_DIRS:
        cat_dir = os.path.join(input_dir, cat_name)
        if not os.path.isdir(cat_dir):
            continue

        files = os.listdir(cat_dir)
        if not files:
            # Empty dir — remove it
            if not dry_run:
                os.rmdir(cat_dir)
            print(f"  Removed empty dir: {cat_name}/")
            removed_dirs += 1
            continue

        print(f"\n[{cat_name}] — {len(files)} file(s)")
        for fname in files:
            src = os.path.join(cat_dir, fname)
            if not os.path.isfile(src):
                continue
            dest = os.path.join(input_dir, fname)

            if os.path.exists(dest):
                # File with same name already exists in root — skip, warn
                print(f"  [CONFLICT] {fname} already exists in root — skipping")
                conflicts += 1
                continue

            print(f"  {fname}")
            if not dry_run:
                shutil.move(src, dest)
            moved += 1

        # Remove the category dir if now empty
        if not dry_run:
            remaining = os.listdir(cat_dir)
            if not remaining:
                os.rmdir(cat_dir)
                removed_dirs += 1
            else:
                print(f"  [WARNING] {cat_name}/ not empty after move "
                      f"({len(remaining)} file(s) remain — conflicts?)")

    print()
    if dry_run:
        print(f"[DRY RUN] Would move {moved} file(s), skip {conflicts} conflict(s).")
        print("Run without --dry-run to apply changes.")
    else:
        print(f"Done. Moved {moved} file(s), {conflicts} conflict(s) skipped, "
              f"{removed_dirs} dir(s) removed.")


def main():
    parser = argparse.ArgumentParser(
        prog="restore",
        description="Move photos from genre subdirs back to the root input directory.",
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory that was previously organized with --organize.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print what would happen without moving any files.",
    )
    args = parser.parse_args()
    restore(args.input_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
