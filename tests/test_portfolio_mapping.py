import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from portfolio_mapping import compute_dest_relpath, map_genre_to_portfolio


class PortfolioMappingTests(unittest.TestCase):
    # --- Safe mappings (no review needed) ---
    def test_safe_mapping_routes_events_to_concert(self):
        result = map_genre_to_portfolio("Events & Music")
        self.assertEqual(result["portfolio_category"], "concert")
        self.assertEqual(result["portfolio_group"], "events")
        self.assertTrue(result["export_include"])
        self.assertFalse(result["needs_review"])

    def test_safe_mapping_routes_food_to_product(self):
        result = map_genre_to_portfolio("Food & Product")
        self.assertEqual(result["portfolio_category"], "product")
        self.assertEqual(result["portfolio_group"], "branding")
        self.assertTrue(result["export_include"])
        self.assertFalse(result["needs_review"])

    def test_safe_mapping_routes_nature_to_nature(self):
        result = map_genre_to_portfolio("Nature & Landscape")
        self.assertEqual(result["portfolio_category"], "nature")
        self.assertEqual(result["portfolio_group"], "author-archive")
        self.assertTrue(result["export_include"])
        self.assertFalse(result["needs_review"])

    # --- Default ambiguous mappings (auto-inferred but needs review) ---
    def test_ambiguous_travel_auto_maps_to_travel_cityscape(self):
        result = map_genre_to_portfolio("Travel & Architecture")
        self.assertEqual(result["portfolio_category"], "travel-cityscape")
        self.assertEqual(result["portfolio_group"], "author-archive")
        self.assertTrue(result["export_include"])
        self.assertTrue(result["needs_review"])
        self.assertEqual(result["mapping_source"], "auto")

    def test_ambiguous_branding_auto_maps_to_portraits(self):
        result = map_genre_to_portfolio("Branding & Portrait")
        self.assertEqual(result["portfolio_category"], "portraits")
        self.assertEqual(result["portfolio_group"], "branding")
        self.assertTrue(result["export_include"])
        self.assertTrue(result["needs_review"])

    def test_ambiguous_street_auto_maps_to_city(self):
        result = map_genre_to_portfolio("Street Documentary")
        self.assertEqual(result["portfolio_category"], "city")
        self.assertEqual(result["portfolio_group"], "author-archive")
        self.assertTrue(result["export_include"])
        self.assertTrue(result["needs_review"])

    # --- Excluded genres (no portfolio bucket) ---
    def test_wedding_defaults_to_exclude(self):
        result = map_genre_to_portfolio("Wedding Photography")
        self.assertEqual(result["portfolio_category"], "exclude")
        self.assertFalse(result["export_include"])
        self.assertTrue(result["needs_review"])

    def test_other_defaults_to_exclude(self):
        result = map_genre_to_portfolio("Other Photography")
        self.assertEqual(result["portfolio_category"], "exclude")
        self.assertFalse(result["export_include"])
        self.assertTrue(result["needs_review"])

    # --- User override takes priority ---
    def test_user_override_takes_priority(self):
        result = map_genre_to_portfolio("Travel & Architecture", user_portfolio_category="city")
        self.assertEqual(result["portfolio_category"], "city")
        self.assertEqual(result["portfolio_group"], "author-archive")
        self.assertTrue(result["export_include"])
        self.assertFalse(result["needs_review"])
        self.assertEqual(result["mapping_source"], "user")

    def test_user_override_exclude_on_ambiguous(self):
        result = map_genre_to_portfolio("Branding & Portrait", user_portfolio_category="exclude")
        self.assertEqual(result["portfolio_category"], "exclude")
        self.assertFalse(result["export_include"])
        self.assertFalse(result["needs_review"])
        self.assertEqual(result["mapping_source"], "user")

    # --- Destination paths ---
    def test_dest_relpath_uses_excluded_folder_for_excluded_items(self):
        relpath = compute_dest_relpath("exclude", "frame.jpg", effective_genre="Wedding Photography")
        self.assertEqual(relpath, "excluded/Wedding Photography/frame.jpg")

    def test_dest_relpath_uses_photos_folder_for_included_items(self):
        relpath = compute_dest_relpath("travel-cityscape", "img.jpg")
        self.assertEqual(relpath, "photos/travel-cityscape/img.jpg")


if __name__ == "__main__":
    unittest.main()
