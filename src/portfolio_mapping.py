"""
portfolio_mapping.py -- Map PhotoCat review genres to Photo Portfolio category slugs.

PhotoCat and Photo Portfolio use different taxonomies on purpose. This module
is the bridge between them. It takes a corrected review genre (the
"effective_genre") and produces the exact directory slug and group that the
Photo Portfolio repo expects.

Safe automatic mappings (one-to-one, no human decision needed):
    Events & Music       -> concert
    Food & Product       -> product
    Nature & Landscape   -> nature

Ambiguous mappings (require a user_portfolio_category override or default
to exclude with needs_review=True):
    Branding & Portrait  -> portraits | exclude  (default: needs review)
    Street Documentary   -> city | exclude        (default: needs review)
    Travel & Architecture -> city | travel-cityscape | exclude (default: needs review)
    Wedding Photography  -> exclude               (default, no portfolio category)
    Other Photography    -> exclude               (always)

Portfolio groups (derived from portfolio_category):
    branding       -> portraits, product
    events         -> concert
    author-archive -> nature, city, travel-cityscape
    exclude        -> exclude
"""

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PORTFOLIO_CATEGORIES = [
    "portraits",
    "concert",
    "city",
    "nature",
    "product",
    "travel-cityscape",
]

# Genres that map safely without any human override.
SAFE_MAPPINGS = {
    "Events & Music": "concert",
    "Food & Product": "product",
    "Nature & Landscape": "nature",
}

# Genres where automatic mapping is risky -- a user_portfolio_category
# override is expected. Without one, the image defaults to "exclude"
# with needs_review=True.
AMBIGUOUS_GENRES = {
    "Branding & Portrait",
    "Street Documentary",
    "Travel & Architecture",
    "Wedding Photography",
    "Other Photography",
}

# portfolio_category -> portfolio_group
PORTFOLIO_GROUPS = {
    "portraits": "branding",
    "product": "branding",
    "concert": "events",
    "nature": "author-archive",
    "city": "author-archive",
    "travel-cityscape": "author-archive",
    "exclude": "exclude",
}

# All valid slugs including "exclude" (used for validation).
_VALID_CATEGORIES = set(PORTFOLIO_CATEGORIES) | {"exclude"}


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def map_genre_to_portfolio(effective_genre, user_portfolio_category=""):
    """
    Map a review genre to portfolio output.

    Args:
        effective_genre:          The corrected/final PhotoCat genre string.
        user_portfolio_category:  Optional user-supplied portfolio slug override.
                                  If provided and valid, it takes priority over
                                  any automatic mapping.

    Returns:
        dict with keys:
            portfolio_category  (str)  -- the slug ("concert", "exclude", etc.)
            portfolio_group     (str)  -- derived group ("events", "exclude", etc.)
            export_include      (bool) -- True when category != "exclude"
            mapping_source      (str)  -- "auto" | "user" | "default-exclude"
            needs_review        (bool) -- True when ambiguous and no user override
    """
    user_cat = (user_portfolio_category or "").strip().lower()

    # --- Path 1: explicit user override ---
    if user_cat and user_cat in _VALID_CATEGORIES:
        category = user_cat
        source = "user"
        needs_review = False

    # --- Path 2: safe automatic mapping ---
    elif effective_genre in SAFE_MAPPINGS:
        category = SAFE_MAPPINGS[effective_genre]
        source = "auto"
        needs_review = False

    # --- Path 3: ambiguous genre without override -> exclude ---
    elif effective_genre in AMBIGUOUS_GENRES:
        category = "exclude"
        source = "default-exclude"
        needs_review = True

    # --- Path 4: unknown genre -> exclude ---
    else:
        category = "exclude"
        source = "default-exclude"
        needs_review = True

    group = PORTFOLIO_GROUPS.get(category, "exclude")
    export_include = category != "exclude"

    return {
        "portfolio_category": category,
        "portfolio_group": group,
        "export_include": export_include,
        "mapping_source": source,
        "needs_review": needs_review,
    }


def compute_dest_relpath(portfolio_category, filename, effective_genre=""):
    """
    Compute the destination relative path for an image.

    Included images:   photos/<portfolio_category>/<filename>
    Excluded images:   excluded/<effective_genre>/<filename>

    Args:
        portfolio_category:  The resolved portfolio slug.
        filename:            Just the file name (no directory component).
        effective_genre:     The PhotoCat genre (used as a sub-folder under
                             excluded/ so excluded images are still grouped).

    Returns:
        str -- forward-slash relative path, e.g. "photos/concert/IMG_001.jpg"
    """
    if portfolio_category == "exclude":
        genre_folder = effective_genre or "unknown"
        return f"excluded/{genre_folder}/{filename}"
    return f"photos/{portfolio_category}/{filename}"


def get_mapping_summary(rows):
    """
    Summarise portfolio mapping results for a batch of images.

    Args:
        rows: list of dicts, each containing at minimum:
              - effective_genre  (str)
              - user_portfolio_category (str, optional)

    Returns:
        dict with keys:
            total               (int)
            counts_by_category  (dict[str, int])
            counts_by_group     (dict[str, int])
            needs_review_count  (int)
            excluded_count      (int)
    """
    counts_by_category = {}
    counts_by_group = {}
    needs_review_count = 0
    excluded_count = 0

    for row in rows:
        genre = row.get("effective_genre", "")
        user_cat = row.get("user_portfolio_category", "")

        result = map_genre_to_portfolio(genre, user_cat)

        category = result["portfolio_category"]
        group = result["portfolio_group"]

        counts_by_category[category] = counts_by_category.get(category, 0) + 1
        counts_by_group[group] = counts_by_group.get(group, 0) + 1

        if result["needs_review"]:
            needs_review_count += 1
        if not result["export_include"]:
            excluded_count += 1

    return {
        "total": len(rows),
        "counts_by_category": counts_by_category,
        "counts_by_group": counts_by_group,
        "needs_review_count": needs_review_count,
        "excluded_count": excluded_count,
    }
