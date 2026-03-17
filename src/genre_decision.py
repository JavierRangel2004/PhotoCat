"""
genre_decision.py — Evidence fusion and confidence-gated write policy.

Combines SigLIP2 classification with YOLO object cues, caption text, and OCR text
to produce a final genre label and a write-policy status.

Phase 2 taxonomy (6 primary + 1 fallback):
  Branding & Portrait | Events & Music | Street Documentary
  Food & Product | Nature & Landscape | Travel & Architecture
  Other Photography (algorithmic fallback)

Write policy:
  HIGH  (>= 0.80) → review_status = "auto"          → write genre to XMP
  MEDIUM (0.50-0.79) → review_status = "review"      → write genre + add 'genre-needs-review' tag
  LOW   (< 0.50)  → review_status = "title-inferred" → derive category from title; write + tag

Margin gating: if top1-vs-top2 gap < 0.15, force "review" even if confidence >= HIGH.

Other Photography gate:
  top-1 < 0.30 after normalization → Other (score too low)
  margin < 0.10 AND top-1 < 0.50   → Other (margin too narrow)
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

# Other Photography algorithmic gate thresholds
_OTHER_SCORE_GATE = 0.30   # if top-1 < this → Other
_OTHER_MARGIN_GATE = 0.10  # if margin < this AND top-1 < 0.50 → Other

# ---------------------------------------------------------------------------
# Object label sets that boost specific genres
# NOTE: "person" intentionally excluded — too generic, biases multiple genres
# ---------------------------------------------------------------------------
_EVENTS_MUSIC_OBJECTS = {
    "microphone", "guitar", "drums", "drum", "keyboard", "piano",
    "speaker", "amplifier", "spotlight", "bass", "violin",
    "turntable", "headphones",
}
_NATURE_OBJECTS = {
    "tree", "flower", "bird", "cat", "dog", "horse", "cow",
    "sheep", "elephant", "bear", "zebra", "giraffe", "mountain",
    "plant", "leaf", "grass", "sky",
}
# Food & Product objects include food-related YOLO labels
_FOOD_PRODUCT_OBJECTS = {
    "bottle", "cell phone", "laptop", "mouse",
    "book", "vase", "scissors", "toothbrush",
    "sports ball", "tennis racket", "remote",
    # Food objects
    "cake", "donut", "sandwich", "pizza", "hot dog", "carrot", "broccoli",
    "apple", "orange", "banana", "wine glass", "cup", "bowl",
    "fork", "knife", "spoon", "dining table", "oven",
}
_STREET_OBJECTS = {
    "car", "bus", "truck", "motorcycle", "bicycle",
    "traffic light", "stop sign", "parking meter",
    "bench", "backpack", "umbrella", "handbag",
}
_TRAVEL_ARCHITECTURE_OBJECTS = {
    "clock",  # clock towers
}
_WEDDING_OBJECTS = {
    "cake", "wine glass", "cup", "dining table", "tie",
}

# ---------------------------------------------------------------------------
# Caption / OCR keyword hints
# ---------------------------------------------------------------------------
_EVENTS_MUSIC_KEYWORDS = {
    "concert", "stage", "mic", "microphone", "guitar", "band", "music",
    "live", "performance", "festival", "musician", "singer", "rapper",
    "dj", "artist backstage", "recording",
}
_NATURE_KEYWORDS = {
    "nature", "forest", "mountain", "river", "lake", "ocean", "wildlife",
    "landscape", "sunset", "sunrise", "tree", "flower", "beach", "field",
}
# Food & Product keywords
_FOOD_PRODUCT_KEYWORDS = {
    "product", "bottle", "can", "brand", "studio", "commercial",
    "isolated", "white background", "packaging",
    # Food keywords
    "food", "cook", "kitchen", "chef", "cake", "donut", "doughnut",
    "meal", "eat", "dish", "bread", "dough", "bake", "dessert",
    "pastry", "plate", "recipe", "restaurant", "ingredient",
    "chocolate", "chefs",
}
_BRANDING_PORTRAIT_KEYWORDS = {
    "portrait", "face", "person", "smile", "close-up", "headshot", "model",
}
_BRANDING_PROFESSIONAL_KEYWORDS = {
    "chef", "barista", "artist", "photographer", "musician",
    "entrepreneur", "creative", "professional", "craftsman", "artisan",
    "tailor", "tattooist", "trainer", "performer", "designer",
    "working", "crafting", "creating", "branding",
}
_STREET_KEYWORDS = {
    "street", "city", "urban", "road", "sidewalk", "building", "crowd",
    "candid", "town",
}
_TRAVEL_ARCHITECTURE_KEYWORDS = {
    "tower", "clock tower", "clock", "building", "facade", "façade",
    "staircase", "stairs", "archway", "window", "columns", "column",
    "statue", "monument", "hallway", "corridor", "cityscape", "skyline",
    "cathedral", "church", "castle", "bridge", "landmark", "spire",
    "plaza", "square", "gate", "gates", "bell tower",
    # Travel terms now included as primary evidence
    "travel", "city view", "rooftop", "panorama", "aerial",
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
MEDIUM_THRESHOLD = 0.50

# --- Title-based fallback category maps (used when confidence < MEDIUM_THRESHOLD) ---
_TITLE_CATEGORY_RULES = [
    # Wedding kept as fallback-only
    ({"bride", "groom", "wedding", "bridal", "bouquet", "veil", "ceremony",
      "reception", "bridesmaid", "groomsmen", "married"},
     "Wedding Photography"),
    # Food keywords route to Food & Product
    ({"food", "cook", "kitchen", "chef", "cake", "donut", "doughnut", "meal", "eat", "dish",
      "bread", "dough", "bake", "dessert", "pastry", "plate", "chocolate", "chefs", "frying",
      "ingredients", "stove", "oven", "restaurant"},
     "Food & Product"),
    ({"danc", "perform", "stage", "festival", "show", "sword", "folk", "cosplay",
      "costume", "parade", "cultural", "carnival", "concert", "band", "music",
      "guitar", "microphone", "singer", "musician", "rapper", "dj"},
     "Events & Music"),
    ({"ship", "boat", "boats", "ferry", "port", "harbor", "industrial", "warehouse",
      "dock", "pier", "road", "highway", "fog", "mist", "minimalist"},
     "Other Photography"),
    # Beach keywords route to Nature & Landscape
    ({"beach", "ocean", "sea", "wave", "surf", "coastal", "shore", "bay"},
     "Nature & Landscape"),
    # Architecture/travel keywords route to Travel & Architecture
    ({"building", "church", "castle", "bridge", "tower", "landmark", "cathedral",
      "monument", "statue", "architecture", "hallway", "corridor", "facade",
      "staircase", "skyline", "cityscape", "clock", "travel", "rooftop", "panorama"},
     "Travel & Architecture"),
    ({"sport", "bike", "skateboard", "football", "run", "jump", "game", "match",
      "soccer", "tennis", "basketball", "swim", "race", "athlete"},
     "Other Photography"),  # Sports → Other (no dedicated category)
    ({"street", "city", "urban", "sidewalk", "alley", "neon", "sign",
      "graffiti", "mural", "market"},
     "Street Documentary"),
    ({"portrait", "face", "smile", "headshot", "selfie", "pose", "posing",
      "branding", "chef", "barista", "artisan", "craftsman"},
     "Branding & Portrait"),
    ({"nature", "forest", "mountain", "river", "lake", "wildlife", "landscape",
      "sunset", "sunrise", "tree", "flower", "field", "garden", "park", "jungle",
      "woods", "waterfall", "cliff", "valley"},
     "Nature & Landscape"),
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
    boosted_genres = set()  # tracks genres that received positive evidence
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

    # --- Events & Music boosts ---
    music_obj_boost = _object_boost(yolo_detections, _EVENTS_MUSIC_OBJECTS)
    music_txt_boost = _keyword_boost(combined_text, _EVENTS_MUSIC_KEYWORDS)
    if music_obj_boost or music_txt_boost:
        scores["Events & Music"] = scores.get("Events & Music", 0.0) + music_obj_boost + music_txt_boost
        evidence_log["music_boost"] = music_obj_boost + music_txt_boost
        boosted_genres.add("Events & Music")

    # --- Nature & Landscape boosts ---
    nature_obj_boost = _object_boost(yolo_detections, _NATURE_OBJECTS) if not has_dominant_person else 0.0
    nature_txt_boost = _keyword_boost(combined_text, _NATURE_KEYWORDS)
    if nature_obj_boost or nature_txt_boost:
        scores["Nature & Landscape"] = scores.get("Nature & Landscape", 0.0) + nature_obj_boost + nature_txt_boost
        evidence_log["nature_boost"] = nature_obj_boost + nature_txt_boost
        boosted_genres.add("Nature & Landscape")

    # --- Food & Product boosts ---
    product_obj_boost = _object_boost(yolo_detections, _FOOD_PRODUCT_OBJECTS)
    product_txt_boost = _keyword_boost(combined_text, _FOOD_PRODUCT_KEYWORDS)
    if product_obj_boost or product_txt_boost:
        scores["Food & Product"] = scores.get("Food & Product", 0.0) + product_obj_boost + product_txt_boost
        evidence_log["product_boost"] = product_obj_boost + product_txt_boost
        boosted_genres.add("Food & Product")

    # --- Branding & Portrait boosts ---
    portrait_txt_boost = _keyword_boost(combined_text, _BRANDING_PORTRAIT_KEYWORDS)
    branding_txt_boost = _keyword_boost(combined_text, _BRANDING_PROFESSIONAL_KEYWORDS)
    total_branding_boost = portrait_txt_boost + branding_txt_boost
    # Extra boost when branding keywords + person detected together
    if branding_txt_boost and has_dominant_person:
        total_branding_boost += _BOOST * 0.5
    if total_branding_boost:
        scores["Branding & Portrait"] = scores.get("Branding & Portrait", 0.0) + total_branding_boost
        evidence_log["branding_portrait_boost"] = total_branding_boost
        boosted_genres.add("Branding & Portrait")

    # --- Street Documentary boosts ---
    street_obj_boost = _object_boost(yolo_detections, _STREET_OBJECTS)
    street_txt_boost = _keyword_boost(combined_text, _STREET_KEYWORDS)
    if street_obj_boost or street_txt_boost:
        scores["Street Documentary"] = scores.get("Street Documentary", 0.0) + street_obj_boost + street_txt_boost
        evidence_log["street_boost"] = street_obj_boost + street_txt_boost
        boosted_genres.add("Street Documentary")

    # --- Travel & Architecture boosts (now PRIMARY, not just a shift) ---
    architecture_hits = _keyword_hits(combined_text, _TRAVEL_ARCHITECTURE_KEYWORDS)
    architecture_obj_boost = _object_boost(yolo_detections, _TRAVEL_ARCHITECTURE_OBJECTS)
    architecture_boost = min((architecture_hits * (_BOOST * 0.75)) + architecture_obj_boost, _OVERRIDE_BOOST + (_BOOST * 0.5))
    if architecture_boost:
        scores["Travel & Architecture"] = scores.get("Travel & Architecture", 0.0) + architecture_boost
        evidence_log["architecture_boost"] = architecture_boost
        boosted_genres.add("Travel & Architecture")

    # --- Wedding boosts (title-fallback only, but still participates in scoring when explicit) ---
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

    # Branding-vs-Nature: if SigLIP2 picked Branding but caption lacks person
    # words and YOLO detects nature objects → flip to Nature
    top_sorted = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    if len(top_sorted) >= 2:
        top_label, top_score = top_sorted[0]
        second_label, second_score = top_sorted[1]
        margin = top_score - second_score

        # Branding wins but Nature is close — check for nature evidence
        if top_label == "Branding & Portrait" and second_label == "Nature & Landscape" and margin < 0.15:
            if not has_person_words and (bool(det_lower & _NATURE_OBJECTS) or has_nature_words):
                scores["Branding & Portrait"] = max(scores["Branding & Portrait"] - _DEMOTE, 0.0)
                scores["Nature & Landscape"] = scores.get("Nature & Landscape", 0.0) + _DEMOTE
                evidence_log["portrait_demote_nature"] = _DEMOTE

        # Branding wins but Street is close — check for street objects
        if top_label == "Branding & Portrait" and second_label == "Street Documentary" and margin < 0.10:
            if bool(det_lower & _STREET_OBJECTS):
                half_demote = _DEMOTE * 0.5
                scores["Branding & Portrait"] = max(scores["Branding & Portrait"] - half_demote, 0.0)
                scores["Street Documentary"] = scores.get("Street Documentary", 0.0) + half_demote
                evidence_log["portrait_demote_street"] = half_demote

        # Music context beats Portrait: stage/concert headshots are Events & Music
        if top_label in ("Branding & Portrait", "Events & Music") and \
           second_label in ("Branding & Portrait", "Events & Music"):
            music_evidence = _has_any_word(combined_text, {"stage", "concert", "performance", "live", "festival"})
            if music_evidence:
                scores["Events & Music"] = scores.get("Events & Music", 0.0) + _BOOST * 0.5
                evidence_log["music_context_boost"] = _BOOST * 0.5

    # Food & Product-vs-Nature disambiguation — if caption mentions animals/sky/nature
    # but SigLIP2 picked Food & Product → shift score to Nature
    if scores.get("Food & Product", 0) > 0.3:
        if has_nature_words and not _has_any_word(combined_text, _FOOD_PRODUCT_KEYWORDS):
            shift = min(_DEMOTE, scores.get("Food & Product", 0.0))
            scores["Food & Product"] = max(scores["Food & Product"] - shift, 0.0)
            scores["Nature & Landscape"] = scores.get("Nature & Landscape", 0.0) + shift
            evidence_log["product_demote_nature"] = shift

    # Structure-dominant city scenes should route to Travel & Architecture,
    # not Street Documentary, unless there is clear candid human evidence.
    if architecture_boost and (architecture_hits >= 2 or not strong_street_human_evidence):
        shift = min(
            (_STRONG_BOOST if architecture_hits >= 2 else _DEMOTE) + (architecture_boost * 0.5),
            scores.get("Street Documentary", 0.0),
        )
        if shift > 0:
            scores["Street Documentary"] = max(scores.get("Street Documentary", 0.0) - shift, 0.0)
            scores["Travel & Architecture"] = scores.get("Travel & Architecture", 0.0) + shift
            evidence_log["street_demote_architecture"] = shift

    # Explicit wedding semantics should dominate sub-scenes
    if explicit_wedding or wedding_context:
        wedding_shift = _DEMOTE if explicit_wedding else _DEMOTE * 0.7
        for label in (
            "Branding & Portrait",
            "Events & Music",
            "Food & Product",
            "Nature & Landscape",
            "Street Documentary",
        ):
            reduction = min(scores.get(label, 0.0), wedding_shift)
            if reduction > 0:
                scores[label] = max(scores.get(label, 0.0) - reduction, 0.0)
                scores["Wedding Photography"] = scores.get("Wedding Photography", 0.0) + reduction
        evidence_log["wedding_override"] = "explicit" if explicit_wedding else "context"

    # Market scenes with active people are documentary/street, not clean
    # product hero shots.
    documentary_hits = _keyword_hits(combined_text, _MARKET_DOCUMENTARY_KEYWORDS)
    if documentary_hits and person_count > 0 and scores.get("Food & Product", 0.0) > 0:
        shift = min(
            _STRONG_BOOST + min(documentary_hits, 3) * (_BOOST * 0.15) + (0.08 if person_count > 1 else 0.0),
            scores["Food & Product"],
        )
        scores["Food & Product"] = max(scores["Food & Product"] - shift, 0.0)
        scores["Street Documentary"] = scores.get("Street Documentary", 0.0) + shift
        evidence_log["product_demote_street"] = shift
        boosted_genres.add("Street Documentary")

    # Jewelry detail shots are usually product/editorial objects, not portraits.
    if _has_any_word(combined_text, _JEWELRY_KEYWORDS):
        shift = min(scores.get("Branding & Portrait", 0.0), _DEMOTE * (2 if not has_person_words else 1))
        if shift > 0:
            scores["Branding & Portrait"] = max(scores["Branding & Portrait"] - shift, 0.0)
            scores["Food & Product"] = scores.get("Food & Product", 0.0) + shift + (_BOOST * 1.25)
            evidence_log["portrait_demote_product_jewelry"] = shift

    # Travel, maritime, and industrial scenic frames should fall back toward
    # Other when they don't match Travel & Architecture.
    if travel_other_hits and not _has_any_word(combined_text, _STRONG_NATURE_WORDS):
        shift = min(scores.get("Nature & Landscape", 0.0), _STRONG_BOOST if travel_other_hits >= 2 else _DEMOTE)
        if shift > 0:
            scores["Nature & Landscape"] = max(scores.get("Nature & Landscape", 0.0) - shift, 0.0)
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

    # ===================================================================
    # OTHER PHOTOGRAPHY GATE — algorithmic fallback for ambiguous images
    # Applied AFTER normalization, BEFORE write policy
    # ===================================================================
    if confidence < _OTHER_SCORE_GATE:
        genre = "Other Photography"
        evidence_log["other_gate"] = {"reason": "score_too_low", "max_score": confidence}
        # Force review for Other
        review_status = "review"
    elif margin < _OTHER_MARGIN_GATE and confidence < 0.50 and genre not in boosted_genres:
        # Only fire margin gate when the winner has NO explicit evidence support.
        # If evidence boosts pushed a genre to the top, trust it despite narrow margin.
        genre = "Other Photography"
        evidence_log["other_gate"] = {"reason": "margin_too_narrow", "margin": margin}
        review_status = "review"
    else:
        # Standard write policy
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

    # Street Documentary without human context → force review
    if genre == "Street Documentary" and not strong_street_human_evidence:
        review_status = "review"
        evidence_log["street_requires_human_context"] = True

    # Other Photography always gets review status (never auto)
    if genre == "Other Photography":
        review_status = "review"

    return {
        "genre": genre,
        "confidence": confidence,
        "review_status": review_status,
        "top2": top_k[:2],
        "evidence_log": evidence_log,
    }
