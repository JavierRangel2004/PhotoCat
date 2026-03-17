"""
scene_classifier.py — Primary genre classifier using SigLIP2.

Loads the model ONCE at init. Call classify_scene() per image.
Primary model: google/siglip2-base-patch16-224 (Apache-2.0)
"""

import torch
from PIL import Image
from transformers import pipeline
from device import get_device

# Phase 2 taxonomy: 6 primary genres aligned with JRMGraphy commercial strategy.
# Each category has 3 prompts: commercial-intent, compositional, and context.
# Wedding remains title-fallback only (not in SigLIP2 primary classification).
GENRE_PROMPTS = {
    "Branding & Portrait": [
        "a portrait or personal branding photograph of a person as the main subject",
        "documentary portrait of a person working, creating, or practicing their craft",
        "close-up or environmental portrait of a creative professional or individual",
    ],
    "Events & Music": [
        "a concert or live music performance photograph with stage lighting",
        "event photography at a cultural gathering, festival, or live show",
        "documentary photograph of a music performance or cultural event",
    ],
    "Street Documentary": [
        "candid street photography of people going about daily life in a public place",
        "documentary photograph of spontaneous real-life moments on a city street or market",
        "unposed photograph of real people in an urban public space or alleyway",
    ],
    "Food & Product": [
        "a food or product photograph showing a meal, dish, or commercial object as the main subject",
        "documentary or commercial photograph focused on food preparation or a product",
        "still-life or editorial food photography with food or objects as the main subject",
    ],
    "Nature & Landscape": [
        "a nature photograph of wildlife, plants, forests, mountains, or natural scenery",
        "landscape photography of a natural outdoor environment without human structures",
        "outdoor nature photograph of animals, flora, geological formations, or ocean",
    ],
    "Travel & Architecture": [
        "an architectural or travel photograph of a building, landmark, or urban structure",
        "cityscape or travel photography featuring monuments, plazas, or historic buildings",
        "photograph of architectural details, facades, skylines, or historic landmarks",
    ],
}

MODEL_ID = "google/siglip2-base-patch16-224"


class SceneClassifier:
    def __init__(self, device=None):
        self.device = device or get_device()
        print(f"[SceneClassifier] Loading {MODEL_ID} on {self.device} ...")

        if self.device == "cuda":
            pipe_device = 0
        elif self.device == "mps":
            pipe_device = "mps"
        else:
            pipe_device = -1

        self.pipe = pipeline(
            task="zero-shot-image-classification",
            model=MODEL_ID,
            device=pipe_device,
            torch_dtype=torch.float16 if self.device == "cuda" else None,
        )

        # GemmaTokenizer (used by SigLIP2) has no predefined model_max_length.
        # The pipeline internally converts padding=True → padding="max_length",
        # which silently disables padding when max_length is unset, causing a
        # tensor-shape crash when prompts tokenise to different lengths.
        # Setting an explicit cap here enables padding to work correctly.
        if getattr(self.pipe.tokenizer, "model_max_length", None) is None or \
                self.pipe.tokenizer.model_max_length > 1_000_000:
            self.pipe.tokenizer.model_max_length = 64

        # Flat list of all prompts, and a mapping from prompt → genre
        self.labels = []
        self._label_to_genre = {}
        for genre, prompts in GENRE_PROMPTS.items():
            for prompt in prompts:
                self.labels.append(prompt)
                self._label_to_genre[prompt] = genre

        print("[SceneClassifier] Ready.")

    def classify_scene(self, image):
        """
        Args:
            image: PIL.Image (RGB) or numpy array (BGR, as returned by OpenCV).

        Returns:
            dict with keys:
                genre_label (str)
                confidence  (float, 0-1)
                top_k       (list of (label, score) sorted descending)
                supporting_evidence (dict — averaged scores per genre)
        """
        if not isinstance(image, Image.Image):
            # Assume OpenCV BGR numpy array
            image = Image.fromarray(image[:, :, ::-1])

        with torch.no_grad():
            results = self.pipe(image, candidate_labels=self.labels, padding=True, truncation=True)
        # results: [{"score": float, "label": str}, ...] sorted descending by score

        # Aggregate scores per genre by averaging over its prompts
        genre_score_sums = {genre: 0.0 for genre in GENRE_PROMPTS}
        genre_prompt_counts = {genre: len(prompts) for genre, prompts in GENRE_PROMPTS.items()}

        for item in results:
            genre = self._label_to_genre[item["label"]]
            genre_score_sums[genre] += item["score"]

        genre_scores = {
            genre: genre_score_sums[genre] / genre_prompt_counts[genre]
            for genre in GENRE_PROMPTS
        }

        top_k = sorted(genre_scores.items(), key=lambda x: x[1], reverse=True)
        genre_label = top_k[0][0]
        confidence = top_k[0][1]

        return {
            "genre_label": genre_label,
            "confidence": confidence,
            "top_k": top_k,
            "supporting_evidence": {"siglip2_genre_scores": genre_scores},
        }


# Module-level singleton (lazy init)
_classifier_instance = None


def get_classifier(device=None):
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = SceneClassifier(device=device)
    return _classifier_instance
