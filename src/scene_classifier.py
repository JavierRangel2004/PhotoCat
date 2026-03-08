"""
scene_classifier.py — Primary genre classifier using SigLIP2.

Loads the model ONCE at init. Call classify_scene() per image.
Primary model: google/siglip2-base-patch16-224 (Apache-2.0)
"""

import torch
from PIL import Image
from transformers import pipeline
from device import get_device

# Phase 1 taxonomy: 5 primary genres with refined prompt ensembles.
# Food & Wedding removed from primary SigLIP2 classification (demoted to
# title-fallback only) to sharpen softmax distribution for core categories.
GENRE_PROMPTS = {
    "Urban / Street Photography": [
        "a street photograph in an urban city environment",
        "candid street photography with people in a city or town",
        "documentary urban photo of city life, buildings, and streets",
    ],
    "Music Photography": [
        "a concert photograph with stage lighting and musicians",
        "live music performance photography on stage",
        "musician portrait or band promotional photograph",
    ],
    "Nature Photography": [
        "a nature photograph of landscape, plants, or wildlife without people as the main subject",
        "outdoor nature scenery photography of mountains, forests, or water",
        "landscape or wildlife photograph in a natural setting",
    ],
    "Portrait Photography": [
        "a portrait photograph focused on a person as the main subject",
        "portrait photography with deliberate subject emphasis and posing",
        "close-up or environmental portrait of a person",
    ],
    "Product Photography": [
        "a product photograph with isolated commercial presentation",
        "product photography showing a commercial object as the main subject",
        "studio-style or commercial product shot with clean background",
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
