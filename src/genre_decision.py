"""
genre_decision.py — Evidence fusion and confidence-gated write policy.

Combines SigLIP2 classification with YOLO object cues, caption text, and OCR text
to produce a final genre label and a write-policy status.

Write policy (Phase 0 decision):
  HIGH  (>= 0.80) → review_status = "auto"   → write genre to XMP
  MEDIUM (0.55-0.79) → review_status = "review"  → write genre + add 'genre-needs-review' tag
  LOW   (< 0.55)  → review_status = "skip"   → log only, no XMP write
"""

# Boost amounts applied per detected evidence cue
_BOOST = 0.12

# Object label sets that boost specific genres
_CONCERT_OBJECTS = {
    "microphone", "guitar", "drums", "keyboard", "piano",
    "speaker", "amplifier", "stage", "spotlight", "crowd",
    "person",  # crowd of people at a concert
}
_NATURE_OBJECTS = {
    "tree", "flower", "bird", "cat", "dog", "horse", "cow",
    "sheep", "elephant", "bear", "zebra", "giraffe", "mountain",
    "plant", "leaf", "grass", "sky",
}
_PRODUCT_OBJECTS = {
    "bottle", "cup", "bowl", "wine glass", "fork", "knife",
    "spoon", "cell phone", "laptop", "keyboard", "mouse",
    "book", "clock", "vase", "scissors", "toothbrush",
    "sports ball", "tennis racket", "remote",
}
_STREET_OBJECTS = {
    "car", "bus", "truck", "motorcycle", "bicycle",
    "traffic light", "stop sign", "parking meter",
    "bench", "backpack", "umbrella", "handbag",
}

# Caption / OCR keyword hints
_CONCERT_KEYWORDS = {"concert", "stage", "mic", "microphone", "guitar", "band", "music", "live", "performance", "festival"}
_NATURE_KEYWORDS = {"nature", "forest", "mountain", "river", "lake", "ocean", "wildlife", "landscape", "sunset", "sunrise", "tree", "flower", "beach", "field"}
_PRODUCT_KEYWORDS = {"product", "bottle", "can", "brand", "studio", "commercial", "isolated", "white background", "packaging"}
_PORTRAIT_KEYWORDS = {"portrait", "face", "person", "smile", "close-up", "headshot", "model"}
_STREET_KEYWORDS = {"street", "city", "urban", "road", "sidewalk", "building", "crowd", "candid", "town"}

HIGH_THRESHOLD = 0.80
MEDIUM_THRESHOLD = 0.55


def _keyword_boost(text, keywords):
    """Return _BOOST if any keyword appears in text, else 0."""
    if not text:
        return 0.0
    text_lower = text.lower()
    return _BOOST if any(kw in text_lower for kw in keywords) else 0.0


def _object_boost(detections, object_set):
    """Return _BOOST if any detected label is in the object set, else 0."""
    if not detections:
        return 0.0
    det_lower = {d.lower() for d in detections}
    return _BOOST if det_lower & object_set else 0.0


def make_genre_decision(siglip_result, yolo_detections=None, caption="", ocr_text=""):
    """
    Args:
        siglip_result:   dict from SceneClassifier.classify_scene()
        yolo_detections: list[str] of detected object class names (may be empty)
        caption:         str caption from image captioning model
        ocr_text:        str OCR output from the image

    Returns:
        dict:
            genre         (str)
            confidence    (float, 0-1, capped at 0.95)
            review_status ("auto" | "review" | "skip")
            top2          (list of two (label, score) tuples)
            evidence_log  (dict — what boosted what)
    """
    yolo_detections = yolo_detections or []
    caption = caption or ""
    ocr_text = ocr_text or ""

    # Start from SigLIP2 scores
    scores = {label: score for label, score in siglip_result["top_k"]}

    evidence_log = {}

    # --- Concert boosts ---
    concert_obj_boost = _object_boost(yolo_detections, _CONCERT_OBJECTS)
    concert_txt_boost = _keyword_boost(caption + " " + ocr_text, _CONCERT_KEYWORDS)
    if concert_obj_boost or concert_txt_boost:
        scores["Concert Photography"] = scores.get("Concert Photography", 0.0) + concert_obj_boost + concert_txt_boost
        evidence_log["concert_boost"] = concert_obj_boost + concert_txt_boost

    # --- Nature boosts ---
    has_dominant_person = "person" in {d.lower() for d in yolo_detections}
    nature_obj_boost = _object_boost(yolo_detections, _NATURE_OBJECTS) if not has_dominant_person else 0.0
    nature_txt_boost = _keyword_boost(caption + " " + ocr_text, _NATURE_KEYWORDS)
    if nature_obj_boost or nature_txt_boost:
        scores["Nature Photography"] = scores.get("Nature Photography", 0.0) + nature_obj_boost + nature_txt_boost
        evidence_log["nature_boost"] = nature_obj_boost + nature_txt_boost

    # --- Product boosts ---
    product_obj_boost = _object_boost(yolo_detections, _PRODUCT_OBJECTS)
    product_txt_boost = _keyword_boost(caption + " " + ocr_text, _PRODUCT_KEYWORDS)
    if product_obj_boost or product_txt_boost:
        scores["Product Photography"] = scores.get("Product Photography", 0.0) + product_obj_boost + product_txt_boost
        evidence_log["product_boost"] = product_obj_boost + product_txt_boost

    # --- Portrait boosts ---
    portrait_txt_boost = _keyword_boost(caption + " " + ocr_text, _PORTRAIT_KEYWORDS)
    if portrait_txt_boost:
        scores["Portraits Photography"] = scores.get("Portraits Photography", 0.0) + portrait_txt_boost
        evidence_log["portrait_boost"] = portrait_txt_boost

    # --- Street boosts ---
    street_obj_boost = _object_boost(yolo_detections, _STREET_OBJECTS)
    street_txt_boost = _keyword_boost(caption + " " + ocr_text, _STREET_KEYWORDS)
    if street_obj_boost or street_txt_boost:
        scores["Street Photography"] = scores.get("Street Photography", 0.0) + street_obj_boost + street_txt_boost
        evidence_log["street_boost"] = street_obj_boost + street_txt_boost

    # Re-normalize so scores sum to 1 (they may have been probability-like already)
    total = sum(scores.values())
    if total > 0:
        scores = {k: v / total for k, v in scores.items()}

    top_k = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    genre = top_k[0][0]
    confidence = min(top_k[0][1], 0.95)  # cap at 0.95

    # Write policy
    if confidence >= HIGH_THRESHOLD:
        review_status = "auto"
    elif confidence >= MEDIUM_THRESHOLD:
        review_status = "review"
    else:
        review_status = "skip"

    return {
        "genre": genre,
        "confidence": confidence,
        "review_status": review_status,
        "top2": top_k[:2],
        "evidence_log": evidence_log,
    }
