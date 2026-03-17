import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from genre_decision import make_genre_decision


ALL_GENRES = [
    "Branding & Portrait",
    "Events & Music",
    "Street Documentary",
    "Food & Product",
    "Nature & Landscape",
    "Travel & Architecture",
]


def build_siglip(top1, top1_score, top2, top2_score):
    scores = {genre: 0.01 for genre in ALL_GENRES}
    scores[top1] = top1_score
    scores[top2] = top2_score
    top_k = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return {"top_k": top_k}


class GenreDecisionPhase2Tests(unittest.TestCase):
    """Tests for the Phase 2 taxonomy migration (6 categories + Other gate)."""

    # ------------------------------------------------------------------
    # Travel & Architecture (formerly Architecture Photography)
    # ------------------------------------------------------------------
    def test_travel_architecture_overrides_street_for_city_scene(self):
        result = make_genre_decision(
            build_siglip("Street Documentary", 0.82, "Branding & Portrait", 0.11),
            caption="There are two towers that have a clock on each of them.",
            title="Clock towers over a city plaza",
        )
        self.assertEqual(result["genre"], "Travel & Architecture")
        self.assertIn("street_demote_architecture", result["evidence_log"])

    def test_travel_cityscape_classified_correctly(self):
        result = make_genre_decision(
            build_siglip("Travel & Architecture", 0.65, "Street Documentary", 0.20),
            caption="A panoramic view of a cathedral and historic plaza at sunset.",
            title="Cathedral skyline panorama",
        )
        self.assertEqual(result["genre"], "Travel & Architecture")

    # ------------------------------------------------------------------
    # Wedding (title-fallback only, but explicit keywords override)
    # ------------------------------------------------------------------
    def test_explicit_wedding_language_overrides_portrait(self):
        result = make_genre_decision(
            build_siglip("Branding & Portrait", 0.78, "Events & Music", 0.12),
            yolo_detections=["person", "person", "wine glass", "cake"],
            caption="Bride and groom share their first dance at the wedding reception.",
        )
        self.assertEqual(result["genre"], "Wedding Photography")
        self.assertIn("wedding_override", result["evidence_log"])

    def test_formal_group_portrait_without_explicit_wedding_still_routes_to_wedding(self):
        result = make_genre_decision(
            build_siglip("Branding & Portrait", 0.56, "Events & Music", 0.32),
            yolo_detections=["person", "person", "person", "person", "person", "person"],
            caption="There are a lot of women standing together in dresses for a group portrait.",
        )
        self.assertEqual(result["genre"], "Wedding Photography")
        self.assertEqual(result["evidence_log"]["wedding_override"], "context")
        self.assertIn("wedding_context_signals", result["evidence_log"])

    def test_formal_mens_group_routes_to_wedding_context(self):
        result = make_genre_decision(
            build_siglip("Branding & Portrait", 0.67, "Events & Music", 0.25),
            yolo_detections=["person", "person", "person", "person", "tie", "tie"],
            caption="A group of men in suits and ties posing for a picture.",
        )
        self.assertEqual(result["genre"], "Wedding Photography")
        self.assertEqual(result["evidence_log"]["wedding_override"], "context")

    # ------------------------------------------------------------------
    # Street Documentary (market scene demotes product)
    # ------------------------------------------------------------------
    def test_documentary_market_scene_demotes_product(self):
        result = make_genre_decision(
            build_siglip("Food & Product", 0.74, "Street Documentary", 0.18),
            yolo_detections=["person", "person", "bottle"],
            caption="A vendor serves drinks from a busy market street food stall.",
        )
        self.assertEqual(result["genre"], "Street Documentary")
        self.assertIn("product_demote_street", result["evidence_log"])

    def test_street_documentary_market_scene(self):
        result = make_genre_decision(
            build_siglip("Street Documentary", 0.70, "Food & Product", 0.15),
            yolo_detections=["person", "person", "backpack"],
            caption="A busy market vendor selling goods on a crowded sidewalk.",
        )
        self.assertEqual(result["genre"], "Street Documentary")

    # ------------------------------------------------------------------
    # Other Photography gate
    # ------------------------------------------------------------------
    def test_travel_industrial_scene_falls_to_other(self):
        result = make_genre_decision(
            build_siglip("Nature & Landscape", 0.76, "Street Documentary", 0.14),
            caption="A ship sits in fog near an industrial harbor at dawn.",
            title="Industrial harbor in heavy mist",
        )
        self.assertEqual(result["genre"], "Other Photography")
        self.assertIn("nature_demote_other", result["evidence_log"])

    def test_other_gate_fires_on_ambiguous_scores(self):
        """All categories score roughly equally → Other Photography via score gate."""
        # Build an evenly-distributed SigLIP result
        even_score = 1.0 / len(ALL_GENRES)
        scores = {genre: even_score for genre in ALL_GENRES}
        top_k = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        siglip = {"top_k": top_k}

        result = make_genre_decision(siglip, caption="", title="")
        self.assertEqual(result["genre"], "Other Photography")
        self.assertIn("other_gate", result["evidence_log"])

    # ------------------------------------------------------------------
    # Branding & Portrait
    # ------------------------------------------------------------------
    def test_branding_portrait_chef_session(self):
        result = make_genre_decision(
            build_siglip("Branding & Portrait", 0.72, "Food & Product", 0.15),
            yolo_detections=["person"],
            caption="A chef working in a kitchen preparing dishes for a branding session.",
            title="Chef portrait in kitchen",
        )
        self.assertEqual(result["genre"], "Branding & Portrait")
        self.assertIn("branding_portrait_boost", result["evidence_log"])

    # ------------------------------------------------------------------
    # Events & Music
    # ------------------------------------------------------------------
    def test_events_music_concert_photo(self):
        result = make_genre_decision(
            build_siglip("Events & Music", 0.75, "Branding & Portrait", 0.12),
            yolo_detections=["person", "microphone"],
            caption="A singer performing on stage at a live concert with bright spotlights.",
        )
        self.assertEqual(result["genre"], "Events & Music")
        self.assertIn("music_boost", result["evidence_log"])

    def test_audio_production_scene_demotes_product_to_events(self):
        result = make_genre_decision(
            build_siglip("Food & Product", 0.99, "Events & Music", 0.01),
            yolo_detections=["bottle"],
            caption="There is a close up of a sound board with a laptop in the background.",
            title="Sound board and laptop backstage",
        )
        self.assertEqual(result["genre"], "Events & Music")
        self.assertIn("product_demote_music_production", result["evidence_log"])

    # ------------------------------------------------------------------
    # Jewelry → Food & Product
    # ------------------------------------------------------------------
    def test_jewelry_detail_demotes_portrait(self):
        result = make_genre_decision(
            build_siglip("Branding & Portrait", 0.70, "Food & Product", 0.20),
            caption="A close-up of a gold necklace and ring jewelry set.",
            title="Gold necklace product detail",
        )
        self.assertEqual(result["genre"], "Food & Product")
        self.assertIn("portrait_demote_product_jewelry", result["evidence_log"])

    def test_jewelry_rule_not_triggered_by_during_word(self):
        result = make_genre_decision(
            build_siglip("Branding & Portrait", 0.72, "Events & Music", 0.16),
            yolo_detections=["person"],
            caption="A performer speaks during a concert intermission.",
        )
        self.assertNotIn("portrait_demote_product_jewelry", result["evidence_log"])

    def test_nature_boost_not_triggered_by_street_word(self):
        result = make_genre_decision(
            build_siglip("Street Documentary", 0.74, "Branding & Portrait", 0.12),
            yolo_detections=["person", "person"],
            caption="Two people crossing the street near a bus stop.",
        )
        self.assertNotIn("nature_boost", result["evidence_log"])

    # ------------------------------------------------------------------
    # Street Documentary without human context → forced review
    # ------------------------------------------------------------------
    def test_street_without_human_context_is_forced_to_review(self):
        result = make_genre_decision(
            build_siglip("Street Documentary", 0.90, "Nature & Landscape", 0.05),
            caption="An empty city street at dawn.",
        )
        self.assertEqual(result["genre"], "Street Documentary")
        self.assertEqual(result["review_status"], "review")
        self.assertTrue(result["evidence_log"]["street_requires_human_context"])

    # ------------------------------------------------------------------
    # Nature & Landscape
    # ------------------------------------------------------------------
    def test_nature_landscape_clear_image(self):
        result = make_genre_decision(
            build_siglip("Nature & Landscape", 0.85, "Travel & Architecture", 0.08),
            caption="A mountain landscape with wildflowers in a meadow at sunset.",
        )
        self.assertEqual(result["genre"], "Nature & Landscape")

    # ------------------------------------------------------------------
    # Other Photography always gets review status
    # ------------------------------------------------------------------
    def test_other_photography_always_review(self):
        """Other Photography should never have 'auto' review_status."""
        result = make_genre_decision(
            build_siglip("Nature & Landscape", 0.76, "Street Documentary", 0.14),
            caption="A ship sits in fog near an industrial harbor at dawn.",
            title="Industrial harbor in heavy mist",
        )
        self.assertEqual(result["genre"], "Other Photography")
        self.assertEqual(result["review_status"], "review")


if __name__ == "__main__":
    unittest.main()
