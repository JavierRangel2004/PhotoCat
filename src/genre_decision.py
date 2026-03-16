"""
genre_decision.py — Evidence fusion and confidence-gated write policy.

Combines SigLIP2 classification with YOLO object cues, caption text, and OCR text
to produce a final genre label and a write-policy status.

Write policy:
  HIGH  (>= 0.80) → review_status = "auto"          → write genre to XMP
  MEDIUM (0.55-0.79) → review_status = "review"      → write genre + add 'genre-needs-review' tag
  LOW   (< 0.55)  → review_status = "title-inferred" → derive category from title; write + tag

Margin gating: if top1-vs-top2 gap < 0.15, force "review" even if confidence >= HIGH.
"""

from collections import Counter

# Boost amounts applied per detected evidence cue
_BOOST = 0.12
# Negative boost (demotion) for contradiction checks
_DEMOTE = 0.10
# Margin below which an otherwise-auto image is forced to review
_MARGIN_THRESHOLD = 0.15
_STRONG_BOOST = _BOOST * 2
_OVERRIDE_BOOST = _BOOST * 3

# ---------------------------------------------------------------------------
# Object label sets that boost specific genres
# NOTE: "person" intentionally excluded — too generic, biases Music/Portrait
# ---------------------------------------------------------------------------
_MUSIC_OBJECTS = {
    "microphone", "guitar", "drums", "drum", "keyboard", "piano",
    "speaker", "amplifier", "spotlight", "bass", "violin",
    "turntable", "headphones",
}
_NATURE_OBJECTS = {
    "tree", "flower", "bird", "cat", "dog", "horse", "cow",
    "sheep", "elephant", "bear", "zebra", "giraffe", "mountain",
    "plant", "leaf", "grass", "sky",
}
# Product objects include food-related YOLO labels (merged per Phase 1 plan)
_PRODUCT_OBJECTS = {
    "bottle", "cell phone", "laptop", "mouse",
    "book", "clock", "vase", "scissors", "toothbrush",
    "sports ball", "tennis racket", "remote",
    # Food objects merged into Product
    "cake", "donut", "sandwich", "pizza", "hot dog", "carrot", "broccoli",
    "apple", "orange", "banana", "wine glass", "cup", "bowl",
    "fork", "knife", "spoon", "dining table", "oven",
}
_STREET_OBJECTS = {
    "car", "bus", "truck", "motorcycle", "bicycle",
    "traffic light", "stop sign", "parking meter",
    "bench", "backpack", "umbrella", "handbag",
}
_ARCHITECTURE_OBJECTS = {
    "clock",
}
_WEDDING_OBJECTS = {
    "cake", "wine glass", "cup", "dining table", "tie",
}

# ---------------------------------------------------------------------------
# Caption / OCR keyword hints
# ---------------------------------------------------------------------------
_MUSIC_KEYWORDS = {
    "concert", "stage", "mic", "microphone", "guitar", "band", "music",
    "live", "performance", "festival", "musician", "singer", "rapper",
    "dj", "artist backstage", "recording",
}
_NATURE_KEYWORDS = {
    "nature", "forest", "mountain", "river", "lake", "ocean", "wildlife",
    "landscape", "sunset", "sunrise", "tree", "flower", "beach", "field",
}
# Product keywords include food-related terms (merged per Phase 1 plan)
_PRODUCT_KEYWORDS = {
    "product", "bottle", "can", "brand", "studio", "commercial",
    "isolated", "white background", "packaging",
    # Food keywords merged into Product
    "food", "cook", "kitchen", "chef", "cake", "donut", "doughnut",
    "meal", "eat", "dish", "bread", "dough", "bake", "dessert",
    "pastry", "plate", "recipe", "restaurant", "ingredient",
    "chocolate", "chefs",
}
_PORTRAIT_KEYWORDS = {
    "portrait", "face", "person", "smile", "close-up", "headshot", "model",
}
_STREET_KEYWORDS = {
    "street", "city", "urban", "road", "sidewalk", "building", "crowd",
    "candid", "town",
}
_ARCHITECTURE_KEYWORDS = {
    "tower", "clock tower", "clock", "building", "facade", "façade",
    "staircase", "stairs", "archway", "window", "columns", "column",
    "statue", "monument", "hallway", "corridor", "cityscape", "skyline",
    "cathedral", "church", "castle", "bridge", "landmark", "spire",
    "plaza", "square", "gate", "gates", "bell tower",
}
_WEDDING_KEYWORDS = {
    "wedding", "bride", "groom", "bridal", "bouquet", "veil",
    "bridesmaid", "groomsmen", "ceremony", "reception", "newlywed",
    "newlyweds", "wedding party", "wedding dress",
}
_WEDDING_CONTEXT_KEYWORDS = {
    "dance", "dancing", "speech", "toast", "family", "formal", "dress",
    "suit", "kiss", "kissing", "rings", "flowers", "place setting",
    "group photo", "first dance", "reception hall", "couple",
}
_CANDID_STREET_KEYWORDS = {
    "candid", "pedestrian", "commuter", "crosswalk", "public", "street life",
    "busy", "alley", "market", "vendor", "people watching", "public life",
    "documentary", "sidewalk", "crowd",
}
_TRAVEL_OTHER_KEYWORDS = {
    "ship", "boat", "boats", "ferry", "port", "harbor", "harbour", "dock",
    "pier", "maritime", "industrial", "factory", "warehouse", "crane",
    "smokestack", "road", "highway", "travel", "fog", "mist", "minimalist",
    "atmospheric", "harbor view", "shipping",
}
_MARKET_DOCUMENTARY_KEYWORDS = {
    "market", "vendor", "stall", "street food", "worker", "working",
    "selling", "serving", "documentary", "public life", "bazaar",
    "shopfront", "shop front", "food stall",
}
_JEWELRY_KEYWORDS = {
    "ring", "rings", "necklace", "chain", "jewelry", "jewellery",
    "bracelet", "earring", "earrings", "pendant",
}

# Contradiction-check word sets
_PERSON_WORDS = {
    "woman", "man", "girl", "boy", "person", "people", "posing",
    "portrait", "dress", "suit", "wearing",
}
# Nature-indicator words for product disambiguation
_NATURE_CAPTION_WORDS = {
    "shark", "fish", "bird", "moon", "sky", "ocean", "sea", "flying",
    "swimming", "sunset", "sunrise", "mountain", "forest", "wildlife",
    "animal", "manta", "seahorse", "ray",
}
_STRONG_NATURE_WORDS = {
    "wildlife", "forest", "mountain", "flower", "tree", "trees", "river",
    "lake", "waterfall", "jungle", "animal", "bird", "ocean", "sea",
}

HIGH_THRESHOLD = 0.80
MEDIUM_THRESHOLD = 0.50  # lowered from 0.55 — fewer images fall to title-inferred with no caption

# --- Title-based fallback category maps (used when confidence < MEDIUM_THRESHOLD) ---
_TITLE_CATEGORY_RULES = [
    # Wedding kept as fallback-only
    ({"bride", "groom", "wedding", "bridal", "bouquet", "veil", "ceremony",
      "reception", "bridesmaid", "groomsmen", "married"},
     "Wedding Photography"),
    # Food keywords route to Product Photography (merged per Phase 1 plan)
    ({"food", "cook", "kitchen", "chef", "cake", "donut", "doughnut", "meal", "eat", "dish",
      "bread", "dough", "bake", "dessert", "pastry", "plate", "chocolate", "chefs", "frying",
      "ingredients", "stove", "oven", "restaurant"},
     "Product Photography"),
    ({"danc", "perform", "stage", "festival", "show", "sword", "folk", "cosplay",
      "costume", "parade", "cultural", "carnival"},
     "Event Photography"),
    ({"ship", "boat", "boats", "ferry", "port", "harbor", "industrial", "warehouse",
      "dock", "pier", "road", "highway", "travel", "fog", "mist", "minimalist"},
     "Other Photography"),
    # Beach keywords route to Nature Photography (merged per Phase 1 plan)
    ({"beach", "ocean", "sea", "wave", "surf", "coastal", "shore", "bay"},
     "Nature Photography"),
    ({"building", "church", "castle", "bridge", "tower", "landmark", "cathedral",
      "monument", "statue", "architecture", "hallway", "corridor", "facade",
      "staircase", "skyline", "cityscape", "clock"},
     "Architecture Photography"),
    ({"sport", "bike", "skateboard", "football", "run", "jump", "game", "match",
      "soccer", "tennis", "basketball", "swim", "race", "athlete"},
     "Sports Photography"),
    ({"street", "city", "urban", "road", "sidewalk", "alley", "neon", "sign",
      "graffiti", "mural", "market"},
     "Street Photography"),
    ({"portrait", "face", "smile", "headshot", "selfie", "pose", "posing"},
     "Portrait Photography"),
    ({"nature", "forest", "mountain", "river", "lake", "wildlife", "landscape",
      "sunset", "sunrise", "tree", "flower", "field", "garden", "park", "jungle",
      "woods", "waterfall", "cliff", "valley"},
     "Nature Photography"),
    ({"concert", "band", "music", "guitar", "microphone", "singer", "musician",
      "rapper", "dj"},
     "Music Photography"),
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


def _keyword_hits(text, keywords):
    """Count how many keywords appear in text (case-insensitive substring match)."""
    if not text:
        return 0
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


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
    detection_counts = Counter(d.lower() for d in yolo_detections)
    det_lower = set(detection_counts)
    person_count = detection_counts.get("person", 0)
    has_dominant_person = person_count > 0
    has_person_words = _has_any_word(combined_text, _PERSON_WORDS)
    has_nature_words = _has_any_word(combined_text, _NATURE_CAPTION_WORDS)
    strong_street_human_evidence = person_count > 0 and (
        _has_any_word(combined_text, _CANDID_STREET_KEYWORDS) or
        bool(det_lower & _STREET_OBJECTS) or
        person_count > 1
    )

    # ===================================================================
    # POSITIVE BOOSTS — add evidence for matching genres
    # ===================================================================

    # --- Music boosts ---
    music_obj_boost = _object_boost(yolo_detections, _MUSIC_OBJECTS)
    music_txt_boost = _keyword_boost(combined_text, _MUSIC_KEYWORDS)
    if music_obj_boost or music_txt_boost:
        scores["Music Photography"] = scores.get("Music Photography", 0.0) + music_obj_boost + music_txt_boost
        evidence_log["music_boost"] = music_obj_boost + music_txt_boost

    # --- Nature boosts ---
    nature_obj_boost = _object_boost(yolo_detections, _NATURE_OBJECTS) if not has_dominant_person else 0.0
    nature_txt_boost = _keyword_boost(combined_text, _NATURE_KEYWORDS)
    if nature_obj_boost or nature_txt_boost:
        scores["Nature Photography"] = scores.get("Nature Photography", 0.0) + nature_obj_boost + nature_txt_boost
        evidence_log["nature_boost"] = nature_obj_boost + nature_txt_boost

    # --- Product boosts (includes food evidence) ---
    product_obj_boost = _object_boost(yolo_detections, _PRODUCT_OBJECTS)
    product_txt_boost = _keyword_boost(combined_text, _PRODUCT_KEYWORDS)
    if product_obj_boost or product_txt_boost:
        scores["Product Photography"] = scores.get("Product Photography", 0.0) + product_obj_boost + product_txt_boost
        evidence_log["product_boost"] = product_obj_boost + product_txt_boost

    # --- Portrait boosts ---
    portrait_txt_boost = _keyword_boost(combined_text, _PORTRAIT_KEYWORDS)
    if portrait_txt_boost:
        scores["Portrait Photography"] = scores.get("Portrait Photography", 0.0) + portrait_txt_boost
        evidence_log["portrait_boost"] = portrait_txt_boost

    # --- Street boosts ---
    street_obj_boost = _object_boost(yolo_detections, _STREET_OBJECTS)
    street_txt_boost = _keyword_boost(combined_text, _STREET_KEYWORDS)
    if street_obj_boost or street_txt_boost:
        scores["Street Photography"] = scores.get("Street Photography", 0.0) + street_obj_boost + street_txt_boost
        evidence_log["street_boost"] = street_obj_boost + street_txt_boost

    # --- Architecture boosts ---
    architecture_hits = _keyword_hits(combined_text, _ARCHITECTURE_KEYWORDS)
    architecture_obj_boost = _object_boost(yolo_detections, _ARCHITECTURE_OBJECTS)
    architecture_boost = min((architecture_hits * (_BOOST * 0.75)) + architecture_obj_boost, _OVERRIDE_BOOST + (_BOOST * 0.5))
    if architecture_boost:
        scores["Architecture Photography"] = scores.get("Architecture Photography", 0.0) + architecture_boost
        evidence_log["architecture_boost"] = architecture_boost

    # --- Wedding boosts ---
    wedding_hits = _keyword_hits(combined_text, _WEDDING_KEYWORDS)
    wedding_context_hits = _keyword_hits(combined_text, _WEDDING_CONTEXT_KEYWORDS)
    wedding_obj_boost = _object_boost(yolo_detections, _WEDDING_OBJECTS) if person_count > 0 else 0.0
    explicit_wedding = wedding_hits > 0
    wedding_context = person_count >= 2 and wedding_context_hits >= 2 and wedding_obj_boost > 0
    if explicit_wedding or wedding_context:
        wedding_boost = wedding_obj_boost
        if explicit_wedding:
            wedding_boost += min(
                _OVERRIDE_BOOST + max(0, wedding_hits - 1) * (_BOOST * 0.25),
                _OVERRIDE_BOOST + _BOOST,
            )
        else:
            wedding_boost += _STRONG_BOOST
        scores["Wedding Photography"] = scores.get("Wedding Photography", 0.0) + wedding_boost
        evidence_log["wedding_boost"] = wedding_boost

    # --- Other boosts for travel / industrial scenes ---
    travel_other_hits = _keyword_hits(combined_text, _TRAVEL_OTHER_KEYWORDS)
    if travel_other_hits and architecture_hits < 2:
        other_boost = min(travel_other_hits * (_BOOST * 0.6), _OVERRIDE_BOOST)
        scores["Other Photography"] = scores.get("Other Photography", 0.0) + other_boost
        evidence_log["other_boost"] = other_boost

    # ===================================================================
    # CONTRADICTION CHECKS — demote genres that conflict with evidence
    # ===================================================================
    has_person_words = _has_any_word(combined_text, _PERSON_WORDS)
    has_nature_words = _has_any_word(combined_text, _NATURE_CAPTION_WORDS)

    # Nature-vs-Portrait disambiguation: if SigLIP2 picked Portrait but
    # caption lacks person words and YOLO detects nature objects → flip to Nature
    top_sorted = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    if len(top_sorted) >= 2:
        top_label, top_score = top_sorted[0]
        second_label, second_score = top_sorted[1]
        margin = top_score - second_score

        # Portrait wins but Nature is close — check for nature evidence
        if top_label == "Portrait Photography" and second_label == "Nature Photography" and margin < 0.15:
            if not has_person_words and (bool(det_lower & _NATURE_OBJECTS) or has_nature_words):
                scores["Portrait Photography"] = max(scores["Portrait Photography"] - _DEMOTE, 0.0)
                scores["Nature Photography"] = scores.get("Nature Photography", 0.0) + _DEMOTE
                evidence_log["portrait_demote_nature"] = _DEMOTE

        # Portrait wins but Street is close — check for street objects
        if top_label == "Portrait Photography" and second_label == "Street Photography" and margin < 0.10:
            if bool(det_lower & _STREET_OBJECTS):
                half_demote = _DEMOTE * 0.5
                scores["Portrait Photography"] = max(scores["Portrait Photography"] - half_demote, 0.0)
                scores["Street Photography"] = scores.get("Street Photography", 0.0) + half_demote
                evidence_log["portrait_demote_street"] = half_demote

        # Music context beats Portrait: stage/concert headshots are Music Photography
        if top_label in ("Portrait Photography", "Music Photography") and \
           second_label in ("Portrait Photography", "Music Photography"):
            music_evidence = _has_any_word(combined_text, {"stage", "concert", "performance", "live", "festival"})
            if music_evidence:
                scores["Music Photography"] = scores.get("Music Photography", 0.0) + _BOOST * 0.5
                evidence_log["music_context_boost"] = _BOOST * 0.5

    # Product-vs-Nature disambiguation — if caption mentions animals/sky/nature
    # but SigLIP2 picked Product → shift score to Nature
    # Structure-dominant city scenes should not default to Street unless there
    # is clear candid human evidence.
    if architecture_boost and (architecture_hits >= 2 or not strong_street_human_evidence):
        shift = min(
            (_STRONG_BOOST if architecture_hits >= 2 else _DEMOTE) + (architecture_boost * 0.5),
            scores.get("Street Photography", 0.0),
        )
        if shift > 0:
            scores["Street Photography"] = max(scores.get("Street Photography", 0.0) - shift, 0.0)
            scores["Architecture Photography"] = scores.get("Architecture Photography", 0.0) + shift
            evidence_log["street_demote_architecture"] = shift

    # Explicit wedding semantics should dominate sub-scenes like portraits,
    # dancing, product details, or reception decor.
    if explicit_wedding or wedding_context:
        wedding_shift = _DEMOTE if explicit_wedding else _DEMOTE * 0.7
        for label in (
            "Portrait Photography",
            "Music Photography",
            "Product Photography",
            "Nature Photography",
            "Street Photography",
        ):
            reduction = min(scores.get(label, 0.0), wedding_shift)
            if reduction > 0:
                scores[label] = max(scores.get(label, 0.0) - reduction, 0.0)
                scores["Wedding Photography"] = scores.get("Wedding Photography", 0.0) + reduction
        evidence_log["wedding_override"] = "explicit" if explicit_wedding else "context"

    if scores.get("Product Photography", 0) > 0.3:
        if has_nature_words and not _has_any_word(combined_text, _PRODUCT_KEYWORDS):
            shift = min(_DEMOTE, scores.get("Product Photography", 0.0))
            scores["Product Photography"] = max(scores["Product Photography"] - shift, 0.0)
            scores["Nature Photography"] = scores.get("Nature Photography", 0.0) + shift
            evidence_log["product_demote_nature"] = shift

    # Market scenes with active people are documentary/street, not clean
    # product hero shots.
    documentary_hits = _keyword_hits(combined_text, _MARKET_DOCUMENTARY_KEYWORDS)
    if documentary_hits and person_count > 0 and scores.get("Product Photography", 0.0) > 0:
        shift = min(
            _STRONG_BOOST + min(documentary_hits, 3) * (_BOOST * 0.15) + (0.08 if person_count > 1 else 0.0),
            scores["Product Photography"],
        )
        scores["Product Photography"] = max(scores["Product Photography"] - shift, 0.0)
        scores["Street Photography"] = scores.get("Street Photography", 0.0) + shift
        evidence_log["product_demote_street"] = shift

    # Jewelry detail shots are usually product/editorial objects, not portraits.
    if _has_any_word(combined_text, _JEWELRY_KEYWORDS):
        shift = min(scores.get("Portrait Photography", 0.0), _DEMOTE * (2 if not has_person_words else 1))
        if shift > 0:
            scores["Portrait Photography"] = max(scores["Portrait Photography"] - shift, 0.0)
            scores["Product Photography"] = scores.get("Product Photography", 0.0) + shift + (_BOOST * 1.25)
            evidence_log["portrait_demote_product_jewelry"] = shift

    # Travel, maritime, and industrial scenic frames should fall back toward
    # Other until a dedicated travel taxonomy exists.
    if travel_other_hits and not _has_any_word(combined_text, _STRONG_NATURE_WORDS):
        shift = min(scores.get("Nature Photography", 0.0), _STRONG_BOOST if travel_other_hits >= 2 else _DEMOTE)
        if shift > 0:
            scores["Nature Photography"] = max(scores.get("Nature Photography", 0.0) - shift, 0.0)
            scores["Other Photography"] = scores.get("Other Photography", 0.0) + shift
            evidence_log["nature_demote_other"] = shift

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

    # Compute margin between top-1 and top-2
    margin = (top_k[0][1] - top_k[1][1]) if len(top_k) >= 2 else 1.0

    # Write policy
    if confidence >= HIGH_THRESHOLD:
        # Margin gating: if top1 vs top2 gap is too small, force review
        if margin < _MARGIN_THRESHOLD:
            review_status = "review"
            evidence_log["margin_demotion"] = margin
        else:
            review_status = "auto"
    elif confidence >= MEDIUM_THRESHOLD:
        review_status = "review"
    else:
        # Low confidence: try title/caption keywords first.
        # If no keywords match (returns "Other Photography") and there's no text to
        # work from, use the model's top-1 prediction with "review" status so the
        # image still lands in a real genre folder rather than "Other Photography".
        fallback_text = title or caption
        inferred = _title_based_category(fallback_text)
        if inferred != top_k[0][0] and top_k[0][1] >= MEDIUM_THRESHOLD * 0.85:
            genre = top_k[0][0]
            review_status = "review"
            evidence_log["rule_top1_preferred"] = inferred
        elif inferred == "Other Photography" and not fallback_text.strip():
            # No caption/title available (genre-only mode) — trust model top-1
            genre = top_k[0][0]
            review_status = "review"
            evidence_log["model_top1_fallback"] = confidence
        else:
            genre = inferred
            review_status = "title-inferred"
            evidence_log["title_fallback"] = fallback_text

    if genre == "Street Photography" and not strong_street_human_evidence:
        review_status = "review"
        evidence_log["street_requires_human_context"] = True

    return {
        "genre": genre,
        "confidence": confidence,
        "review_status": review_status,
        "top2": top_k[:2],
        "evidence_log": evidence_log,
    }
