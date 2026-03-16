import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from genre_decision import make_genre_decision


ALL_GENRES = [
    "Street Photography",
    "Music Photography",
    "Nature Photography",
    "Portrait Photography",
    "Product Photography",
]


def build_siglip(top1, top1_score, top2, top2_score):
    scores = {genre: 0.01 for genre in ALL_GENRES}
    scores[top1] = top1_score
    scores[top2] = top2_score
    top_k = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return {"top_k": top_k}


class GenreDecisionPlanTests(unittest.TestCase):
    def test_architecture_overrides_generic_street_city_scene(self):
        result = make_genre_decision(
            build_siglip("Street Photography", 0.82, "Portrait Photography", 0.11),
            caption="There are two towers that have a clock on each of them.",
            title="Clock towers over a city plaza",
        )

        self.assertEqual(result["genre"], "Architecture Photography")
        self.assertIn("street_demote_architecture", result["evidence_log"])

    def test_explicit_wedding_language_overrides_portrait(self):
        result = make_genre_decision(
            build_siglip("Portrait Photography", 0.78, "Music Photography", 0.12),
            yolo_detections=["person", "person", "wine glass", "cake"],
            caption="Bride and groom share their first dance at the wedding reception.",
        )

        self.assertEqual(result["genre"], "Wedding Photography")
        self.assertIn("wedding_override", result["evidence_log"])

    def test_documentary_market_scene_demotes_product(self):
        result = make_genre_decision(
            build_siglip("Product Photography", 0.74, "Street Photography", 0.18),
            yolo_detections=["person", "person", "bottle"],
            caption="A vendor serves drinks from a busy market street food stall.",
        )

        self.assertEqual(result["genre"], "Street Photography")
        self.assertIn("product_demote_street", result["evidence_log"])

    def test_travel_industrial_scene_falls_to_other(self):
        result = make_genre_decision(
            build_siglip("Nature Photography", 0.76, "Street Photography", 0.14),
            caption="A ship sits in fog near an industrial harbor at dawn.",
            title="Industrial harbor in heavy mist",
        )

        self.assertEqual(result["genre"], "Other Photography")
        self.assertIn("nature_demote_other", result["evidence_log"])

    def test_jewelry_detail_demotes_portrait(self):
        result = make_genre_decision(
            build_siglip("Portrait Photography", 0.70, "Product Photography", 0.20),
            caption="A close-up of a gold necklace and ring jewelry set.",
            title="Gold necklace product detail",
        )

        self.assertEqual(result["genre"], "Product Photography")
        self.assertIn("portrait_demote_product_jewelry", result["evidence_log"])

    def test_street_without_human_context_is_forced_to_review(self):
        result = make_genre_decision(
            build_siglip("Street Photography", 0.90, "Nature Photography", 0.05),
            caption="An empty city street at dawn.",
        )

        self.assertEqual(result["genre"], "Street Photography")
        self.assertEqual(result["review_status"], "review")
        self.assertTrue(result["evidence_log"]["street_requires_human_context"])


if __name__ == "__main__":
    unittest.main()
