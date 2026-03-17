import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from portfolio_mapping import compute_dest_relpath, map_genre_to_portfolio


class PortfolioMappingTests(unittest.TestCase):
    def test_safe_mapping_routes_events_to_concert(self):
        result = map_genre_to_portfolio("Events & Music")
        self.assertEqual(result["portfolio_category"], "concert")
        self.assertEqual(result["portfolio_group"], "events")
        self.assertTrue(result["export_include"])
        self.assertFalse(result["needs_review"])

    def test_ambiguous_mapping_defaults_to_exclude_until_override(self):
        result = map_genre_to_portfolio("Travel & Architecture")
        self.assertEqual(result["portfolio_category"], "exclude")
        self.assertFalse(result["export_include"])
        self.assertTrue(result["needs_review"])

    def test_user_override_takes_priority(self):
        result = map_genre_to_portfolio("Travel & Architecture", user_portfolio_category="travel-cityscape")
        self.assertEqual(result["portfolio_category"], "travel-cityscape")
        self.assertEqual(result["portfolio_group"], "author-archive")
        self.assertTrue(result["export_include"])
        self.assertFalse(result["needs_review"])

    def test_dest_relpath_uses_excluded_folder_for_excluded_items(self):
        relpath = compute_dest_relpath("exclude", "frame.jpg", effective_genre="Wedding Photography")
        self.assertEqual(relpath, "excluded/Wedding Photography/frame.jpg")


if __name__ == "__main__":
    unittest.main()
