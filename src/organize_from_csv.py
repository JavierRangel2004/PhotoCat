"""
organize_from_csv.py — Organize files into portfolio-ready directories from a corrected audit CSV.

This module reads a corrected CSV (the output of the Inspector review flow) and
moves files into Photo Portfolio-compatible category directories.  It never
re-runs classification; the CSV is the sole source of truth.

Usage from api_bridge.py or directly:

    from organize_from_csv import organize_preview, organize_commit, restore_from_manifest

    preview = organize_preview("corrected.csv", "/output/portfolio")
    result  = organize_commit("corrected.csv", "/output/portfolio")
    undone  = restore_from_manifest("/output/portfolio/photocat_manifest_20260317T120000.json")
"""

import csv
import hashlib
import json
import os
import posixpath
import shutil
from collections import defaultdict
from datetime import datetime, timezone

ORGANIZE_MODE_REPLACE = "replace"
ORGANIZE_MODE_APPEND_DEDUPE = "append_dedupe"

# Hash only likely photo/sidecar files when scanning the portfolio tree (skip huge non-media).
_HASH_EXTENSIONS = frozenset({
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".tif", ".tiff", ".heic", ".heif",
    ".bmp", ".cr2", ".cr3", ".nef", ".arw", ".dng", ".xmp",
})
_DEDUPE_SKIPPED_CAP = 500

try:
    from portfolio_mapping import PORTFOLIO_CATEGORIES
except ImportError:
    PORTFOLIO_CATEGORIES = [
        "portraits",
        "concert",
        "city",
        "nature",
        "product",
        "travel-cityscape",
    ]


REQUIRED_CORRECTED_COLUMNS = {
    "source_path",
    "filename",
    "effective_genre",
    "portfolio_category",
    "export_include",
    "dest_relpath",
}


def normalize_organize_mode(mode):
    """Normalize CLI/UI organize mode string."""
    m = (mode or ORGANIZE_MODE_REPLACE).strip().lower().replace("-", "_")
    if m == ORGANIZE_MODE_APPEND_DEDUPE:
        return ORGANIZE_MODE_APPEND_DEDUPE
    return ORGANIZE_MODE_REPLACE


def resolve_fs_path(path):
    """Resolve a user-supplied path to an absolute path independent of process cwd.

    Backslashes are normalized to slashes before abspath so pasted Windows-style
    paths on macOS/Linux resolve under /Users/... instead of relative to cwd.
    """
    if path is None or not str(path).strip():
        return ""
    s = str(path).strip().replace("\\", "/")
    s = os.path.expanduser(s)
    s = os.path.normpath(s)
    return os.path.abspath(s)


def _file_sha256(path, chunk_size=1024 * 1024):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _should_hash_file(path):
    ext = os.path.splitext(path)[1].lower()
    return ext in _HASH_EXTENSIONS


def _scan_existing_hashes(output_root):
    """Walk output_root and return dict sha256_hex -> list of posix-style relative paths."""
    result = defaultdict(list)
    if not output_root or not os.path.isdir(output_root):
        return dict(result)
    output_root = os.path.abspath(output_root)
    for dirpath, _dirnames, filenames in os.walk(output_root):
        for name in filenames:
            full = os.path.join(dirpath, name)
            if not os.path.isfile(full) or os.path.islink(full):
                continue
            if not _should_hash_file(full):
                continue
            try:
                digest = _file_sha256(full)
            except OSError:
                continue
            rel = os.path.relpath(full, output_root).replace("\\", "/")
            result[digest].append(rel)
    return dict(result)


def _unique_dest_path(dest_path, src_hash_hex):
    """Pick a non-existing path in the same directory using an 8-char hash suffix."""
    dest_dir = os.path.dirname(dest_path)
    base, ext = os.path.splitext(os.path.basename(dest_path))
    suffix = f"_{src_hash_hex[:8]}"
    candidate = os.path.join(dest_dir, f"{base}{suffix}{ext}")
    n = 0
    while os.path.exists(candidate):
        candidate = os.path.join(dest_dir, f"{base}{suffix}_{n}{ext}")
        n += 1
    return os.path.normpath(candidate)


def _append_dedupe_process_entries(entries, output_root):
    """Apply content dedupe / collision rename. entries need source_path, dest_path, filename.

    Returns (adjusted_entries, skipped_records, renamed_collision_count).
    """
    if not output_root:
        return list(entries), [], 0
    hash_map = _scan_existing_hashes(output_root)
    known_hashes = set(hash_map.keys())
    adjusted = []
    skipped = []
    renamed_collision = 0

    for entry in entries:
        src = entry.get("source_path", "")
        dest = entry.get("dest_path", "")
        if not src or not dest or not os.path.isfile(src):
            continue
        try:
            src_hash = _file_sha256(src)
        except OSError as exc:
            skipped.append({
                "source_path": src,
                "reason": f"hash_failed: {exc}",
                "existing_relpath": None,
            })
            continue

        if src_hash in known_hashes:
            rels = hash_map.get(src_hash, [])
            skipped.append({
                "source_path": src,
                "reason": "duplicate_content_in_portfolio",
                "existing_relpath": rels[0] if rels else None,
            })
            continue

        new_dest = dest
        if os.path.isfile(new_dest):
            try:
                dest_hash = _file_sha256(new_dest)
            except OSError:
                dest_hash = None
            if dest_hash == src_hash:
                rel = os.path.relpath(new_dest, output_root).replace("\\", "/")
                skipped.append({
                    "source_path": src,
                    "reason": "already_at_destination",
                    "existing_relpath": rel,
                })
                continue
            new_dest = _unique_dest_path(new_dest, src_hash)
            renamed_collision += 1

        new_entry = dict(entry)
        new_entry["dest_path"] = os.path.normpath(new_dest)
        new_entry["dest_relpath"] = os.path.relpath(new_dest, output_root).replace("\\", "/")
        adjusted.append(new_entry)
        known_hashes.add(src_hash)
        hash_map.setdefault(src_hash, []).append(new_entry["dest_relpath"])

    return adjusted, skipped, renamed_collision


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _read_csv_rows(csv_path):
    """Read the corrected CSV and return a list of row dicts."""
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _is_export_included(row):
    """Check whether a row should be included in the portfolio export."""
    value = str(row.get("export_include", "")).strip().lower()
    return value in ("true", "1", "yes")


def _xmp_sidecar_path(image_path):
    """Return the expected XMP sidecar path for an image, or None if it does not exist."""
    stem = os.path.splitext(image_path)[0]
    xmp_path = stem + ".xmp"
    if os.path.isfile(xmp_path):
        return xmp_path
    # Also check uppercase variant (Lightroom sometimes exports .XMP)
    xmp_upper = stem + ".XMP"
    if os.path.isfile(xmp_upper):
        return xmp_upper
    return None


def _manifest_filename():
    """Generate a timestamped manifest filename."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"photocat_manifest_{ts}.json"


def _validate_csv_contract(rows):
    """Return a list of corrected-CSV contract violations."""
    if not rows:
        return ["Corrected CSV is empty."]

    columns = set(rows[0].keys())
    missing_columns = sorted(REQUIRED_CORRECTED_COLUMNS - columns)
    errors = []
    if missing_columns:
        errors.append(
            "Corrected CSV is missing required columns: "
            + ", ".join(missing_columns)
        )
    return errors


def _normalize_dest_relpath(dest_relpath):
    """Normalize a relative destination path using forward slashes."""
    normalized = posixpath.normpath(str(dest_relpath or "").replace("\\", "/").strip())
    if normalized in ("", "."):
        return ""
    return normalized


def _resolve_dest_path(output_dir, dest_relpath):
    """Resolve a relative destination path and ensure it stays inside output_dir."""
    normalized_relpath = _normalize_dest_relpath(dest_relpath)
    if not normalized_relpath:
        return None, "Destination path is empty."
    if normalized_relpath.startswith("../") or normalized_relpath == "..":
        return None, "Destination path escapes the output root."
    if os.path.isabs(normalized_relpath):
        return None, "Destination path must be relative."

    output_root = os.path.abspath(output_dir)
    resolved = os.path.abspath(os.path.join(output_root, normalized_relpath))
    try:
        common_root = os.path.commonpath([output_root, resolved])
    except ValueError:
        return None, "Destination path escapes the output root."
    if common_root != output_root:
        return None, "Destination path escapes the output root."
    return resolved, ""


def _validate_dest_relpath(dest_relpath, portfolio_category, export_include):
    """Validate a corrected CSV destination against the portfolio contract."""
    normalized = _normalize_dest_relpath(dest_relpath)
    if not normalized:
        return normalized, "Destination path is empty."

    parts = normalized.split("/")
    if export_include:
        if len(parts) < 3 or parts[0] != "photos":
            return normalized, "Included rows must target photos/<category>/..."
        if portfolio_category not in PORTFOLIO_CATEGORIES:
            return normalized, f"Invalid portfolio category '{portfolio_category}'."
        if parts[1] != portfolio_category:
            return normalized, "Destination category does not match portfolio_category."
        return normalized, ""

    if len(parts) < 3 or parts[0] != "excluded":
        return normalized, "Excluded rows must target excluded/<genre>/..."
    return normalized, ""


def _build_move_plan(csv_path, output_dir):
    """Parse the corrected CSV and build the full move plan.

    Returns (moves, excluded, missing, errors, invalid_destinations, rows) where:
        moves: list of dicts for included files
        excluded: list of dicts for excluded files
        missing: list of dicts for files not found on disk
        errors: list of contract/path validation errors
        invalid_destinations: list of per-row destination validation errors
        rows: raw CSV rows (for diagnostics)
    """
    rows = _read_csv_rows(csv_path)
    moves = []
    excluded = []
    missing = []
    errors = _validate_csv_contract(rows)
    invalid_destinations = []

    for row in rows:
        source_path = row.get("source_path", "").strip()
        filename = row.get("filename", "").strip()
        effective_genre = row.get("effective_genre", "").strip()
        portfolio_category = row.get("portfolio_category", "").strip()
        include = _is_export_included(row)
        dest_relpath = row.get("dest_relpath", "").strip()
        normalized_relpath, validation_error = _validate_dest_relpath(
            dest_relpath,
            portfolio_category,
            include,
        )

        if not source_path:
            continue

        if validation_error:
            invalid_destinations.append({
                "source_path": source_path,
                "filename": filename,
                "dest_relpath": normalized_relpath or dest_relpath,
                "reason": validation_error,
            })
            continue

        dest_path, resolution_error = _resolve_dest_path(output_dir, normalized_relpath)
        if resolution_error:
            invalid_destinations.append({
                "source_path": source_path,
                "filename": filename,
                "dest_relpath": normalized_relpath,
                "reason": resolution_error,
            })
            continue

        # Check that the source file actually exists on disk
        if not os.path.isfile(source_path):
            missing.append({
                "source_path": source_path,
                "filename": filename,
            })
            continue

        if not include:
            excluded.append({
                "source_path": source_path,
                "filename": filename,
                "effective_genre": effective_genre,
                "portfolio_category": portfolio_category,
                "dest_relpath": normalized_relpath,
                "dest_path": os.path.normpath(dest_path),
            })
            continue

        moves.append({
            "source_path": source_path,
            "dest_path": os.path.normpath(dest_path),
            "dest_relpath": normalized_relpath,
            "portfolio_category": portfolio_category,
            "effective_genre": effective_genre,
            "filename": filename,
        })

    if invalid_destinations:
        errors.append(
            f"Detected {len(invalid_destinations)} invalid destination path(s)."
        )

    return moves, excluded, missing, errors, invalid_destinations, rows


def _detect_conflicts(moves):
    """Find destination paths that would receive more than one source file.

    Returns a list of {dest_path, sources: [source_path, ...]}.
    """
    dest_to_sources = defaultdict(list)
    for m in moves:
        dest_to_sources[m["dest_path"]].append(m["source_path"])

    conflicts = []
    for dest_path, sources in dest_to_sources.items():
        if len(sources) > 1:
            conflicts.append({
                "dest_path": dest_path,
                "sources": sources,
            })
    return conflicts


def _counts_by_category(moves):
    """Count files per portfolio category."""
    counts = defaultdict(int)
    for m in moves:
        cat = m.get("portfolio_category") or "unsorted"
        counts[cat] += 1
    return dict(counts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def organize_preview(csv_path, output_dir, mode=ORGANIZE_MODE_REPLACE):
    """Read corrected CSV and compute what would happen without moving anything.

    Returns dict:
        moves: list of {source_path, dest_path, portfolio_category, effective_genre}
        missing: list of {source_path, filename}
        conflicts: list of {dest_path, sources: [source_path, ...]}
        counts_by_category: dict[str, int]
        excluded_count: int
        total: int
        manifest_path_preview: str
    """
    mode_norm = normalize_organize_mode(mode)
    resolved_csv = resolve_fs_path(csv_path)
    resolved_out = resolve_fs_path(output_dir)
    moves, excluded, missing, errors, invalid_destinations, rows = _build_move_plan(
        resolved_csv, resolved_out
    )

    dedupe_skipped = []
    renamed_m = renamed_e = 0
    if mode_norm == ORGANIZE_MODE_APPEND_DEDUPE and not errors:
        moves, skipped_m, renamed_m = _append_dedupe_process_entries(moves, resolved_out)
        dedupe_skipped.extend(skipped_m)
        excluded_adj, skipped_e, renamed_e = _append_dedupe_process_entries(excluded, resolved_out)
        excluded = excluded_adj
        dedupe_skipped.extend(skipped_e)

    conflicts = _detect_conflicts(moves)
    counts = _counts_by_category(moves)
    manifest_preview = os.path.join(resolved_out, _manifest_filename())
    present_categories = sorted(counts.keys())

    return {
        "moves": moves,
        "missing": missing,
        "conflicts": conflicts,
        "counts_by_category": counts,
        "excluded_count": len(excluded),
        "total": len(rows),
        "manifest_path_preview": os.path.normpath(manifest_preview),
        "errors": errors,
        "invalid_destinations": invalid_destinations,
        "contract_valid": not errors,
        "allowed_photo_categories": list(PORTFOLIO_CATEGORIES),
        "present_photo_categories": present_categories,
        "resolved_output_dir": resolved_out,
        "resolved_csv_path": resolved_csv,
        "mode": mode_norm,
        "dedupe_new": len(moves),
        "dedupe_skipped_duplicate": len(dedupe_skipped),
        "dedupe_renamed_collision": renamed_m + renamed_e,
        "dedupe_skipped": dedupe_skipped[:_DEDUPE_SKIPPED_CAP],
        "dedupe_skipped_truncated": max(0, len(dedupe_skipped) - _DEDUPE_SKIPPED_CAP),
    }


def _move_one_entry(entry, dest_path, dry_run, manifest_moves, errors, is_excluded=False):
    """Move image + optional XMP; append manifest entry. Returns True if counted as moved."""
    label = "excluded " if is_excluded else ""
    dest_stem = os.path.splitext(os.path.basename(dest_path))[0]
    if not dry_run:
        try:
            dest_dir = os.path.dirname(dest_path)
            os.makedirs(dest_dir, exist_ok=True)
            shutil.move(entry["source_path"], dest_path)
            xmp_src = _xmp_sidecar_path(entry["source_path"])
            xmp_dest = None
            if xmp_src is not None:
                xmp_basename = dest_stem + os.path.splitext(xmp_src)[1]
                xmp_dest = os.path.join(dest_dir, xmp_basename)
                shutil.move(xmp_src, xmp_dest)
            manifest_moves.append({
                "source": entry["source_path"],
                "dest": dest_path,
                "xmp_source": xmp_src,
                "xmp_dest": xmp_dest,
            })
            return True
        except Exception as exc:
            errors.append(f"Failed to move {label}{entry['source_path']} -> {dest_path}: {exc}")
            return False
    xmp_src = _xmp_sidecar_path(entry["source_path"])
    xmp_dest = None
    if xmp_src is not None:
        xmp_basename = dest_stem + os.path.splitext(xmp_src)[1]
        xmp_dest = os.path.join(os.path.dirname(dest_path), xmp_basename)
    manifest_moves.append({
        "source": entry["source_path"],
        "dest": dest_path,
        "xmp_source": xmp_src,
        "xmp_dest": xmp_dest,
    })
    return True


def organize_commit(
    csv_path,
    output_dir,
    dry_run=False,
    include_excluded=True,
    mode=ORGANIZE_MODE_REPLACE,
):
    """Execute the organize: move files according to corrected CSV.

    Parameters:
        csv_path: Path to the corrected audit CSV.
        output_dir: Root directory for organized output.
        dry_run: If True, compute everything but do not move files.
        include_excluded: If True, move excluded files to output_dir/excluded/<genre>/.
                          If False, skip excluded files entirely.
        mode: replace (legacy) or append_dedupe (content-hash dedupe + collision rename).

    Returns dict:
        moved: int
        skipped: int
        missing: int
        conflicts: int
        manifest_path: str
        errors: list[str]
    """
    mode_norm = normalize_organize_mode(mode)
    resolved_csv = resolve_fs_path(csv_path)
    resolved_out = resolve_fs_path(output_dir)
    moves, excluded, missing, errors, invalid_destinations, rows = _build_move_plan(
        resolved_csv, resolved_out
    )
    errors = list(errors)
    excluded_rows_total = len(excluded)

    dedupe_skipped = []
    renamed_m = renamed_e = 0
    if mode_norm == ORGANIZE_MODE_APPEND_DEDUPE and not errors:
        moves, skipped_m, renamed_m = _append_dedupe_process_entries(moves, resolved_out)
        dedupe_skipped.extend(skipped_m)
        excluded, skipped_e, renamed_e = _append_dedupe_process_entries(excluded, resolved_out)
        dedupe_skipped.extend(skipped_e)

    conflicts = _detect_conflicts(moves)

    if invalid_destinations:
        errors.extend(
            [
                f"{entry['filename']}: {entry['reason']} ({entry['dest_relpath']})"
                for entry in invalid_destinations
            ]
        )
    if conflicts:
        errors.append("Resolve destination conflicts before commit.")

    conflicted_dests = {c["dest_path"] for c in conflicts}

    manifest_moves = []
    moved_count = 0
    skipped_count = excluded_rows_total
    conflict_count = 0

    manifest_path = os.path.join(resolved_out, _manifest_filename())

    base_result = {
        "resolved_output_dir": resolved_out,
        "resolved_csv_path": resolved_csv,
        "mode": mode_norm,
        "dedupe_new": len(moves),
        "dedupe_skipped_duplicate": len(dedupe_skipped),
        "dedupe_renamed_collision": renamed_m + renamed_e,
        "dedupe_skipped": dedupe_skipped[:_DEDUPE_SKIPPED_CAP],
        "dedupe_skipped_truncated": max(0, len(dedupe_skipped) - _DEDUPE_SKIPPED_CAP),
    }

    if errors:
        return {
            **base_result,
            "moved": 0,
            "skipped": skipped_count,
            "missing": len(missing),
            "conflicts": len(conflicts),
            "manifest_path": os.path.normpath(manifest_path),
            "errors": errors,
        }

    for m in moves:
        dest_path = m["dest_path"]
        if dest_path in conflicted_dests:
            conflict_count += 1
            continue
        if _move_one_entry(m, dest_path, dry_run, manifest_moves, errors, is_excluded=False):
            moved_count += 1

    excluded_moves = []
    if include_excluded:
        for ex in excluded:
            dest_path = ex["dest_path"]
            if _move_one_entry(ex, dest_path, dry_run, excluded_moves, errors, is_excluded=True):
                pass

    all_moves = manifest_moves + excluded_moves

    manifest_meta = {
        "csv_path": resolved_csv,
        "output_dir": resolved_out,
        "moved": moved_count,
        "excluded": len(excluded_moves),
        "missing": len(missing),
        "conflicts": conflict_count,
        "dry_run": dry_run,
        "organize_mode": mode_norm,
        "dedupe_skipped_duplicate": len(dedupe_skipped),
        "dedupe_renamed_collision": renamed_m + renamed_e,
        "dedupe_skipped": dedupe_skipped[:_DEDUPE_SKIPPED_CAP],
    }

    if not dry_run:
        os.makedirs(resolved_out, exist_ok=True)
        write_manifest(manifest_path, all_moves, manifest_meta)

    return {
        **base_result,
        "moved": moved_count,
        "skipped": skipped_count,
        "missing": len(missing),
        "conflicts": conflict_count,
        "manifest_path": os.path.normpath(manifest_path),
        "errors": errors,
    }


def write_manifest(manifest_path, moves, metadata):
    """Write a JSON manifest recording every file move for restore.

    Format:
    {
        "version": 1,
        "created_at": ISO timestamp,
        "csv_path": str,
        "output_dir": str,
        "moves": [
            {"source": str, "dest": str, "xmp_source": str|null, "xmp_dest": str|null}
        ],
        "summary": {moved, excluded, missing}
    }
    """
    manifest = {
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "csv_path": metadata.get("csv_path", ""),
        "output_dir": metadata.get("output_dir", ""),
        "moves": moves,
        "summary": {
            "moved": metadata.get("moved", 0),
            "excluded": metadata.get("excluded", 0),
            "missing": metadata.get("missing", 0),
        },
    }
    if metadata.get("organize_mode"):
        manifest["organize_mode"] = metadata["organize_mode"]
    if "dedupe_skipped_duplicate" in metadata:
        manifest["dedupe_skipped_duplicate"] = metadata["dedupe_skipped_duplicate"]
    if "dedupe_renamed_collision" in metadata:
        manifest["dedupe_renamed_collision"] = metadata["dedupe_renamed_collision"]
    if metadata.get("dedupe_skipped"):
        manifest["dedupe_skipped"] = metadata["dedupe_skipped"]

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def restore_from_manifest(manifest_path, dry_run=False):
    """Reverse all moves recorded in a manifest.

    Each entry in the manifest's "moves" list is reversed: the file at "dest"
    is moved back to "source".  XMP sidecars are restored the same way.

    Parameters:
        manifest_path: Path to a photocat_manifest_*.json file.
        dry_run: If True, report what would be restored without moving files.

    Returns dict:
        restored: int
        missing: int (dest files that no longer exist)
        errors: list[str]
    """
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    if manifest.get("version") != 1:
        return {
            "restored": 0,
            "missing": 0,
            "errors": [f"Unsupported manifest version: {manifest.get('version')}"],
        }

    moves = manifest.get("moves", [])
    restored = 0
    missing = 0
    errors = []

    # Reverse moves in reverse order (LIFO) to safely unwind nested moves
    for entry in reversed(moves):
        dest = entry.get("dest", "")
        source = entry.get("source", "")
        xmp_dest = entry.get("xmp_dest")
        xmp_source = entry.get("xmp_source")

        if not dest or not source:
            errors.append(f"Skipping entry with empty source or dest: {entry}")
            continue

        if not os.path.isfile(dest):
            missing += 1
            continue

        if not dry_run:
            try:
                # Ensure the original source directory still exists
                source_dir = os.path.dirname(source)
                os.makedirs(source_dir, exist_ok=True)

                shutil.move(dest, source)

                # Restore XMP sidecar if it was moved
                if xmp_dest and xmp_source and os.path.isfile(xmp_dest):
                    xmp_source_dir = os.path.dirname(xmp_source)
                    os.makedirs(xmp_source_dir, exist_ok=True)
                    shutil.move(xmp_dest, xmp_source)

                restored += 1
            except Exception as exc:
                errors.append(f"Failed to restore {dest} -> {source}: {exc}")
        else:
            restored += 1

    return {
        "restored": restored,
        "missing": missing,
        "errors": errors,
    }
