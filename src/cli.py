"""
cli.py — Argument parser for PhotoCat batch pipeline.

Replaces the hard-coded 'images/' path in main.py.
"""

import argparse
import os


def build_parser():
    parser = argparse.ArgumentParser(
        prog="photocat",
        description="PhotoCat: batch image analysis and genre classification pipeline.",
    )

    parser.add_argument(
        "--input-dir",
        default="images",
        help="Directory of images to process (default: images/).",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        default=False,
        help="Recurse into sub-directories.",
    )
    parser.add_argument(
        "--extensions",
        default=".jpg,.jpeg,.png,.tiff,.webp,.cr2,.cr3,.dng",
        help="Comma-separated list of file extensions to include.",
    )
    parser.add_argument(
        "--write-xmp",
        action="store_true",
        default=False,
        help="Write XMP sidecar files (default: dry-run, no writes).",
    )
    parser.add_argument(
        "--genre-only",
        action="store_true",
        default=False,
        help="Run genre classification only; skip blur/exposure/OCR/captioning.",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.55,
        help="Minimum confidence to include a genre prediction in output (default: 0.55).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of parallel worker processes (default: 1). "
             "Keep at 1 when running GPU models to avoid VRAM exhaustion.",
    )

    return parser


def collect_images(input_dir, recursive=False, extensions=None):
    """Return sorted list of image paths under input_dir."""
    if extensions is None:
        extensions = {".jpg", ".jpeg", ".png", ".tiff", ".webp", ".cr2", ".cr3", ".dng"}
    else:
        extensions = {e.strip().lower() for e in extensions.split(",")}

    paths = []
    if recursive:
        for root, _dirs, files in os.walk(input_dir):
            for fname in files:
                if os.path.splitext(fname)[1].lower() in extensions:
                    paths.append(os.path.join(root, fname))
    else:
        for fname in os.listdir(input_dir):
            if os.path.splitext(fname)[1].lower() in extensions:
                paths.append(os.path.join(input_dir, fname))

    return sorted(paths)
