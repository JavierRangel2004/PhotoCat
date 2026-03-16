"""
api_bridge.py -- Python JSON bridge for the Node migration.

This file does not move processing into Node. It only exposes existing Python
review/export/preview behavior through a small CLI contract that returns JSON.
"""

import argparse
import json
import os
import sys

from ui_state import UIState


def _load_state(csv_path: str, image_dir: str, corrections_path: str = "") -> UIState:
    state = UIState()
    msg = state.load_csv(csv_path, image_dir)
    if msg.startswith("File not found") or msg.startswith("Error") or msg.startswith("CSV missing"):
        raise RuntimeError(msg)

    if corrections_path:
        _apply_corrections(state, corrections_path)

    return state


def _apply_corrections(state: UIState, corrections_path: str) -> None:
    if not corrections_path or not os.path.isfile(corrections_path):
        return

    with open(corrections_path, "r", encoding="utf-8") as handle:
        corrections = json.load(handle)

    if state.base_df is None:
        return

    filename_to_index = {
        str(state.base_df.at[idx, "filename"]): idx for idx in state.base_df.index
    }

    for filename, payload in corrections.items():
        idx = filename_to_index.get(filename)
        if idx is None:
            continue
        user_genre = payload.get("user_genre", "")
        user_label = payload.get("user_label", "")
        if user_genre:
            state.base_df.at[idx, "user_genre"] = user_genre
        if user_label:
            state.base_df.at[idx, "user_label"] = user_label

    state._rebuild_visible()


def _session_payload(state: UIState, csv_path: str, image_dir: str) -> dict:
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
    for row_index in state.base_df.index:
        row = state.base_df.loc[row_index]
        filename = str(row.get("filename", ""))
        image_path = os.path.join(state.img_dir, filename)
        user_genre = str(row.get("user_genre", ""))
        final_genre = str(row.get("final_genre", ""))
        effective_genre = user_genre if user_genre else final_genre

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
            "filename": filename,
            "imagePath": image_path if os.path.isfile(image_path) else "",
            "imagePathDisplay": image_path,
            "finalGenre": final_genre,
            "effectiveGenre": effective_genre,
            "userGenre": user_genre,
            "userLabel": str(row.get("user_label", "")),
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

    args = parser.parse_args()

    try:
        state = _load_state(args.csv_path, args.image_dir, getattr(args, "corrections_path", ""))

        if args.command == "load-session":
            print(json.dumps(_session_payload(state, args.csv_path, args.image_dir)))
            return 0

        if args.command == "export-corrected":
            message = state.export_corrected_csv(args.output_path)
            print(json.dumps({
                "ok": True,
                "message": message,
                "csvPath": args.csv_path,
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

    print(json.dumps({"ok": False, "error": "Unsupported command"}))
    return 1


if __name__ == "__main__":
    sys.exit(main())
