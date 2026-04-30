"""
api_bridge.py -- Python JSON bridge for the Node migration.

This file does not move processing into Node. It only exposes existing Python
review/export/preview behavior through a small CLI contract that returns JSON.
"""

import argparse
import json
import os
import sys

def _load_state(csv_path: str, image_dir: str, corrections_path: str = ""):
    from ui_state import UIState

    state = UIState()
    msg = state.load_csv(csv_path, image_dir)
    if msg.startswith("File not found") or msg.startswith("Error") or msg.startswith("CSV missing"):
        raise RuntimeError(msg)

    if corrections_path:
        _apply_corrections(state, corrections_path)

    return state


def _apply_corrections(state, corrections_path: str) -> None:
    if not corrections_path or not os.path.isfile(corrections_path):
        return

    with open(corrections_path, "r", encoding="utf-8") as handle:
        corrections = json.load(handle)

    if state.base_df is None:
        return

    # Use path-safe key lookup (falls back to filename for old CSVs)
    key_to_idx = state._build_key_to_idx()

    for key, payload in corrections.items():
        idx = key_to_idx.get(key)
        if idx is None:
            continue
        user_genre = payload.get("user_genre", "")
        user_label = payload.get("user_label", "")
        user_portfolio = payload.get("user_portfolio_category", "")
        if user_genre:
            state.base_df.at[idx, "user_genre"] = user_genre
        if user_label:
            state.base_df.at[idx, "user_label"] = user_label
        if user_portfolio and "user_portfolio_category" in state.base_df.columns:
            state.base_df.at[idx, "user_portfolio_category"] = user_portfolio

    state._rebuild_visible()


def _session_payload(state, csv_path: str, image_dir: str) -> dict:
    if state.base_df is None:
        return {
            "csvPath": csv_path,
            "imageDir": image_dir,
            "summary": {
                "total": 0,
                "auto": 0,
                "review": 0,
                "titleInferred": 0,
                "corrected": 0,
                "visible": 0,
                "genreCounts": {},
            },
            "genres": [],
            "statuses": [],
            "items": [],
        }

    items = []
    try:
        from portfolio_mapping import map_genre_to_portfolio, compute_dest_relpath
    except ImportError:
        map_genre_to_portfolio = None
        compute_dest_relpath = None

    for row_index in state.base_df.index:
        row = state.base_df.loc[row_index]
        filename = str(row.get("filename", ""))
        source_path = _clean(row.get("source_path", ""))
        relative_input_path = _clean(row.get("relative_input_path", ""))
        image_candidates = [
            source_path,
            os.path.join(state.img_dir, relative_input_path) if relative_input_path else "",
            os.path.join(state.img_dir, filename),
        ]
        image_path = next((candidate for candidate in image_candidates if candidate and os.path.isfile(candidate)), "")
        image_path_display = image_path or source_path or image_candidates[-1]
        user_genre = str(row.get("user_genre", ""))
        final_genre = str(row.get("final_genre", ""))
        effective_genre = user_genre if user_genre else final_genre
        user_portfolio_category = _clean(row.get("user_portfolio_category", ""))

        portfolio_category = ""
        portfolio_group = ""
        export_include = False
        dest_relpath = ""
        portfolio_needs_review = False
        portfolio_mapping_source = ""
        if map_genre_to_portfolio and compute_dest_relpath:
            portfolio = map_genre_to_portfolio(effective_genre, user_portfolio_category)
            portfolio_category = _clean(portfolio.get("portfolio_category", ""))
            portfolio_group = _clean(portfolio.get("portfolio_group", ""))
            export_include = bool(portfolio.get("export_include", False))
            dest_relpath = compute_dest_relpath(portfolio_category, filename, effective_genre=effective_genre)
            portfolio_needs_review = bool(portfolio.get("needs_review", False))
            portfolio_mapping_source = _clean(portfolio.get("mapping_source", ""))

        siglip_scores = []
        model_1st = str(row.get("model_1st", ""))
        model_1st_conf = row.get("model_1st_conf", None)
        model_2nd = str(row.get("model_2nd", ""))
        model_2nd_conf = row.get("model_2nd_conf", None)
        if model_1st:
            siglip_scores.append(f"{model_1st}: {model_1st_conf}")
        if model_2nd:
            siglip_scores.append(f"{model_2nd}: {model_2nd_conf}")

        evidence = row.get("evidence_log", "")
        if isinstance(evidence, str) and evidence.startswith("{"):
            try:
                evidence = json.dumps(json.loads(evidence), indent=2)
            except json.JSONDecodeError:
                pass

        items.append({
            "id": str(row_index),
            "rowKey": state._row_key(row_index),
            "filename": filename,
            "sourcePath": source_path,
            "relativeInputPath": relative_input_path,
            "imagePath": image_path,
            "imagePathDisplay": image_path_display,
            "finalGenre": final_genre,
            "effectiveGenre": effective_genre,
            "userGenre": user_genre,
            "userLabel": str(row.get("user_label", "")),
            "userPortfolioCategory": user_portfolio_category,
            "reviewStatus": str(row.get("review_status", "")),
            "rating": _clean(row.get("rating", "")),
            "isBlurry": _clean(row.get("is_blurry", "")),
            "exposure": _clean(row.get("exposure", "")),
            "caption": _clean(row.get("caption", "")),
            "objects": _clean(row.get("objects_detected", "")),
            "ocrText": _clean(row.get("ocr_text", "")),
            "siglipScores": siglip_scores,
            "evidence": str(evidence),
            "modelFirstConf": _to_number(model_1st_conf),
            "modelSecondConf": _to_number(model_2nd_conf),
            "portfolioCategory": portfolio_category,
            "portfolioGroup": portfolio_group,
            "exportInclude": export_include,
            "destRelpath": dest_relpath,
            "portfolioNeedsReview": portfolio_needs_review,
            "portfolioMappingSource": portfolio_mapping_source,
        })

    summary = state.get_summary()
    return {
        "csvPath": csv_path,
        "imageDir": image_dir,
        "summary": {
            "total": summary.get("total", 0),
            "auto": summary.get("auto", 0),
            "review": summary.get("review", 0),
            "titleInferred": summary.get("title_inferred", 0),
            "corrected": summary.get("corrected", 0),
            "visible": summary.get("visible", 0),
            "genreCounts": summary.get("genre_counts", {}),
        },
        "genres": state.get_unique_genres(),
        "statuses": state.get_unique_statuses(),
        "items": items,
    }


def _clean(value) -> str:
    text = str(value) if value is not None else ""
    return "" if text in ("nan", "NaN", "None") else text


def _to_number(value):
    try:
        if value in ("", None):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="PhotoCat Python bridge for Node frontend.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common_args(subparser):
        subparser.add_argument("--csv-path", required=True)
        subparser.add_argument("--image-dir", required=True)
        subparser.add_argument("--corrections-path", default="")

    load_session = subparsers.add_parser("load-session")
    add_common_args(load_session)

    export_corrected = subparsers.add_parser("export-corrected")
    add_common_args(export_corrected)
    export_corrected.add_argument("--output-path", default="")

    organize_preview = subparsers.add_parser("organize-preview")
    add_common_args(organize_preview)

    organize_csv_preview = subparsers.add_parser("organize-from-csv-preview")
    organize_csv_preview.add_argument("--csv-path", required=True)
    organize_csv_preview.add_argument("--output-dir", required=True)
    organize_csv_preview.add_argument(
        "--organize-mode",
        default="replace",
        help="replace (default) or append_dedupe",
    )

    organize_csv_commit = subparsers.add_parser("organize-from-csv-commit")
    organize_csv_commit.add_argument("--csv-path", required=True)
    organize_csv_commit.add_argument("--output-dir", required=True)
    organize_csv_commit.add_argument("--dry-run", action="store_true", default=False)
    organize_csv_commit.add_argument(
        "--include-excluded",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    organize_csv_commit.add_argument(
        "--organize-mode",
        default="replace",
        help="replace (default) or append_dedupe",
    )

    restore_manifest = subparsers.add_parser("restore-from-manifest")
    restore_manifest.add_argument("--manifest-path", required=True)
    restore_manifest.add_argument("--dry-run", action="store_true", default=False)

    args = parser.parse_args()

    ui_state_commands = {"load-session", "export-corrected", "organize-preview"}

    if args.command in ui_state_commands:
        try:
            state = _load_state(args.csv_path, args.image_dir, getattr(args, "corrections_path", ""))

            if args.command == "load-session":
                print(json.dumps(_session_payload(state, args.csv_path, args.image_dir)))
                return 0

            if args.command == "export-corrected":
                output_path = args.output_path or f"{os.path.splitext(args.csv_path)[0]}_corrected.csv"
                message = state.export_corrected_csv(output_path)
                print(json.dumps({
                    "ok": True,
                    "message": message,
                    "csvPath": args.csv_path,
                    "outputPath": output_path,
                }))
                return 0

            if args.command == "organize-preview":
                preview = state.get_organize_preview()
                print(json.dumps({
                    "ok": True,
                    "preview": preview,
                    "csvPath": args.csv_path,
                }))
                return 0

        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc)}))
            return 1

    # --- Commands that do NOT need UIState ---
    try:
        if args.command == "organize-from-csv-preview":
            from organize_from_csv import organize_preview as csv_preview
            result = csv_preview(
                args.csv_path,
                args.output_dir,
                mode=getattr(args, "organize_mode", "replace"),
            )
            print(json.dumps({"ok": True, **result}, default=str))
            return 0

        if args.command == "organize-from-csv-commit":
            from organize_from_csv import organize_commit as csv_commit
            result = csv_commit(
                args.csv_path,
                args.output_dir,
                dry_run=args.dry_run,
                include_excluded=args.include_excluded,
                mode=getattr(args, "organize_mode", "replace"),
            )
            ok = not result.get("errors")
            print(json.dumps({"ok": ok, **result}, default=str))
            return 0

        if args.command == "restore-from-manifest":
            from organize_from_csv import restore_from_manifest
            result = restore_from_manifest(args.manifest_path, dry_run=args.dry_run)
            ok = not result.get("errors")
            print(json.dumps({"ok": ok, **result}, default=str))
            return 0

    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1

    print(json.dumps({"ok": False, "error": "Unsupported command"}))
    return 1


if __name__ == "__main__":
    sys.exit(main())
