import csv
import gc
import os
import shutil
import sys
import time
import cv2
import numpy as np
import pytesseract
import nltk
from nltk import word_tokenize, pos_tag
from nltk.corpus import stopwords
import string

# Download NLTK data only when not already cached locally (avoids blocking startup).
_NLTK_PACKAGES = [
    ("tokenizers/punkt",                          "punkt"),
    ("tokenizers/punkt_tab",                      "punkt_tab"),
    ("taggers/averaged_perceptron_tagger",         "averaged_perceptron_tagger"),
    ("taggers/averaged_perceptron_tagger_eng",     "averaged_perceptron_tagger_eng"),
    ("corpora/stopwords",                          "stopwords"),
]
for _resource_path, _package in _NLTK_PACKAGES:
    try:
        nltk.data.find(_resource_path)
    except LookupError:
        nltk.download(_package, quiet=True)

from device import get_device, get_device_info, print_device_info
from image_analysis import load_image, is_blurry, check_exposure, preprocess_image, analyze_color_tone
from object_detection import detect_objects
from metadata_writer import write_xmp_sidecar
from image_captioning import ImageCaptioner
from scene_classifier import get_classifier
from genre_decision import make_genre_decision
from cli import build_parser, collect_images, CATEGORY_DIRS
from cache import (
    ImageCache,
    build_full_payload,
    build_genre_only_payload,
    restore_siglip,
)

#####################
# Lazy model singletons
# Initialized on first use inside each worker process, not at import time.
# This prevents Windows spawn workers from loading multi-GB models 8× simultaneously.
#####################
_captioner = None
_scene_clf = None


def _get_captioner():
    global _captioner
    if _captioner is None:
        _captioner = ImageCaptioner()
    return _captioner


def _get_scene_clf():
    global _scene_clf
    if _scene_clf is None:
        _scene_clf = get_classifier()
    return _scene_clf


#####################
# Helper Functions
#####################

def compute_composition_rating(image, objects):
    if len(objects) == 0:
        return 1
    elif len(objects) == 1:
        return 2
    return 3


def compute_rating(is_blur, exposure, objects_detected, composition_score):
    rating = composition_score
    if is_blur:
        rating -= 1
    if exposure in ['under', 'over']:
        rating -= 1
    else:
        rating += 1
    return max(1, min(rating, 5))


def basic_color_name(rgb):
    hsv = cv2.cvtColor(np.uint8([[rgb]]), cv2.COLOR_RGB2HSV)[0][0]
    h, s, v = hsv
    if s < 50 and v > 200:
        return "white"
    if v < 50:
        return "black"
    if s < 50 and v < 200:
        return "gray"
    if h < 15 or h > 165:
        return "red"
    elif h < 35:
        return "orange"
    elif h < 85:
        return "green"
    elif h < 125:
        return "blue"
    elif h < 165:
        return "purple"
    return "colorful"


def extract_top_colors(image, top_n=3):
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img_small = cv2.resize(img_rgb, (100, 100))
    data = np.float32(img_small.reshape(-1, 3))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(data, top_n, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    centers = np.uint8(centers)
    counts = np.bincount(labels.flatten())
    sorted_idx = np.argsort(counts)[::-1]
    named_colors = []
    for c in centers[sorted_idx]:
        name = basic_color_name(c)
        if name not in named_colors:
            named_colors.append(name)
    return named_colors


def detect_mood(image):
    brightness, contrast = analyze_color_tone(image)
    if brightness > 150 and contrast < 50:
        return "serene"
    elif brightness > 150 and contrast >= 50:
        return "vibrant"
    elif brightness < 80 and contrast < 50:
        return "muted"
    elif brightness < 80 and contrast >= 50:
        return "dramatic"
    return "calm"


def ocr_text(image):
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 3)
        return pytesseract.image_to_string(gray).lower()
    except pytesseract.TesseractNotFoundError:
        return ""


def analyze_scene(objects, ocr_result):
    beverage_words = ["can", "bottle", "drink", "beverage"]
    brand_words = ["mamitas", "mandarina", "coca", "pepsi"]
    lower_objects = [obj.lower() for obj in objects]
    has_beverage = any(obj in lower_objects for obj in beverage_words)
    if not has_beverage:
        has_beverage = any(bw in ocr_result for bw in beverage_words)
    identified_brand = next((bw for bw in brand_words if bw in ocr_result), None)
    return has_beverage, identified_brand


def caption_to_tags(caption):
    words = word_tokenize(caption.lower())
    words = [w for w in words if w not in set(stopwords.words('english')) and w not in string.punctuation]
    pos_tags = pos_tag(words)
    return list({w for w, pos in pos_tags if pos.startswith('NN') or pos.startswith('JJ')})


def generate_tags_from_all(objects_detected, image, has_beverage, identified_brand, caption):
    tags = set(obj.lower() for obj in objects_detected)
    tags.update(extract_top_colors(image, top_n=3))
    tags.add(detect_mood(image))
    if has_beverage:
        tags.add("beverage")
        if identified_brand:
            tags.add(identified_brand)
    tags.update(caption_to_tags(caption))
    return list(tags)


def refine_title(caption, objects_detected, has_beverage, identified_brand):
    title = caption.strip()
    if not title.endswith('.'):
        title += '.'
    title = title[0].upper() + title[1:]
    if has_beverage and identified_brand and identified_brand not in title.lower():
        if "beverage can" in title.lower():
            title = title.replace("beverage can", f"{identified_brand.capitalize()} beverage can")
        elif "can" in title.lower():
            title = title.replace("can", f"{identified_brand.capitalize()} can")
    return title


#####################
# Per-image pipeline
#####################

def _clear_model_cache():
    """Free unused memory after model inference."""
    gc.collect()
    import torch
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        torch.mps.empty_cache()


def process_image(img_path, enable_blur=True, enable_exposure=True,
                  enable_object_detection=True, enable_genre=True,
                  genre_only=False, idx=None, total=None, cache=None):
    t_start = time.perf_counter()
    tag = f"[{idx}/{total}] " if idx is not None else ""
    fname = os.path.basename(img_path)

    # ------------------------------------------------------------------
    # Cache lookup — skip all GPU work on hit
    # ------------------------------------------------------------------
    if cache is not None:
        cached = cache.get(img_path)
        if cached is not None:
            # Only a genre_only payload cannot serve a full-pipeline request
            if genre_only or cached.get("mode") == "full":
                siglip_result = restore_siglip(cached["siglip_result"])

                if genre_only:
                    genre_result = make_genre_decision(siglip_result=siglip_result)
                    elapsed = (time.perf_counter() - t_start) * 1000
                    print(f"{tag}[cache] {fname}: Genre={genre_result['genre']} "
                          f"(conf={genre_result['confidence']:.2f}, "
                          f"status={genre_result['review_status']}, {elapsed:.0f}ms)")
                    return None, None, None, genre_result, None

                # Full pipeline from cache
                objects_detected = cached.get("objects_detected", [])
                caption = cached.get("caption", "")
                ocr_result = cached.get("ocr_result", "")
                title = cached.get("title", "")
                genre_result = make_genre_decision(
                    siglip_result=siglip_result,
                    yolo_detections=objects_detected,
                    caption=caption,
                    ocr_text=ocr_result,
                    title=title,
                )
                rating = cached.get("rating")
                tags = cached.get("tags", [])
                meta = {
                    "is_blurry": cached.get("is_blurry"),
                    "exposure": cached.get("exposure"),
                    "objects_detected": objects_detected,
                    "ocr_result": ocr_result,
                    "caption": caption,
                }
                elapsed = (time.perf_counter() - t_start) * 1000
                print(f"{tag}[cache] {fname}: Genre={genre_result['genre']} "
                      f"(conf={genre_result['confidence']:.2f}, "
                      f"status={genre_result['review_status']}, {elapsed:.0f}ms)")
                return rating, tags, title, genre_result, meta

    # ------------------------------------------------------------------
    # Full pipeline (cache miss or cache disabled)
    # ------------------------------------------------------------------
    print(f"{tag}Processing: {fname}")
    image = load_image(img_path)
    if image is None:
        print(f"{tag}Skipping {fname} (load failure)")
        return None, None, None, None, None

    image = preprocess_image(image, apply_noise_reduction=True)

    # Genre-only mode: skip YOLO, OCR, BLIP — only run SigLIP2
    if genre_only:
        from PIL import Image as PILImage
        pil_image = PILImage.fromarray(image[:, :, ::-1])
        siglip_result = _get_scene_clf().classify_scene(pil_image)
        genre_result = make_genre_decision(siglip_result=siglip_result)
        elapsed = (time.perf_counter() - t_start) * 1000
        print(f"{tag}  Genre: {genre_result['genre']} "
              f"(conf={genre_result['confidence']:.2f}, status={genre_result['review_status']})")
        _clear_model_cache()
        print(f"{tag}Done {fname}: Genre-only ({elapsed:.0f}ms)")
        if cache is not None:
            cache.set(img_path, build_genre_only_payload(siglip_result))
        return None, None, None, genre_result, None

    is_image_blurry = is_blurry(image) if enable_blur else False
    exposure = check_exposure(image) if enable_exposure else 'normal'

    objects_detected = []
    if enable_object_detection:
        objects_detected = detect_objects(image)

    ocr_result = ocr_text(image)
    has_beverage, identified_brand = analyze_scene(objects_detected, ocr_result)
    caption = _get_captioner().caption_image(image)
    composition_score = compute_composition_rating(image, objects_detected)
    rating = compute_rating(is_image_blurry, exposure, objects_detected, composition_score)
    tags = generate_tags_from_all(objects_detected, image, has_beverage, identified_brand, caption)
    title = refine_title(caption, objects_detected, has_beverage, identified_brand)

    meta = {
        "is_blurry": is_image_blurry,
        "exposure": exposure,
        "objects_detected": objects_detected,
        "ocr_result": ocr_result,
        "caption": caption,
    }

    genre_result = None
    if enable_genre:
        from PIL import Image as PILImage
        pil_image = PILImage.fromarray(image[:, :, ::-1])
        siglip_result = _get_scene_clf().classify_scene(pil_image)
        genre_result = make_genre_decision(
            siglip_result=siglip_result,
            yolo_detections=objects_detected,
            caption=caption,
            ocr_text=ocr_result,
            title=title,
        )
        print(f"{tag}  Genre: {genre_result['genre']} "
              f"(conf={genre_result['confidence']:.2f}, status={genre_result['review_status']})")
        if cache is not None:
            cache.set(img_path, build_full_payload(
                objects_detected=objects_detected,
                caption=caption,
                siglip_result=siglip_result,
                ocr_result=ocr_result,
                is_blurry=is_image_blurry,
                exposure=exposure,
                rating=rating,
                tags=tags,
                title=title,
            ))

    _clear_model_cache()

    elapsed = (time.perf_counter() - t_start) * 1000
    print(f"{tag}Done {fname}: Rating={rating}, Title='{title}' ({elapsed:.0f}ms)")
    return rating, tags, title, genre_result, meta


def process_and_write(args):
    img_path, write_xmp, genre_only, idx, total, cache = args
    rating, tags, title, genre_result, meta = process_image(
        img_path, enable_genre=True, genre_only=genre_only, idx=idx, total=total,
        cache=cache,
    )
    if genre_only:
        if write_xmp and genre_result:
            write_xmp_sidecar(img_path, None, None, None, genre_result=genre_result)
        return (img_path, None, None, None, genre_result, None)
    if rating is None:
        return (img_path, None, None, None, None, None)
    if write_xmp:
        write_xmp_sidecar(img_path, rating, tags, title, genre_result=genre_result)
    return (img_path, rating, tags, title, genre_result, meta)


def _write_audit_csv(csv_path, results):
    """Write an audit CSV with final genre, raw model predictions, review status, and full meta."""
    import json

    # Detect whether any result has meta (full pipeline) to decide header set
    has_meta = any(len(r) >= 6 and r[5] is not None for r in results)

    base_cols = [
        "filename", "rating", "final_genre", "review_status",
        "model_1st", "model_1st_conf", "model_2nd", "model_2nd_conf", "title",
    ]
    rich_cols = [
        "is_blurry", "exposure", "objects_detected", "caption", "ocr_text", "evidence_log",
    ]
    header = base_cols + (rich_cols if has_meta else [])

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        for row in results:
            img_path = row[0]
            rating   = row[1]
            tags     = row[2]
            title    = row[3]
            genre_result = row[4]
            meta     = row[5] if len(row) >= 6 else None

            fname = os.path.basename(img_path)

            if genre_result is None:
                base = [fname, rating or "", "", "skipped", "", "", "", "", title or ""]
                if has_meta:
                    base += ["", "", "", "", "", ""]
                writer.writerow(base)
                continue

            top2 = genre_result.get("top2", [])
            m1 = top2[0][0] if len(top2) > 0 else ""
            c1 = f"{top2[0][1]:.4f}" if len(top2) > 0 else ""
            m2 = top2[1][0] if len(top2) > 1 else ""
            c2 = f"{top2[1][1]:.4f}" if len(top2) > 1 else ""

            base = [
                fname, rating or "",
                genre_result.get("genre", ""),
                genre_result.get("review_status", ""),
                m1, c1, m2, c2, title or "",
            ]

            if has_meta:
                if meta:
                    objects_str = "; ".join(meta.get("objects_detected") or [])
                    evidence_str = json.dumps(genre_result.get("evidence_log", {}), ensure_ascii=False)
                    base += [
                        "yes" if meta.get("is_blurry") else "no",
                        meta.get("exposure", ""),
                        objects_str,
                        meta.get("caption", ""),
                        meta.get("ocr_result", ""),
                        evidence_str,
                    ]
                else:
                    base += ["", "", "", "", "", ""]

            writer.writerow(base)


def _organize_into_dirs(input_dir, results, dry_run=False):
    """Move images into genre subdirectories. Returns count of moved files."""
    from collections import defaultdict
    plan = defaultdict(list)  # genre → [fname, ...]

    for row in results:
        img_path, genre_result = row[0], row[4]
        if genre_result is None:
            continue
        genre = genre_result.get("genre", "")
        if not genre:
            continue
        fname = os.path.basename(img_path)
        dest_path = os.path.join(input_dir, genre, fname)
        if os.path.abspath(img_path) == os.path.abspath(dest_path):
            continue
        plan[genre].append((img_path, dest_path))

    if dry_run:
        total_planned = sum(len(v) for v in plan.values())
        print(f"\n[dry-run] Would move {total_planned} image(s) into {len(plan)} genre folder(s):\n")
        for genre in sorted(plan):
            print(f"  {genre}/  ({len(plan[genre])} files)")
            for img_path, _ in plan[genre]:
                print(f"    {os.path.basename(img_path)}")
        print()
        return 0

    moved = 0
    for genre, items in plan.items():
        dest_dir = os.path.join(input_dir, genre)
        os.makedirs(dest_dir, exist_ok=True)
        for img_path, dest_path in items:
            shutil.move(img_path, dest_path)
            moved += 1
            xmp_src = os.path.splitext(img_path)[0] + ".xmp"
            if os.path.exists(xmp_src):
                shutil.move(xmp_src, os.path.join(dest_dir, os.path.basename(xmp_src)))
    return moved


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Startup: detect and report hardware
    device_info = get_device_info()
    print_device_info(device_info)
    print()

    input_dir = args.input_dir
    print(f"Input: {input_dir}")

    image_files = collect_images(
        input_dir,
        recursive=args.recursive,
        extensions=args.extensions,
    )

    if not image_files:
        print("No images found.")
        return

    total = len(image_files)
    write_xmp = args.write_xmp

    # ------------------------------------------------------------------
    # Cache setup
    # ------------------------------------------------------------------
    use_cache = not args.no_cache
    cache = None
    if use_cache:
        cache_dir = args.cache_dir or os.path.join(input_dir, ".photocat_cache")
        cache = ImageCache(cache_dir)
        print(f"Cache: {cache_dir}")
    else:
        print("Cache: disabled (--no-cache)")

    print(f"Found {total} image(s). write-xmp={write_xmp}, workers={args.workers}")
    print()

    task_args = [
        (f, write_xmp, args.genre_only, i + 1, total, cache)
        for i, f in enumerate(image_files)
    ]

    batch_start = time.perf_counter()

    if args.workers > 1:
        # Cache is not safe to share across processes; disable it for multi-worker runs.
        if cache is not None:
            print("[WARNING] Cache disabled for multi-worker runs (workers > 1).")
            cache.close()
            cache = None
        task_args = [
            (f, write_xmp, args.genre_only, i + 1, total, None)
            for i, f in enumerate(image_files)
        ]
        from multiprocessing import Pool
        with Pool(args.workers) as p:
            results = p.map(process_and_write, task_args)
    else:
        results = [process_and_write(a) for a in task_args]

    batch_elapsed = time.perf_counter() - batch_start

    if cache is not None:
        stats = cache.stats()
        cache.close()
        print(f"Cache: {stats['hits']} hits, {stats['misses']} misses")

    print()
    print(f"{'='*60}")
    print(f"Batch complete: {total} images in {batch_elapsed:.1f}s ({batch_elapsed/total:.2f}s/image avg)")
    print(f"{'='*60}")

    skipped = sum(1 for r in results if r[1] is None and r[4] is None)
    if skipped:
        print(f"Skipped: {skipped} image(s)")

    # --- CSV audit report ---
    csv_path = args.csv
    if csv_path is None:
        # Always generate CSV by default into input dir
        csv_path = os.path.join(input_dir, "photocat_audit.csv")
    _write_audit_csv(csv_path, results)
    print(f"Audit CSV written to: {csv_path}")

    # --- Organize into genre subdirectories ---
    if args.organize:
        moved = _organize_into_dirs(input_dir, results, dry_run=args.dry_run)
        if not args.dry_run:
            print(f"Organized: {moved} image(s) moved into category directories.")


# Required on Windows to prevent recursive spawning of worker processes
if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    main()
