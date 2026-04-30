"""
ui.py -- PhotoCat Gradio UI entry point.

Three-tab interface:
  Tab 1: Run Pipeline - configure and run the batch pipeline with live log
  Tab 2: Review Table - load CSV, filter, browse thumbnails, export corrections
  Tab 3: Image Inspector - full image + evidence + genre correction workflow

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


UI_CSS = """
:root {
  --pc-surface: rgba(255, 251, 245, 0.9);
  --pc-surface-strong: #fffdf8;
  --pc-ink: #1f1a17;
  --pc-muted: #6f6257;
  --pc-border: rgba(102, 83, 61, 0.16);
  --pc-accent: #9a4f2f;
  --pc-accent-strong: #7f3518;
  --pc-shadow: 0 18px 50px rgba(39, 26, 17, 0.08);
}

.gradio-container {
  background:
    radial-gradient(circle at top left, rgba(154, 79, 47, 0.12), transparent 28%),
    radial-gradient(circle at top right, rgba(40, 89, 67, 0.08), transparent 26%),
    linear-gradient(180deg, #f8f3eb 0%, #efe8dc 100%);
  color: var(--pc-ink);
}

#photocat-shell {
  max-width: 1500px;
  margin: 0 auto;
  padding: 20px 18px 36px;
}

#hero-banner {
  margin-bottom: 16px;
  padding: 24px 28px;
  border: 1px solid var(--pc-border);
  border-radius: 28px;
  background:
    linear-gradient(135deg, rgba(255,255,255,0.82), rgba(255,248,240,0.9)),
    linear-gradient(120deg, rgba(154,79,47,0.08), rgba(40,89,67,0.06));
  box-shadow: var(--pc-shadow);
}

#hero-banner h1 {
  margin: 0;
  font-size: 2.5rem;
  line-height: 1;
  letter-spacing: -0.04em;
}

#hero-banner p {
  margin: 10px 0 0;
  max-width: 860px;
  color: var(--pc-muted);
  font-size: 1rem;
}

#hero-meta {
  margin-top: 14px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

#hero-meta span {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255,255,255,0.7);
  border: 1px solid var(--pc-border);
  font-size: 0.85rem;
  color: var(--pc-ink);
}

.panel,
.workflow-card {
  border: 1px solid var(--pc-border);
  border-radius: 22px;
  background: var(--pc-surface);
  box-shadow: var(--pc-shadow);
}

.panel {
  padding: 14px;
}

.workflow-card {
  padding: 18px;
}

.panel-tight {
  padding: 10px;
}

#app-tabs {
  border-radius: 24px;
  overflow: hidden;
}

#app-tabs .tab-nav {
  background: rgba(255,255,255,0.58);
  border: 1px solid var(--pc-border);
  border-radius: 18px;
  padding: 6px;
  margin-bottom: 18px;
}

#app-tabs .tabitem {
  border-radius: 24px;
}

#app-tabs .tabitem.selected {
  background: linear-gradient(180deg, #fffdf9, #f6ede3);
  color: var(--pc-ink);
}

#inspector-toolbar {
  position: sticky;
  top: 12px;
  z-index: 10;
  margin-bottom: 14px;
  gap: 14px;
}

#inspector-toolbar .gradio-button {
  min-height: 44px;
  font-weight: 600;
}

#inspector-main {
  align-items: flex-start;
  gap: 14px;
}

#inspector-image-frame img {
  border-radius: 18px;
}

.decision-panel {
  background:
    linear-gradient(180deg, rgba(255,255,255,0.92), rgba(255,247,238,0.94));
}

.metric-strip {
  background: var(--pc-surface-strong);
}

.evidence-stack {
  gap: 12px;
}

.evidence-stack .gradio-accordion {
  border-radius: 18px;
  overflow: hidden;
  border: 1px solid var(--pc-border);
  background: var(--pc-surface);
}

#review-gallery,
#review-table,
#run-log-panel {
  overflow: hidden;
}

.status-note {
  color: var(--pc-muted);
  font-size: 0.95rem;
}

.gradio-button.primary {
  background: linear-gradient(135deg, var(--pc-accent), var(--pc-accent-strong));
}

.gradio-button.stop {
  background: linear-gradient(135deg, #a44747, #8b2e2e);
}

@media (max-width: 980px) {
  #hero-banner {
    padding: 20px;
  }

  #hero-banner h1 {
    font-size: 2rem;
  }

  #inspector-toolbar {
    position: static;
  }
}
"""


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
        img_dir,
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
    import gradio.utils
    if hasattr(gradio.utils, "is_in_or_equal"):
        pass
    _EXTRA_ALLOWED_PATHS.add(abs_path)


_EXTRA_ALLOWED_PATHS: set[str] = set()


def apply_filters_action(genre, status_filter, max_conf, sort_col, sort_asc):
    """Apply filters and return updated table + gallery."""
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
            None,
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            gr.update(value=None),
            "",
            "",
            "0 / 0",
        )

    nav = f"{d['position'] + 1} / {d['total_visible']}"
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
    theme = gr.themes.Base()
    with gr.Blocks(title="PhotoCat", theme=theme, css=UI_CSS) as app:
        with gr.Column(elem_id="photocat-shell"):
            gr.HTML(
                """
                <section id="hero-banner">
                  <h1>PhotoCat</h1>
                  <p>Review image genres with less friction: keep the photo large, keep the decision controls visible,
                  and keep the evidence close enough to trust every correction.</p>
                  <div id="hero-meta">
                    <span>Local-first browser UI</span>
                    <span>Fast genre review workflow</span>
                    <span>Designed for photographers, not dashboards</span>
                  </div>
                </section>
                """
            )

            with gr.Tabs(elem_id="app-tabs"):
                with gr.Tab("Run Pipeline"):
                    with gr.Column(elem_classes="workflow-card"):
                        gr.Markdown(
                            "### Pipeline Control\n"
                            "Launch the batch process here, then switch to review once a CSV exists."
                        )
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

                        with gr.Group(elem_classes="panel panel-tight"):
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

                        with gr.Row():
                            run_status = gr.Textbox(label="Status", value="Ready", interactive=False)
                            run_progress = gr.Textbox(label="Progress", value="", interactive=False)

                        with gr.Group(elem_id="run-log-panel", elem_classes="panel"):
                            run_log = gr.Textbox(
                                label="Live Log",
                                lines=20,
                                max_lines=40,
                                interactive=False,
                                autoscroll=True,
                            )

                with gr.Tab("Review Table"):
                    with gr.Column(elem_classes="workflow-card"):
                        with gr.Row():
                            csv_path_input = gr.Textbox(
                                label="CSV Path",
                                value="output/full_audit.csv",
                                scale=3,
                            )
                            load_btn = gr.Button("Load CSV", variant="primary")

                        with gr.Group(elem_classes="panel panel-tight"):
                            gr.Markdown("### Image Source Path")
                            with gr.Row():
                                img_dir_input = gr.Textbox(
                                    label="Folder containing the actual image files (filenames in CSV are resolved relative to this)",
                                    value="",
                                    placeholder=r"e.g. F:\Photos\export  or  /home/user/photos",
                                    scale=4,
                                )
                                update_path_btn = gr.Button("Update Path", scale=1)

                        with gr.Row():
                            load_msg = gr.Textbox(label="Status", interactive=False)
                            summary_text = gr.Textbox(label="Summary", lines=3, interactive=False)

                        with gr.Group(elem_classes="panel panel-tight"):
                            gr.Markdown("### Filter The Review Queue")
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

                        gr.Markdown(
                            "<div class='status-note'>Click any thumbnail to jump straight into the inspector.</div>"
                        )

                        with gr.Group(elem_id="review-gallery", elem_classes="panel"):
                            gallery = gr.Gallery(
                                label="Image Grid",
                                columns=6,
                                height=360,
                                object_fit="cover",
                            )

                        with gr.Group(elem_id="review-table", elem_classes="panel"):
                            review_table = gr.Dataframe(
                                headers=["filename", "review_status", "final_genre", "user_genre", "model_1st_conf", "user_label"],
                                interactive=False,
                                wrap=True,
                                label="Audit Table (read-only - edit genre in Inspector)",
                            )

                        with gr.Row():
                            export_btn = gr.Button("Export Corrected CSV", variant="primary")
                            organize_btn = gr.Button("Preview Organize")
                        export_msg = gr.Textbox(label="Export Status", interactive=False)
                        organize_preview = gr.Textbox(
                            label="Organize Preview", lines=8, interactive=False,
                        )

                with gr.Tab("Image Inspector"):
                    with gr.Column(elem_classes="workflow-card"):
                        gr.Markdown(
                            "### Review Workspace\n"
                            "Keep the photo large, keep the action controls visible, and expand evidence only when you need it."
                        )

                        with gr.Row(elem_id="inspector-toolbar"):
                            with gr.Column(scale=2, elem_classes="panel decision-panel"):
                                gr.Markdown("#### Review Position")
                                with gr.Row():
                                    prev_btn = gr.Button("< Prev")
                                    nav_label = gr.Textbox(
                                        value="0 / 0",
                                        label="Position",
                                        interactive=False,
                                        scale=1,
                                    )
                                    next_btn = gr.Button("Next >")
                                insp_status = gr.Textbox(label="Review Status", interactive=False)
                                insp_label_display = gr.Textbox(label="User Label", interactive=False)

                            with gr.Column(scale=3, elem_classes="panel decision-panel"):
                                gr.Markdown("#### Genre Decision")
                                genre_dropdown = gr.Dropdown(
                                    choices=GENRE_CATEGORIES,
                                    label="Assigned Genre",
                                    allow_custom_value=False,
                                )
                                with gr.Row():
                                    confirm_btn = gr.Button("Confirm Correct", variant="primary")
                                    wrong_btn = gr.Button("Mark Wrong", variant="stop")
                                action_msg = gr.Textbox(label="Action", interactive=False)

                        with gr.Row(elem_id="inspector-main"):
                            with gr.Column(scale=7, elem_classes="panel", elem_id="inspector-image-frame"):
                                insp_filename = gr.Textbox(label="File", interactive=False)
                                insp_image = gr.Image(
                                    label="Preview",
                                    type="filepath",
                                    height=620,
                                )

                            with gr.Column(scale=5, elem_classes="evidence-stack"):
                                with gr.Group(elem_classes="panel metric-strip"):
                                    gr.Markdown("#### Quick Read")
                                    with gr.Row():
                                        insp_rating = gr.Textbox(label="Rating", interactive=False, scale=1)
                                        insp_blur = gr.Textbox(label="Blur", interactive=False, scale=1)
                                        insp_exposure = gr.Textbox(label="Exposure", interactive=False, scale=1)

                                with gr.Accordion("Model Evidence", open=True, elem_classes="panel"):
                                    insp_siglip = gr.Textbox(label="SigLIP Scores", lines=4, interactive=False)
                                    insp_evidence = gr.Textbox(label="Evidence Log", lines=6, interactive=False)

                                with gr.Accordion("Scene Understanding", open=True, elem_classes="panel"):
                                    insp_caption = gr.Textbox(label="BLIP Caption", lines=3, interactive=False)
                                    insp_objects = gr.Textbox(label="YOLO Objects", interactive=False)
                                    insp_ocr = gr.Textbox(label="OCR Text", lines=3, interactive=False)

                    inspector_outputs = [
                        insp_image, insp_filename, insp_rating, insp_blur,
                        insp_exposure, insp_caption, insp_objects, insp_ocr,
                        insp_siglip, insp_evidence, genre_dropdown, insp_status,
                        insp_label_display, nav_label,
                    ]
                    inspector_outputs_with_msg = [action_msg] + inspector_outputs

        run_btn.click(
            run_pipeline,
            inputs=[
                input_dir, csv_output, recursive, write_xmp, genre_only,
                no_cache, organize, dry_run, min_conf, workers, extensions,
            ],
            outputs=[run_log, run_progress, run_status],
        )
        stop_btn.click(stop_pipeline, outputs=[run_status])

        load_btn.click(
            load_csv_action,
            inputs=[csv_path_input, img_dir_input],
            outputs=[load_msg, summary_text, review_table, gallery,
                     filter_genre, filter_status, img_dir_input],
        )

        update_path_btn.click(
            update_source_path,
            inputs=[img_dir_input],
            outputs=[load_msg, gallery] + inspector_outputs,
        )

        filter_btn.click(
            apply_filters_action,
            inputs=[filter_genre, filter_status, filter_conf, sort_col, sort_dir],
            outputs=[review_table, gallery, summary_text],
        )

        export_btn.click(export_csv_action, outputs=[export_msg])
        organize_btn.click(organize_preview_action, outputs=[organize_preview])

        gallery.select(gallery_select_action, outputs=inspector_outputs)

        prev_btn.click(inspector_prev, outputs=inspector_outputs)
        next_btn.click(inspector_next, outputs=inspector_outputs)

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

    allowed = list(_EXTRA_ALLOWED_PATHS)
    if sys.platform == "win32":
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
        allowed_paths=allowed,
    )


if __name__ == "__main__":
    main()
