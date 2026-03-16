"""
ui.py -- PhotoCat Gradio UI entry point.

Three-tab interface:
  Tab 1: Run Pipeline — configure and run the batch pipeline with live log
  Tab 2: Review Table — load CSV, filter, browse thumbnails, export corrections
  Tab 3: Image Inspector — full image + evidence + genre correction dropdown

Usage:
    python src/ui.py
    python src/ui.py --browser
"""

import argparse
import os
import sys

import gradio as gr

# Ensure src/ is on the path so sibling modules can be imported
sys.path.insert(0, os.path.dirname(__file__))

from ui_state import UIState, GENRE_CATEGORIES
from ui_runner import PipelineRunner

# ---------- Singletons ----------
state = UIState()
runner = PipelineRunner()


# =====================================================================
# TAB 1: Run Pipeline
# =====================================================================

def run_pipeline(
    input_dir, csv_output, recursive, write_xmp, genre_only,
    no_cache, organize, dry_run, min_conf, workers, extensions,
):
    """Generator: run the pipeline subprocess and stream log lines."""
    if not input_dir or not os.path.isdir(input_dir):
        yield "Invalid input directory.", "", "Ready"
        return

    if not csv_output:
        csv_output = os.path.join(input_dir, "photocat_audit.csv")

    cmd = runner.build_command(
        input_dir=input_dir,
        csv_path=csv_output,
        recursive=recursive,
        write_xmp=write_xmp,
        genre_only=genre_only,
        no_cache=no_cache,
        organize=organize,
        dry_run=dry_run,
        min_confidence=min_conf,
        workers=int(workers),
        extensions=extensions,
    )

    log_text = ""
    for line, cur, tot in runner.run(cmd):
        log_text += line
        progress_str = f"{cur}/{tot}" if tot > 0 else "..."
        yield log_text, progress_str, runner.get_status()

    yield log_text, f"{runner.progress}/{runner.total}", runner.get_status()


def stop_pipeline():
    return runner.stop()


# =====================================================================
# TAB 2: Review Table
# =====================================================================

def load_csv_action(csv_path, img_dir):
    """Load CSV and return table data + summary + gallery + filter dropdown updates."""
    if not img_dir:
        img_dir = os.path.dirname(os.path.abspath(csv_path)) if csv_path else ""

    # Register this path with Gradio's allowed_paths so it can serve the files
    _register_allowed_path(img_dir)

    msg = state.load_csv(csv_path, img_dir)
    summary = state.format_summary()
    table = state.get_table_data()
    gallery = state.get_gallery_paths()
    genres = ["All"] + state.get_unique_genres()
    statuses = ["All"] + state.get_unique_statuses()

    return (
        msg,
        summary,
        table,
        gallery,
        gr.update(choices=genres, value="All"),
        gr.update(choices=statuses, value="All"),
        img_dir,  # echo back to the source path field
    )


def update_source_path(new_path):
    """Change the image source directory and refresh gallery + inspector."""
    new_path = new_path.strip()
    empty_inspector = _build_inspector_outputs()

    if not new_path:
        return ("No path provided.", []) + empty_inspector

    if not os.path.isdir(new_path):
        return (f"Directory not found: {new_path}", []) + empty_inspector

    _register_allowed_path(new_path)
    state.img_dir = new_path
    gallery = state.get_gallery_paths()
    found = len(gallery)
    total = len(state.visible_indices) if state.base_df is not None else 0
    msg = f"Image source: {new_path} ({found}/{total} images found)"
    inspector = _build_inspector_outputs()
    return (msg, gallery) + inspector


def _register_allowed_path(path):
    """Add a directory to the running Gradio app's allowed_paths at runtime."""
    if not path:
        return
    abs_path = os.path.abspath(path)
    # Gradio stores allowed_paths on the Blocks instance; we also need parent dirs
    # for paths with spaces. We add the exact dir.
    import gradio.utils
    if hasattr(gradio.utils, 'is_in_or_equal'):
        # Gradio 4+ / 6+ — add to the global set that _check_allowed reads
        pass
    # The safest approach: add to the app's allowed_paths list which is checked
    # by processing_utils._check_allowed
    _EXTRA_ALLOWED_PATHS.add(abs_path)


# Paths registered at runtime — passed to launch()
_EXTRA_ALLOWED_PATHS: set[str] = set()


def apply_filters_action(genre, status_filter, max_conf, sort_col, sort_asc):
    """Apply filters and return updated table + gallery."""
    # Guard: if Gradio passes unexpected types, coerce to string
    genre = str(genre) if genre else "All"
    status_filter = str(status_filter) if status_filter else "All"

    asc = sort_asc == "Ascending"
    state.apply_filters(
        genre=genre,
        status=status_filter,
        max_conf=max_conf,
        sort_col=sort_col,
        sort_asc=asc,
    )
    table = state.get_table_data()
    gallery = state.get_gallery_paths()
    summary = state.format_summary()
    return table, gallery, summary


def export_csv_action():
    """Export corrected CSV."""
    msg = state.export_corrected_csv()
    state.clear_autosave()
    return msg


def organize_preview_action():
    """Show dry-run preview of organize."""
    return state.get_organize_preview()


def gallery_select_action(evt: gr.SelectData):
    """When user clicks a gallery thumbnail, navigate Inspector to that image."""
    if evt.index is not None:
        # Map gallery index (which skips missing files) to visible_indices position
        vis_pos = state.gallery_index_to_visible(evt.index)
        state.active_idx = vis_pos
    return _build_inspector_outputs()


# =====================================================================
# TAB 3: Image Inspector
# =====================================================================

def _build_inspector_outputs():
    """Build all Inspector component values from current state."""
    d = state.get_inspector_data()

    if d.get("empty"):
        return (
            None,       # image
            "",         # filename
            "",         # rating
            "",         # blur
            "",         # exposure
            "",         # caption
            "",         # objects
            "",         # ocr
            "",         # siglip scores
            "",         # evidence
            gr.update(value=None),  # genre dropdown — None to avoid invalid empty string
            "",         # review status
            "",         # user label
            "0 / 0",   # nav label
        )

    nav = f"{d['position'] + 1} / {d['total_visible']}"

    # Show full resolved path so user can verify; fall back to bare filename
    display_path = d.get("img_path_display", "") or d["filename"]

    return (
        d["img_path"] if d["img_path"] else None,
        display_path,
        d["rating"],
        d["is_blurry"],
        d["exposure"],
        d["caption"],
        d["objects"],
        d["ocr_text"],
        d["siglip_scores"],
        d["evidence"],
        d["effective_genre"],
        d["review_status"],
        d["user_label"],
        nav,
    )


def inspector_next():
    state.inspector_next()
    return _build_inspector_outputs()


def inspector_prev():
    state.inspector_prev()
    return _build_inspector_outputs()


def inspector_set_genre(genre):
    if not genre:
        return ("",) + _build_inspector_outputs()
    msg = state.set_user_genre(genre)
    outputs = _build_inspector_outputs()
    return (msg,) + outputs


def inspector_confirm():
    msg = state.set_user_label("correct")
    outputs = _build_inspector_outputs()
    return (msg,) + outputs


def inspector_mark_wrong():
    msg = state.set_user_label("wrong")
    outputs = _build_inspector_outputs()
    return (msg,) + outputs


# =====================================================================
# BUILD UI
# =====================================================================

def build_ui():
    with gr.Blocks(title="PhotoCat") as app:
        gr.Markdown("# PhotoCat")

        with gr.Tabs():
            # =============================================================
            # TAB 1: RUN PIPELINE
            # =============================================================
            with gr.Tab("Run Pipeline"):
                with gr.Row():
                    input_dir = gr.Textbox(
                        label="Input Directory",
                        value="images",
                        scale=3,
                    )
                    csv_output = gr.Textbox(
                        label="CSV Output Path",
                        value="",
                        placeholder="(auto: <input-dir>/photocat_audit.csv)",
                        scale=2,
                    )

                with gr.Group():
                    gr.Markdown("### Pipeline Flags")
                    with gr.Row():
                        recursive = gr.Checkbox(label="--recursive", value=False)
                        write_xmp = gr.Checkbox(label="--write-xmp", value=False)
                        genre_only = gr.Checkbox(label="--genre-only", value=False)
                    with gr.Row():
                        no_cache = gr.Checkbox(label="--no-cache", value=False)
                        organize = gr.Checkbox(label="--organize", value=False)
                        dry_run = gr.Checkbox(label="--dry-run", value=False)

                    with gr.Row():
                        min_conf = gr.Slider(
                            minimum=0.3, maximum=0.95, value=0.55, step=0.05,
                            label="Min Confidence",
                        )
                        workers = gr.Dropdown(
                            choices=["1", "2", "4"], value="1",
                            label="Workers",
                        )
                        extensions = gr.Textbox(
                            label="Extensions",
                            value=".jpg,.jpeg,.png,.tiff,.webp,.cr2,.dng",
                        )

                with gr.Row():
                    run_btn = gr.Button("Run Pipeline", variant="primary")
                    stop_btn = gr.Button("Stop", variant="stop")

                run_status = gr.Textbox(label="Status", value="Ready", interactive=False)
                run_progress = gr.Textbox(label="Progress", value="", interactive=False)
                run_log = gr.Textbox(
                    label="Live Log",
                    lines=20,
                    max_lines=40,
                    interactive=False,
                    autoscroll=True,
                )

                # (wiring done after all tabs are defined)

            # =============================================================
            # TAB 2: REVIEW TABLE
            # =============================================================
            with gr.Tab("Review Table"):
                with gr.Row():
                    csv_path_input = gr.Textbox(
                        label="CSV Path",
                        value="output/full_audit.csv",
                        scale=3,
                    )
                    load_btn = gr.Button("Load CSV", variant="primary")

                with gr.Group():
                    gr.Markdown("### Image Source Path")
                    with gr.Row():
                        img_dir_input = gr.Textbox(
                            label="Folder containing the actual image files (filenames in CSV are resolved relative to this)",
                            value="",
                            placeholder=r"e.g. F:\Photos\export  or  /home/user/photos",
                            scale=4,
                        )
                        update_path_btn = gr.Button("Update Path", scale=1)

                load_msg = gr.Textbox(label="Status", interactive=False)
                summary_text = gr.Textbox(label="Summary", lines=3, interactive=False)

                with gr.Row():
                    filter_genre = gr.Dropdown(
                        choices=["All"] + GENRE_CATEGORIES,
                        value="All",
                        label="Filter Genre",
                    )
                    filter_status = gr.Dropdown(
                        choices=["All", "auto", "review", "title-inferred"],
                        value="All",
                        label="Filter Status",
                    )
                    filter_conf = gr.Slider(
                        minimum=0.0, maximum=1.0, value=1.0, step=0.05,
                        label="Max Confidence (show below)",
                    )
                with gr.Row():
                    sort_col = gr.Dropdown(
                        choices=["filename", "final_genre", "model_1st_conf", "review_status"],
                        value="filename", label="Sort By",
                    )
                    sort_dir = gr.Dropdown(
                        choices=["Ascending", "Descending"],
                        value="Ascending", label="Sort Direction",
                    )
                    filter_btn = gr.Button("Apply Filters")

                gallery = gr.Gallery(
                    label="Image Grid (click to inspect)",
                    columns=6,
                    height=300,
                    object_fit="cover",
                )

                review_table = gr.Dataframe(
                    headers=["filename", "review_status", "final_genre", "user_genre", "model_1st_conf", "user_label"],
                    interactive=False,
                    wrap=True,
                    label="Audit Table (read-only — edit genre in Inspector tab)",
                )

                with gr.Row():
                    export_btn = gr.Button("Export Corrected CSV", variant="primary")
                    organize_btn = gr.Button("Preview Organize")
                export_msg = gr.Textbox(label="Export Status", interactive=False)
                organize_preview = gr.Textbox(
                    label="Organize Preview", lines=8, interactive=False,
                )

                # (wiring done after all tabs are defined)

            # =============================================================
            # TAB 3: IMAGE INSPECTOR
            # =============================================================
            with gr.Tab("Image Inspector"):
                with gr.Row():
                    with gr.Column(scale=3):
                        insp_image = gr.Image(
                            label="Preview",
                            type="filepath",
                            height=500,
                        )
                        with gr.Row():
                            prev_btn = gr.Button("< Prev")
                            nav_label = gr.Textbox(
                                value="0 / 0", label="Position",
                                interactive=False, scale=1,
                            )
                            next_btn = gr.Button("Next >")

                    with gr.Column(scale=2):
                        insp_filename = gr.Textbox(label="File", interactive=False)
                        with gr.Row():
                            insp_rating = gr.Textbox(label="Rating", interactive=False, scale=1)
                            insp_blur = gr.Textbox(label="Blur", interactive=False, scale=1)
                            insp_exposure = gr.Textbox(label="Exposure", interactive=False, scale=1)

                        insp_caption = gr.Textbox(label="BLIP Caption", lines=2, interactive=False)
                        insp_objects = gr.Textbox(label="YOLO Objects", interactive=False)
                        insp_ocr = gr.Textbox(label="OCR Text", lines=2, interactive=False)
                        insp_siglip = gr.Textbox(label="SigLIP Scores", lines=2, interactive=False)
                        insp_evidence = gr.Textbox(label="Evidence Log", lines=3, interactive=False)
                        insp_status = gr.Textbox(label="Review Status", interactive=False)
                        insp_label_display = gr.Textbox(label="User Label", interactive=False)

                        gr.Markdown("### Correct Genre")
                        genre_dropdown = gr.Dropdown(
                            choices=GENRE_CATEGORIES,
                            label="Assigned Genre",
                            allow_custom_value=False,
                        )
                        with gr.Row():
                            confirm_btn = gr.Button("Confirm Correct", variant="primary")
                            wrong_btn = gr.Button("Mark Wrong", variant="stop")
                        action_msg = gr.Textbox(label="Action", interactive=False)

                # All inspector outputs in order
                inspector_outputs = [
                    insp_image, insp_filename, insp_rating, insp_blur,
                    insp_exposure, insp_caption, insp_objects, insp_ocr,
                    insp_siglip, insp_evidence, genre_dropdown, insp_status,
                    insp_label_display, nav_label,
                ]
                inspector_outputs_with_msg = [action_msg] + inspector_outputs

        # =============================================================
        # EVENT WIRING (after all tabs so cross-tab refs work)
        # =============================================================

        # Tab 1: Run
        run_btn.click(
            run_pipeline,
            inputs=[
                input_dir, csv_output, recursive, write_xmp, genre_only,
                no_cache, organize, dry_run, min_conf, workers, extensions,
            ],
            outputs=[run_log, run_progress, run_status],
        )
        stop_btn.click(stop_pipeline, outputs=[run_status])

        # Tab 2: Load CSV
        load_btn.click(
            load_csv_action,
            inputs=[csv_path_input, img_dir_input],
            outputs=[load_msg, summary_text, review_table, gallery,
                     filter_genre, filter_status, img_dir_input],
        )

        # Tab 2: Update image source path
        update_path_btn.click(
            update_source_path,
            inputs=[img_dir_input],
            outputs=[load_msg, gallery] + inspector_outputs,
        )

        # Tab 2: Filters
        filter_btn.click(
            apply_filters_action,
            inputs=[filter_genre, filter_status, filter_conf, sort_col, sort_dir],
            outputs=[review_table, gallery, summary_text],
        )

        # Tab 2: Export + organize
        export_btn.click(export_csv_action, outputs=[export_msg])
        organize_btn.click(organize_preview_action, outputs=[organize_preview])

        # Tab 3: Gallery click -> inspector
        gallery.select(gallery_select_action, outputs=inspector_outputs)

        # Tab 3: Navigation
        prev_btn.click(inspector_prev, outputs=inspector_outputs)
        next_btn.click(inspector_next, outputs=inspector_outputs)

        # Tab 3: Genre correction
        genre_dropdown.change(
            inspector_set_genre,
            inputs=[genre_dropdown],
            outputs=inspector_outputs_with_msg,
        )
        confirm_btn.click(inspector_confirm, outputs=inspector_outputs_with_msg)
        wrong_btn.click(inspector_mark_wrong, outputs=inspector_outputs_with_msg)

    return app


# =====================================================================
# MAIN
# =====================================================================

def main():
    parser = argparse.ArgumentParser(description="PhotoCat Gradio UI")
    parser.add_argument("--browser", action="store_true", help="Auto-open browser")
    parser.add_argument("--port", type=int, default=7860, help="Server port")
    args = parser.parse_args()

    app = build_ui()

    # Build allowed_paths: since the user can point to any local directory,
    # we allow common root paths. This is safe because share=False (local only).
    allowed = list(_EXTRA_ALLOWED_PATHS)
    if sys.platform == "win32":
        # Allow all mounted drive letters
        import string as _string
        for letter in _string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.isdir(drive):
                allowed.append(drive)
    else:
        allowed.append("/")

    app.launch(
        server_name="127.0.0.1",
        server_port=args.port,
        inbrowser=args.browser,
        share=False,
        theme=gr.themes.Soft(),
        allowed_paths=allowed,
    )


if __name__ == "__main__":
    main()
