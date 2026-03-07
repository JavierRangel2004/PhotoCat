"""
genre_decision.py — Evidence fusion and confidence-gated write policy.

Combines SigLIP2 classification with YOLO object cues, caption text, and OCR text
to produce a final genre label and a write-policy status.

Write policy (Phase 0 decision):
  HIGH  (>= 0.80) → review_status = "auto"          → write genre to XMP
  MEDIUM (0.55-0.79) → review_status = "review"      → write genre + add 'genre-needs-review' tag
  LOW   (< 0.55)  → review_status = "title-inferred" → derive category from title; write + tag
"""

# Boost amounts applied per detected evidence cue
_BOOST = 0.12
# Negative boost (demotion) for contradiction checks
_DEMOTE = 0.10

# ---------------------------------------------------------------------------
# Object label sets that boost specific genres
# NOTE: "person" intentionally excluded — too generic, biases Concert/Wedding
# ---------------------------------------------------------------------------
_CONCERT_OBJECTS = {
    "microphone", "guitar", "drums", "keyboard", "piano",
    "speaker", "amplifier", "spotlight",
}
_NATURE_OBJECTS = {
    "tree", "flower", "bird", "cat", "dog", "horse", "cow",
    "sheep", "elephant", "bear", "zebra", "giraffe", "mountain",
    "plant", "leaf", "grass", "sky",
}
_FOOD_OBJECTS = {
    "cake", "donut", "sandwich", "pizza", "hot dog", "carrot", "broccoli",
    "apple", "orange", "banana", "wine glass", "cup", "bowl",
    "fork", "knife", "spoon", "dining table", "oven",
}
_PRODUCT_OBJECTS = {
    "bottle", "cell phone", "laptop", "mouse",
    "book", "clock", "vase", "scissors", "toothbrush",
    "sports ball", "tennis racket", "remote",
}
_STREET_OBJECTS = {
    "car", "bus", "truck", "motorcycle", "bicycle",
    "traffic light", "stop sign", "parking meter",
    "bench", "backpack", "umbrella", "handbag",
}
# Phase 1: Wedding objects — YOLO labels that suggest a wedding scene
_WEDDING_OBJECTS = {
    "tie", "cake",
}

# ---------------------------------------------------------------------------
# Caption / OCR keyword hints
# ---------------------------------------------------------------------------
_CONCERT_KEYWORDS = {"concert", "stage", "mic", "microphone", "guitar", "band", "music", "live", "performance", "festival"}
_NATURE_KEYWORDS = {"nature", "forest", "mountain", "river", "lake", "ocean", "wildlife", "landscape", "sunset", "sunrise", "tree", "flower", "beach", "field"}
# Phase 3: Removed generic keywords "cutting", "preparing" — too many false positives
_FOOD_KEYWORDS = {"food", "cook", "kitchen", "chef", "cake", "donut", "doughnut", "meal", "eat", "dish", "bread", "dough", "bake", "dessert", "pastry", "plate", "recipe", "restaurant", "ingredient", "chocolate", "chefs"}
_PRODUCT_KEYWORDS = {"product", "bottle", "can", "brand", "studio", "commercial", "isolated", "white background", "packaging"}
_PORTRAIT_KEYWORDS = {"portrait", "face", "person", "smile", "close-up", "headshot", "model"}
_STREET_KEYWORDS = {"street", "city", "urban", "road", "sidewalk", "building", "crowd", "candid", "town"}
# Phase 1: Wedding keywords
_WEDDING_KEYWORDS = {
    "bride", "groom", "wedding", "bridal", "bouquet", "veil",
    "reception", "ceremony", "marriage", "married", "chapel",
    "bridesmaid", "groomsmen", "confetti", "aisle",
}

# Phase 2: Contradiction-check word sets
_PERSON_WORDS = {"woman", "man", "girl", "boy", "person", "people", "posing", "portrait", "dress", "suit", "wearing"}
_FOOD_CONFIRM_WORDS = {"food", "dish", "meal", "plate", "cook", "chef", "kitchen", "eat", "restaurant", "cake", "donut", "bread", "dessert", "pastry", "pizza", "sandwich", "chocolate"}
# Phase 4: Nature-indicator words for product disambiguation
_NATURE_CAPTION_WORDS = {"shark", "fish", "bird", "moon", "sky", "ocean", "sea", "flying", "swimming", "sunset", "sunrise", "mountain", "forest", "wildlife", "animal", "manta", "seahorse", "ray"}

HIGH_THRESHOLD = 0.80
MEDIUM_THRESHOLD = 0.55

# --- Title-based fallback category maps (used when confidence < MEDIUM_THRESHOLD) ---
_TITLE_CATEGORY_RULES = [
    # Phase 1: Wedding before Food/Event to catch wedding receptions
    ({"bride", "groom", "wedding", "bridal", "bouquet", "veil", "ceremony",
      "reception", "bridesmaid", "groomsmen", "married"},
     "Wedding Photography"),
    ({"food", "cook", "kitchen", "chef", "cake", "donut", "doughnut", "meal", "eat", "dish",
      "bread", "dough", "bake", "dessert", "pastry", "plate", "chocolate", "chefs", "frying",
      "ingredients", "stove", "oven", "restaurant"},
     "Food Photography"),
    ({"danc", "perform", "stage", "festival", "show", "sword", "folk", "cosplay",
      "costume", "parade", "cultural", "carnival"},
     "Event Photography"),
    ({"beach", "ocean", "sea", "wave", "surf", "coastal", "shore", "bay"},
     "Beach Photography"),
    ({"building", "church", "castle", "bridge", "tower", "landmark", "cathedral",
      "monument", "statue", "architecture", "hallway", "corridor"},
     "Architecture Photography"),
    ({"sport", "bike", "skateboard", "football", "run", "jump", "game", "match",
      "soccer", "tennis", "basketball", "swim", "race", "athlete"},
     "Sports Photography"),
    ({"street", "city", "urban", "road", "sidewalk", "alley", "neon", "sign",
      "graffiti", "mural", "market"},
     "Street Photography"),
    ({"portrait", "face", "smile", "headshot", "selfie", "pose", "posing"},
     "Portraits Photography"),
    ({"nature", "forest", "mountain", "river", "lake", "wildlife", "landscape",
      "sunset", "sunrise", "tree", "flower", "field", "garden", "park", "jungle",
      "woods", "waterfall", "cliff", "valley"},
     "Nature Photography"),
    ({"concert", "band", "music", "guitar", "microphone", "singer", "musician"},
     "Concert Photography"),
]


def _title_based_category(title: str) -> str:
    """Derive a photography category from image title keywords when model confidence is low."""
    title_lower = title.lower()
    for keyword_set, category in _TITLE_CATEGORY_RULES:
        if any(kw in title_lower for kw in keyword_set):
            return category
    return "Other Photography"


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


def _has_any_word(text, word_set):
    """Check if any word from word_set appears in text (case-insensitive)."""
    if not text:
        return False
    text_lower = text.lower()
    return any(w in text_lower for w in word_set)


def make_genre_decision(siglip_result, yolo_detections=None, caption="", ocr_text="", title=""):
    """
    Args:
        siglip_result:   dict from SceneClassifier.classify_scene()
        yolo_detections: list[str] of detected object class names (may be empty)
        caption:         str caption from image captioning model
        ocr_text:        str OCR output from the image
        title:           str refined title used as fallback for low-confidence images

    Returns:
        dict:
            genre         (str)
            confidence    (float, 0-1, capped at 0.95)
            review_status ("auto" | "review" | "title-inferred")
            top2          (list of two (label, score) tuples)
            evidence_log  (dict — what boosted what)
    """
    yolo_detections = yolo_detections or []
    caption = caption or ""
    ocr_text = ocr_text or ""
    title = title or ""
    combined_text = caption + " " + ocr_text + " " + title

    # Start from SigLIP2 scores
    scores = {label: score for label, score in siglip_result["top_k"]}

    evidence_log = {}
    det_lower = {d.lower() for d in yolo_detections}
    has_dominant_person = "person" in det_lower

    # ===================================================================
    # POSITIVE BOOSTS — add evidence for matching genres
    # ===================================================================

    # --- Concert boosts ---
    concert_obj_boost = _object_boost(yolo_detections, _CONCERT_OBJECTS)
    concert_txt_boost = _keyword_boost(combined_text, _CONCERT_KEYWORDS)
    if concert_obj_boost or concert_txt_boost:
        scores["Concert Photography"] = scores.get("Concert Photography", 0.0) + concert_obj_boost + concert_txt_boost
        evidence_log["concert_boost"] = concert_obj_boost + concert_txt_boost

    # --- Nature boosts ---
    nature_obj_boost = _object_boost(yolo_detections, _NATURE_OBJECTS) if not has_dominant_person else 0.0
    nature_txt_boost = _keyword_boost(combined_text, _NATURE_KEYWORDS)
    if nature_obj_boost or nature_txt_boost:
        scores["Nature Photography"] = scores.get("Nature Photography", 0.0) + nature_obj_boost + nature_txt_boost
        evidence_log["nature_boost"] = nature_obj_boost + nature_txt_boost

    # --- Food boosts ---
    food_obj_boost = _object_boost(yolo_detections, _FOOD_OBJECTS)
    food_txt_boost = _keyword_boost(combined_text, _FOOD_KEYWORDS)
    if food_obj_boost or food_txt_boost:
        scores["Food Photography"] = scores.get("Food Photography", 0.0) + food_obj_boost + food_txt_boost
        evidence_log["food_boost"] = food_obj_boost + food_txt_boost

    # --- Product boosts ---
    product_obj_boost = _object_boost(yolo_detections, _PRODUCT_OBJECTS)
    product_txt_boost = _keyword_boost(combined_text, _PRODUCT_KEYWORDS)
    if product_obj_boost or product_txt_boost:
        scores["Product Photography"] = scores.get("Product Photography", 0.0) + product_obj_boost + product_txt_boost
        evidence_log["product_boost"] = product_obj_boost + product_txt_boost

    # --- Portrait boosts ---
    portrait_txt_boost = _keyword_boost(combined_text, _PORTRAIT_KEYWORDS)
    if portrait_txt_boost:
        scores["Portraits Photography"] = scores.get("Portraits Photography", 0.0) + portrait_txt_boost
        evidence_log["portrait_boost"] = portrait_txt_boost

    # --- Street boosts ---
    street_obj_boost = _object_boost(yolo_detections, _STREET_OBJECTS)
    street_txt_boost = _keyword_boost(combined_text, _STREET_KEYWORDS)
    if street_obj_boost or street_txt_boost:
        scores["Street Photography"] = scores.get("Street Photography", 0.0) + street_obj_boost + street_txt_boost
        evidence_log["street_boost"] = street_obj_boost + street_txt_boost

    # --- Phase 1: Wedding boosts ---
    wedding_obj_boost = _object_boost(yolo_detections, _WEDDING_OBJECTS)
    wedding_txt_boost = _keyword_boost(combined_text, _WEDDING_KEYWORDS)
    if wedding_obj_boost or wedding_txt_boost:
        scores["Wedding Photography"] = scores.get("Wedding Photography", 0.0) + wedding_obj_boost + wedding_txt_boost
        evidence_log["wedding_boost"] = wedding_obj_boost + wedding_txt_boost

    # ===================================================================
    # PHASE 2: CONTRADICTION CHECKS — demote genres that conflict with caption
    # ===================================================================
    has_wedding_words = _has_any_word(combined_text, _WEDDING_KEYWORDS)
    has_person_words = _has_any_word(combined_text, _PERSON_WORDS)
    has_food_words = _has_any_word(combined_text, _FOOD_CONFIRM_WORDS)
    has_food_objects = bool(det_lower & _FOOD_OBJECTS) if det_lower else False
    has_nature_words = _has_any_word(combined_text, _NATURE_CAPTION_WORDS)

    # If caption says wedding but SigLIP2 picked Concert → demote Concert, boost Wedding
    if has_wedding_words:
        if scores.get("Concert Photography", 0) > 0.3:
            scores["Concert Photography"] = max(scores["Concert Photography"] - _DEMOTE, 0.0)
            scores["Wedding Photography"] = scores.get("Wedding Photography", 0.0) + _DEMOTE
            evidence_log["concert_demote_wedding"] = _DEMOTE
        if scores.get("Food Photography", 0) > 0.3:
            scores["Food Photography"] = max(scores["Food Photography"] - _DEMOTE, 0.0)
            scores["Wedding Photography"] = scores.get("Wedding Photography", 0.0) + _DEMOTE
            evidence_log["food_demote_wedding"] = _DEMOTE

    # Phase 3: Food veto — if SigLIP2 says Food but caption has person/portrait
    # words and NO food words and YOLO has no food objects → demote Food
    if scores.get("Food Photography", 0) > 0.3 and not has_wedding_words:
        if has_person_words and not has_food_words and not has_food_objects:
            scores["Food Photography"] = max(scores["Food Photography"] - _DEMOTE, 0.0)
            scores["Portraits Photography"] = scores.get("Portraits Photography", 0.0) + _DEMOTE * 0.5
            evidence_log["food_veto_no_food_evidence"] = _DEMOTE

    # Phase 4: Product-vs-Nature disambiguation — if caption mentions animals,
    # sky, nature but SigLIP2 picked Product → shift score to Nature
    if scores.get("Product Photography", 0) > 0.3:
        if has_nature_words and not _has_any_word(combined_text, _PRODUCT_KEYWORDS):
            shift = min(_DEMOTE, scores.get("Product Photography", 0.0))
            scores["Product Photography"] = max(scores["Product Photography"] - shift, 0.0)
            scores["Nature Photography"] = scores.get("Nature Photography", 0.0) + shift
            evidence_log["product_demote_nature"] = shift

    # ===================================================================
    # SCORING — normalize and pick winner
    # ===================================================================

    # Re-normalize so scores sum to 1
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
        # Low confidence: derive category from title instead of leaving unlabeled
        genre = _title_based_category(title or caption)
        review_status = "title-inferred"
        evidence_log["title_fallback"] = title or caption

    return {
        "genre": genre,
        "confidence": confidence,
        "review_status": review_status,
        "top2": top_k[:2],
        "evidence_log": evidence_log,
    }
