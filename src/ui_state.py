"""
ui_state.py -- In-memory DataFrame state manager for PhotoCat Gradio UI.

Manages:
  - Base DataFrame loaded from audit CSV
  - Derived state: filters, sort order, visible subset, active index
  - Genre correction helpers (user_genre, user_label columns)
  - Autosave to temp JSON every N changes
  - Corrected CSV export
"""

import csv
import json
import os
import tempfile
from pathlib import Path

import pandas as pd

# All taxonomy categories used across the pipeline (Phase 2 — JRMGraphy aligned)
GENRE_CATEGORIES = [
    "Branding & Portrait",
    "Events & Music",
    "Street Documentary",
    "Food & Product",
    "Nature & Landscape",
    "Travel & Architecture",
    "Other Photography",
    "Wedding Photography",
]

_AUTOSAVE_INTERVAL = 10  # save temp file every N corrections


class UIState:
    """Central state for the Gradio UI.

    Separation:
      - base_df: full DataFrame loaded from CSV (plus user_genre, user_label cols)
      - Derived: filter_genre, filter_status, filter_max_conf, sort_col, sort_asc,
                 visible_indices (list of base_df row indices matching current filters),
                 active_idx (position within visible_indices for Inspector navigation)
    """

    def __init__(self):
        self.base_df: pd.DataFrame | None = None
        self.csv_path: str = ""
        self.img_dir: str = ""  # directory containing the images

        # Derived filter state
        self.filter_genre: str = "All"
        self.filter_status: str = "All"
        self.filter_max_conf: float = 1.0
        self.sort_col: str = "filename"
        self.sort_asc: bool = True

        # Visible subset (list of integer indices into base_df)
        self.visible_indices: list[int] = []

        # Inspector position within visible_indices
        self.active_idx: int = 0

        # Change counter for autosave
        self._change_count: int = 0
        self._autosave_path: str = ""

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------
    def load_csv(self, csv_path: str, img_dir: str = "") -> str:
        """Load an audit CSV into base_df. Returns status message."""
        if not os.path.isfile(csv_path):
            return f"File not found: {csv_path}"

        try:
            df = pd.read_csv(csv_path, encoding="utf-8")
        except Exception as e:
            return f"Error reading CSV: {e}"

        if "filename" not in df.columns:
            return "CSV missing required 'filename' column."

        # Clean NaN values — replace with empty string for display
        str_cols = [c for c in df.columns if df[c].dtype == object]
        df[str_cols] = df[str_cols].fillna("")
        # Numeric NaN stays as-is for filtering, but we'll handle on display

        # Add correction columns if not present
        if "user_genre" not in df.columns:
            df["user_genre"] = ""
        if "user_label" not in df.columns:
            df["user_label"] = ""
        if "user_portfolio_category" not in df.columns:
            df["user_portfolio_category"] = ""

        self.base_df = df
        self.csv_path = csv_path
        self.img_dir = img_dir or str(Path(csv_path).parent)

        # Setup autosave path
        self._autosave_path = os.path.join(
            tempfile.gettempdir(),
            f"photocat_autosave_{os.path.basename(csv_path)}.json",
        )
        self._change_count = 0

        # Try restoring autosave
        restored = self._restore_autosave()

        # Reset filters and rebuild visible set
        self.filter_genre = "All"
        self.filter_status = "All"
        self.filter_max_conf = 1.0
        self.active_idx = 0
        self._rebuild_visible()

        n = len(df)
        msg = f"Loaded {n} images from {os.path.basename(csv_path)}"
        if restored:
            msg += f" (restored {restored} corrections from autosave)"
        return msg

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------
    def apply_filters(
        self,
        genre: str = "All",
        status: str = "All",
        max_conf: float = 1.0,
        sort_col: str = "filename",
        sort_asc: bool = True,
    ) -> None:
        """Update filter state and rebuild visible_indices."""
        self.filter_genre = genre
        self.filter_status = status
        self.filter_max_conf = max_conf
        self.sort_col = sort_col
        self.sort_asc = sort_asc
        self.active_idx = 0
        self._rebuild_visible()

    def _rebuild_visible(self) -> None:
        """Recompute visible_indices from base_df + current filters."""
        if self.base_df is None:
            self.visible_indices = []
            return

        df = self.base_df
        mask = pd.Series([True] * len(df), index=df.index)

        if self.filter_genre != "All":
            # Use user_genre override if set, else final_genre
            effective = df["user_genre"].where(df["user_genre"] != "", df.get("final_genre", ""))
            mask &= effective == self.filter_genre

        if self.filter_status != "All":
            if "review_status" in df.columns:
                mask &= df["review_status"] == self.filter_status

        if self.filter_max_conf < 1.0 and "model_1st_conf" in df.columns:
            conf = pd.to_numeric(df["model_1st_conf"], errors="coerce").fillna(0)
            mask &= conf <= self.filter_max_conf

        filtered = df[mask]

        # Sort
        col = self.sort_col if self.sort_col in filtered.columns else "filename"
        try:
            filtered = filtered.sort_values(col, ascending=self.sort_asc)
        except TypeError:
            pass

        self.visible_indices = filtered.index.tolist()

    # ------------------------------------------------------------------
    # Table data
    # ------------------------------------------------------------------
    def get_table_data(self) -> list[list]:
        """Return table rows for visible subset (for gr.Dataframe)."""
        if self.base_df is None:
            return []

        cols = ["filename", "review_status", "final_genre", "user_genre", "model_1st_conf", "user_label"]
        available = [c for c in cols if c in self.base_df.columns]

        rows = []
        for idx in self.visible_indices:
            row = [str(self.base_df.at[idx, c]) if c in self.base_df.columns else "" for c in available]
            rows.append(row)
        return rows

    def get_table_headers(self) -> list[str]:
        cols = ["filename", "review_status", "final_genre", "user_genre", "model_1st_conf", "user_label"]
        if self.base_df is None:
            return cols
        return [c for c in cols if c in self.base_df.columns]

    # ------------------------------------------------------------------
    # Gallery thumbnails
    # ------------------------------------------------------------------
    def get_gallery_paths(self) -> list[tuple[str, str]]:
        """Return (image_path, caption) tuples for visible subset.

        Also builds _gallery_idx_map so gallery click index maps back
        to the correct position in visible_indices.
        """
        if self.base_df is None:
            self._gallery_idx_map = []
            return []

        items = []
        self._gallery_idx_map = []  # gallery_position -> visible_indices position
        for vis_pos, idx in enumerate(self.visible_indices):
            fname = str(self.base_df.at[idx, "filename"])
            full = os.path.join(self.img_dir, fname)
            if os.path.isfile(full):
                items.append((full, fname))
                self._gallery_idx_map.append(vis_pos)
        return items

    def gallery_index_to_visible(self, gallery_idx: int) -> int:
        """Convert a gallery click index to the corresponding visible_indices position."""
        if hasattr(self, "_gallery_idx_map") and 0 <= gallery_idx < len(self._gallery_idx_map):
            return self._gallery_idx_map[gallery_idx]
        return gallery_idx

    # ------------------------------------------------------------------
    # Summary stats
    # ------------------------------------------------------------------
    def get_summary(self) -> dict:
        """Return summary stats for the loaded CSV."""
        if self.base_df is None:
            return {}

        df = self.base_df
        total = len(df)

        status_counts = {}
        if "review_status" in df.columns:
            status_counts = df["review_status"].value_counts().to_dict()

        genre_counts = {}
        if "final_genre" in df.columns:
            genre_counts = df["final_genre"].value_counts().to_dict()

        corrected = int((df["user_genre"] != "").sum())

        return {
            "total": total,
            "auto": status_counts.get("auto", 0),
            "review": status_counts.get("review", 0),
            "title_inferred": status_counts.get("title-inferred", 0),
            "genre_counts": genre_counts,
            "corrected": corrected,
            "visible": len(self.visible_indices),
        }

    def format_summary(self) -> str:
        """Return a human-readable summary string."""
        s = self.get_summary()
        if not s:
            return "No data loaded."

        lines = [
            f"{s['total']} images | {s['auto']} auto | {s['review']} review | {s['title_inferred']} title-inferred",
            f"{s['corrected']} user corrections | {s['visible']} visible (filtered)",
        ]
        genre_parts = [f"{g} {n}" for g, n in sorted(s["genre_counts"].items(), key=lambda x: -x[1])]
        if genre_parts:
            lines.append(" | ".join(genre_parts))
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Inspector: get row data
    # ------------------------------------------------------------------
    def get_inspector_data(self, position: int | None = None) -> dict:
        """Return full data for the image at the given position in visible_indices."""
        if self.base_df is None or not self.visible_indices:
            return {"empty": True}

        if position is not None:
            self.active_idx = max(0, min(position, len(self.visible_indices) - 1))

        idx = self.visible_indices[self.active_idx]
        row = self.base_df.loc[idx]

        # Resolve image path
        fname = str(row.get("filename", ""))
        img_path = os.path.join(self.img_dir, fname)

        # Parse evidence log if JSON
        evidence = row.get("evidence_log", "")
        if isinstance(evidence, str) and evidence.startswith("{"):
            try:
                evidence = json.loads(evidence)
            except json.JSONDecodeError:
                pass

        # SigLIP scores from model columns
        siglip_scores = []
        m1 = row.get("model_1st", "")
        c1 = row.get("model_1st_conf", "")
        m2 = row.get("model_2nd", "")
        c2 = row.get("model_2nd_conf", "")
        if m1:
            siglip_scores.append(f"{m1}: {c1}")
        if m2:
            siglip_scores.append(f"{m2}: {c2}")

        # Effective genre (user override or model)
        user_genre = str(row.get("user_genre", ""))
        final_genre = str(row.get("final_genre", ""))
        effective_genre = user_genre if user_genre else final_genre

        def _clean(val):
            """Convert value to string, replacing NaN/nan with empty."""
            s = str(val) if val is not None else ""
            return "" if s in ("nan", "NaN", "None") else s

        return {
            "empty": False,
            "filename": fname,
            "img_path": img_path if os.path.isfile(img_path) else "",
            "img_path_display": img_path,  # always show the resolved path for debugging
            "rating": _clean(row.get("rating", "")),
            "is_blurry": _clean(row.get("is_blurry", "")),
            "exposure": _clean(row.get("exposure", "")),
            "caption": _clean(row.get("caption", "")),
            "objects": _clean(row.get("objects_detected", "")),
            "ocr_text": _clean(row.get("ocr_text", "")),
            "siglip_scores": "\n".join(siglip_scores),
            "evidence": json.dumps(evidence, indent=2) if isinstance(evidence, dict) else str(evidence),
            "final_genre": final_genre,
            "user_genre": user_genre,
            "effective_genre": effective_genre,
            "review_status": str(row.get("review_status", "")),
            "user_label": str(row.get("user_label", "")),
            "position": self.active_idx,
            "total_visible": len(self.visible_indices),
            "row_index": int(idx),
        }

    def inspector_next(self) -> dict:
        return self.get_inspector_data(self.active_idx + 1)

    def inspector_prev(self) -> dict:
        return self.get_inspector_data(self.active_idx - 1)

    # ------------------------------------------------------------------
    # Genre correction
    # ------------------------------------------------------------------
    def set_user_genre(self, genre: str) -> str:
        """Set user_genre for the currently active Inspector image."""
        if self.base_df is None or not self.visible_indices:
            return "No data loaded."

        idx = self.visible_indices[self.active_idx]
        self.base_df.at[idx, "user_genre"] = genre
        self._on_change()
        fname = self.base_df.at[idx, "filename"]
        return f"Set genre to '{genre}' for {fname}"

    def set_user_label(self, label: str) -> str:
        """Set user_label ('correct' or 'wrong') for the currently active image."""
        if self.base_df is None or not self.visible_indices:
            return "No data loaded."

        idx = self.visible_indices[self.active_idx]
        self.base_df.at[idx, "user_label"] = label
        self._on_change()
        fname = self.base_df.at[idx, "filename"]
        return f"Marked '{label}' for {fname}"

    # ------------------------------------------------------------------
    # Row key helpers
    # ------------------------------------------------------------------
    def _row_key(self, idx) -> str:
        """Return a stable row key.  Prefer source_path > relative_input_path > filename."""
        if self.base_df is None:
            return ""
        row = self.base_df.loc[idx]
        sp = str(row.get("source_path", ""))
        if sp and sp not in ("", "nan", "NaN", "None"):
            return sp
        rp = str(row.get("relative_input_path", ""))
        if rp and rp not in ("", "nan", "NaN", "None"):
            return rp
        return str(row.get("filename", ""))

    def _build_key_to_idx(self) -> dict:
        """Build a mapping from row key -> DataFrame index for correction lookups."""
        if self.base_df is None:
            return {}
        mapping = {}
        for idx in self.base_df.index:
            key = self._row_key(idx)
            mapping[key] = idx
            # Also index by filename as fallback for backward-compat
            fname = str(self.base_df.at[idx, "filename"])
            if fname not in mapping:
                mapping[fname] = idx
        return mapping

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def export_corrected_csv(self, output_path: str = "") -> str:
        """Write corrected CSV with materialized organizing columns."""
        if self.base_df is None:
            return "No data to export."

        if not output_path:
            base = os.path.splitext(self.csv_path)[0]
            output_path = f"{base}_corrected.csv"

        # Materialize derived columns before export
        self._materialize_organizing_columns()

        self.base_df.to_csv(output_path, index=False, encoding="utf-8")
        n_corrected = int((self.base_df["user_genre"] != "").sum())
        return f"Exported {len(self.base_df)} rows ({n_corrected} corrected) to {output_path}"

    def _materialize_organizing_columns(self) -> None:
        """Compute effective_genre, portfolio_category, portfolio_group, export_include, dest_relpath."""
        if self.base_df is None:
            return

        try:
            from portfolio_mapping import map_genre_to_portfolio, compute_dest_relpath
        except ImportError:
            # portfolio_mapping not yet available — skip materialization
            return

        df = self.base_df

        # effective_genre: user override wins
        ug = df["user_genre"].fillna("")
        fg = df["final_genre"].fillna("") if "final_genre" in df.columns else pd.Series("", index=df.index)
        df["effective_genre"] = ug.where(ug != "", fg)

        # user_portfolio_category may have been set in the review UI
        if "user_portfolio_category" not in df.columns:
            df["user_portfolio_category"] = ""
        upc = df["user_portfolio_category"].fillna("")

        portfolio_cats = []
        portfolio_groups = []
        export_includes = []
        dest_relpaths = []

        for idx in df.index:
            eg = str(df.at[idx, "effective_genre"])
            upc_val = str(upc.at[idx]) if upc.at[idx] else ""
            fname = str(df.at[idx, "filename"])

            result = map_genre_to_portfolio(eg, user_portfolio_category=upc_val)
            portfolio_cats.append(result["portfolio_category"])
            portfolio_groups.append(result["portfolio_group"])
            export_includes.append(result["export_include"])
            dest_relpaths.append(compute_dest_relpath(
                result["portfolio_category"], fname, effective_genre=eg,
            ))

        df["portfolio_category"] = portfolio_cats
        df["portfolio_group"] = portfolio_groups
        df["export_include"] = export_includes
        df["dest_relpath"] = dest_relpaths

    # ------------------------------------------------------------------
    # Autosave
    # ------------------------------------------------------------------
    def _on_change(self) -> None:
        """Track changes and autosave periodically."""
        self._change_count += 1
        if self._change_count % _AUTOSAVE_INTERVAL == 0:
            self._autosave()

    def _autosave(self) -> None:
        """Save user corrections to a temp JSON file, keyed by path-safe row key."""
        if self.base_df is None or not self._autosave_path:
            return

        corrections = {}
        for idx in self.base_df.index:
            ug = self.base_df.at[idx, "user_genre"]
            ul = self.base_df.at[idx, "user_label"]
            upc = self.base_df.at[idx, "user_portfolio_category"] if "user_portfolio_category" in self.base_df.columns else ""
            if ug or ul or upc:
                key = self._row_key(idx)
                entry = {"user_genre": ug, "user_label": ul}
                if upc:
                    entry["user_portfolio_category"] = upc
                corrections[key] = entry

        if corrections:
            try:
                with open(self._autosave_path, "w", encoding="utf-8") as f:
                    json.dump(corrections, f, indent=2)
            except OSError:
                pass

    def _restore_autosave(self) -> int:
        """Restore corrections from autosave if it exists. Returns count restored."""
        if not self._autosave_path or not os.path.isfile(self._autosave_path):
            return 0
        if self.base_df is None:
            return 0

        try:
            with open(self._autosave_path, "r", encoding="utf-8") as f:
                corrections = json.load(f)
        except (OSError, json.JSONDecodeError):
            return 0

        count = 0
        key_to_idx = self._build_key_to_idx()
        for key, corr in corrections.items():
            if key in key_to_idx:
                idx = key_to_idx[key]
                if corr.get("user_genre"):
                    self.base_df.at[idx, "user_genre"] = corr["user_genre"]
                    count += 1
                if corr.get("user_label"):
                    self.base_df.at[idx, "user_label"] = corr["user_label"]
                if corr.get("user_portfolio_category") and "user_portfolio_category" in self.base_df.columns:
                    self.base_df.at[idx, "user_portfolio_category"] = corr["user_portfolio_category"]
        return count

    def clear_autosave(self) -> None:
        """Remove the autosave file (e.g. after successful export)."""
        if self._autosave_path and os.path.isfile(self._autosave_path):
            try:
                os.remove(self._autosave_path)
            except OSError:
                pass

    # ------------------------------------------------------------------
    # Organize helpers
    # ------------------------------------------------------------------
    def get_organize_preview(self) -> dict | str:
        """Return a preview of what organize would do with corrections applied.

        Returns a structured dict when portfolio_mapping is available,
        otherwise falls back to a plain text summary for backward compat.
        """
        if self.base_df is None:
            return "No data loaded."

        from collections import Counter

        # Try structured preview via portfolio mapping
        try:
            from portfolio_mapping import map_genre_to_portfolio, compute_dest_relpath
            return self._structured_organize_preview()
        except ImportError:
            pass

        # Fallback: plain text summary
        plan = Counter()
        override_count = 0

        for idx in self.base_df.index:
            ug = self.base_df.at[idx, "user_genre"]
            fg = self.base_df.at[idx, "final_genre"] if "final_genre" in self.base_df.columns else ""
            genre = ug if ug else fg
            if genre:
                plan[genre] += 1
                if ug:
                    override_count += 1

        total = sum(plan.values())
        lines = [f"Would organize {total} image(s) into {len(plan)} folder(s):"]
        lines.append(f"  ({override_count} using user-corrected genre)\n")
        for genre, n in plan.most_common():
            lines.append(f"  {genre}/  ({n} files)")
        return "\n".join(lines)

    def _structured_organize_preview(self) -> dict:
        """Build a structured organize preview using portfolio mapping."""
        from portfolio_mapping import map_genre_to_portfolio, compute_dest_relpath
        from collections import Counter

        df = self.base_df
        moves = []
        excluded = []
        missing = []
        needs_review = 0
        counts_by_category = Counter()
        dest_paths = Counter()

        for idx in df.index:
            ug = str(df.at[idx, "user_genre"] or "")
            fg = str(df.at[idx, "final_genre"]) if "final_genre" in df.columns else ""
            eg = ug if ug else fg
            upc = str(df.at[idx, "user_portfolio_category"] or "") if "user_portfolio_category" in df.columns else ""
            fname = str(df.at[idx, "filename"])
            source = str(df.at[idx, "source_path"]) if "source_path" in df.columns else os.path.join(self.img_dir, fname)

            result = map_genre_to_portfolio(eg, user_portfolio_category=upc)
            dest_rel = compute_dest_relpath(result["portfolio_category"], fname, effective_genre=eg)

            if not os.path.isfile(source):
                missing.append({"source_path": source, "filename": fname})
                continue

            if result["needs_review"]:
                needs_review += 1

            entry = {
                "source_path": source,
                "filename": fname,
                "effective_genre": eg,
                "portfolio_category": result["portfolio_category"],
                "dest_relpath": dest_rel,
                "export_include": result["export_include"],
            }

            if result["export_include"]:
                moves.append(entry)
                counts_by_category[result["portfolio_category"]] += 1
                dest_paths[dest_rel] += 1
            else:
                excluded.append(entry)

        conflicts = [
            {"dest_relpath": path, "count": count}
            for path, count in dest_paths.items() if count > 1
        ]

        return {
            "moves": len(moves),
            "excluded": len(excluded),
            "missing": missing,
            "conflicts": conflicts,
            "needs_review": needs_review,
            "counts_by_category": dict(counts_by_category),
            "total": len(df),
        }

    def get_unique_genres(self) -> list[str]:
        """Return sorted list of unique genres found in the CSV."""
        if self.base_df is None or "final_genre" not in self.base_df.columns:
            return GENRE_CATEGORIES
        found = set(self.base_df["final_genre"].dropna().unique())
        # Also include any user-corrected genres
        if "user_genre" in self.base_df.columns:
            found |= set(self.base_df["user_genre"][self.base_df["user_genre"] != ""].unique())
        return sorted(found)

    def get_unique_statuses(self) -> list[str]:
        """Return unique review statuses found in CSV."""
        if self.base_df is None or "review_status" not in self.base_df.columns:
            return ["auto", "review", "title-inferred"]
        return sorted(self.base_df["review_status"].dropna().unique().tolist())
