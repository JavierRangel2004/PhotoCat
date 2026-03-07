import gc
import os
import sys
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

from image_analysis import load_image, is_blurry, check_exposure, preprocess_image, analyze_color_tone
from object_detection import detect_objects
from metadata_writer import write_xmp_sidecar
from image_captioning import ImageCaptioner
from scene_classifier import get_classifier
from genre_decision import make_genre_decision
from cli import build_parser, collect_images

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
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()


def process_image(img_path, enable_blur=True, enable_exposure=True,
                  enable_object_detection=True, enable_genre=True,
                  genre_only=False):
    print(f"Processing image: {img_path}")
    image = load_image(img_path)
    if image is None:
        print(f"Skipping {img_path} due to load failure.")
        return None, None, None, None

    image = preprocess_image(image, apply_noise_reduction=True)

    # Genre-only mode: skip YOLO, OCR, BLIP — only run SigLIP2
    if genre_only:
        from PIL import Image as PILImage
        pil_image = PILImage.fromarray(image[:, :, ::-1])
        siglip_result = _get_scene_clf().classify_scene(pil_image)
        genre_result = make_genre_decision(siglip_result=siglip_result)
        print(f"  Genre: {genre_result['genre']} "
              f"(conf={genre_result['confidence']:.2f}, status={genre_result['review_status']})")
        _clear_model_cache()
        print(f"Finished {img_path}: Genre-only mode")
        return None, None, None, genre_result

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
        print(f"  Genre: {genre_result['genre']} "
              f"(conf={genre_result['confidence']:.2f}, status={genre_result['review_status']})")

    _clear_model_cache()

    print(f"Finished {img_path}: Rating={rating}, Title='{title}'")
    return rating, tags, title, genre_result


def process_and_write(args):
    img_path, write_xmp, genre_only = args
    rating, tags, title, genre_result = process_image(
        img_path, enable_genre=True, genre_only=genre_only,
    )
    if genre_only:
        if write_xmp and genre_result:
            write_xmp_sidecar(img_path, None, None, None, genre_result=genre_result)
        return (img_path, None, None, None, genre_result)
    if rating is None:
        return (img_path, None, None, None, None)
    if write_xmp:
        write_xmp_sidecar(img_path, rating, tags, title, genre_result=genre_result)
    return (img_path, rating, tags, title, genre_result)


def main():
    parser = build_parser()
    args = parser.parse_args()

    input_dir = args.input_dir
    print(f"Processing images in: {input_dir}")

    image_files = collect_images(
        input_dir,
        recursive=args.recursive,
        extensions=args.extensions,
    )

    if not image_files:
        print("No images found.")
        return

    write_xmp = args.write_xmp
    print(f"Found {len(image_files)} image(s). write-xmp={write_xmp}, workers={args.workers}")

    task_args = [(f, write_xmp, args.genre_only) for f in image_files]

    if args.workers > 1:
        from multiprocessing import Pool
        with Pool(args.workers) as p:
            results = p.map(process_and_write, task_args)
    else:
        results = [process_and_write(a) for a in task_args]

    for res in results:
        img_path, rating, tags, title, genre_result = res
        if genre_result and rating is None:
            # genre-only mode
            print(f"Done {img_path}: Genre={genre_result['genre']} "
                  f"({genre_result['review_status']}, "
                  f"conf={genre_result['confidence']:.2f})")
        elif rating is not None:
            genre_str = ""
            if genre_result:
                genre_str = (f", Genre={genre_result['genre']} "
                             f"({genre_result['review_status']}, "
                             f"conf={genre_result['confidence']:.2f})")
            print(f"Done {img_path}: Rating={rating}{genre_str}")
        else:
            print(f"Skipped {img_path}")


# Required on Windows to prevent recursive spawning of worker processes
if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    main()
