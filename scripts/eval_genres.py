"""
eval_genres.py — Genre classification evaluation harness.

Walks the 5 labeled folders in Photo-Portfolio, runs SceneClassifier on each
image, and writes output/genre_review.csv.

Usage:
    python scripts/eval_genres.py \
        --portfolio-dir ../Photo-Portfolio/public/photos \
        --output output/genre_review.csv

Folder → label mapping:
    city/       → Urban / Street Photography
    concert/    → Music Photography
    nature/     → Nature Photography
    portraits/  → Portrait Photography
    product/    → Product Photography
"""

import argparse
import csv
import os
import sys

from PIL import Image
from sklearn.metrics import classification_report, f1_score

# Allow importing from src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from scene_classifier import SceneClassifier
from genre_decision import make_genre_decision

FOLDER_TO_LABEL = {
    "city": "Urban / Street Photography",
    "concert": "Music Photography",
    "nature": "Nature Photography",
    "portraits": "Portrait Photography",
    "product": "Product Photography",
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp"}


def collect_samples(portfolio_dir):
    samples = []
    for folder, true_label in FOLDER_TO_LABEL.items():
        folder_path = os.path.join(portfolio_dir, folder)
        if not os.path.isdir(folder_path):
            print(f"[WARN] Folder not found: {folder_path}")
            continue
        for fname in sorted(os.listdir(folder_path)):
            ext = os.path.splitext(fname)[1].lower()
            if ext in IMAGE_EXTENSIONS:
                samples.append((os.path.join(folder_path, fname), true_label))
    return samples


def _warn_if_low_vram():
    """Print a warning when free VRAM is likely insufficient for the full pipeline."""
    try:
        import torch
        if torch.cuda.is_available():
            free_bytes, total_bytes = torch.cuda.mem_get_info()
            free_gb = free_bytes / 1e9
            total_gb = total_bytes / 1e9
            print(f"[eval] GPU VRAM: {free_gb:.1f} GB free / {total_gb:.1f} GB total")
            if free_gb < 2.5:
                print(
                    f"[WARN] Only {free_gb:.1f} GB VRAM free. "
                    "This eval uses SigLIP2 only (~400 MB) and should be fine, "
                    "but running main.py (full pipeline) may OOM. "
                    "Use --genre-only for the full pipeline on low-VRAM machines."
                )
    except Exception:
        pass  # Non-fatal — VRAM check is advisory only


def run_eval(portfolio_dir, output_csv, device=None):
    _warn_if_low_vram()
    samples = collect_samples(portfolio_dir)
    if not samples:
        print("[ERROR] No images found. Check --portfolio-dir.")
        sys.exit(1)

    print(f"[eval] Found {len(samples)} images across {len(FOLDER_TO_LABEL)} classes.")

    classifier = SceneClassifier(device=device)

    os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)

    rows = []
    true_labels = []
    pred_labels = []

    for i, (img_path, true_label) in enumerate(samples, 1):
        try:
            image = Image.open(img_path).convert("RGB")
        except Exception as e:
            print(f"[SKIP] {img_path}: {e}")
            continue

        siglip_result = classifier.classify_scene(image)
        decision = make_genre_decision(siglip_result)

        top2 = siglip_result["top_k"][:2]
        top2_alt = top2[1][0] if len(top2) > 1 else ""

        rows.append({
            "filename": os.path.relpath(img_path, portfolio_dir),
            "true_label": true_label,
            "predicted_label": decision["genre"],
            "confidence": f"{decision['confidence']:.4f}",
            "top2_alternative": top2_alt,
            "review_status": decision["review_status"],
        })
        true_labels.append(true_label)
        pred_labels.append(decision["genre"])

        if i % 10 == 0 or i == len(samples):
            print(f"  [{i}/{len(samples)}] {os.path.basename(img_path)} → {decision['genre']} ({decision['confidence']:.2f}, {decision['review_status']})")

    # Write CSV
    fieldnames = ["filename", "true_label", "predicted_label", "confidence", "top2_alternative", "review_status"]
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n[eval] Results written to {output_csv}")

    # Print classification report
    all_labels = list(FOLDER_TO_LABEL.values())
    print("\n=== Classification Report ===")
    print(classification_report(true_labels, pred_labels, labels=all_labels, zero_division=0))

    macro_f1 = f1_score(true_labels, pred_labels, labels=all_labels, average="macro", zero_division=0)
    per_class_f1 = f1_score(true_labels, pred_labels, labels=all_labels, average=None, zero_division=0)

    print("=== Per-class F1 ===")
    for label, score in zip(all_labels, per_class_f1):
        flag = "  OK" if score >= 0.75 else "  BELOW THRESHOLD"
        print(f"  {label:<28} {score:.3f}{flag}")

    print(f"\n=== Macro F1: {macro_f1:.3f} (target >= 0.85) ===")

    if macro_f1 >= 0.85 and all(s >= 0.75 for s in per_class_f1):
        print("[PASS] Thresholds met — safe to enable automatic XMP genre writes.")
    else:
        print("[HOLD] Thresholds NOT met — do not enable automatic XMP writes yet.")

    # Per-class confusion summary
    from collections import Counter
    print("\n=== Per-class Confusion Summary ===")
    for label in all_labels:
        indices = [i for i, t in enumerate(true_labels) if t == label]
        if not indices:
            continue
        misclassified = Counter(
            pred_labels[i] for i in indices if pred_labels[i] != label
        )
        if misclassified:
            top_confusions = misclassified.most_common(3)
            confusion_str = ", ".join(f"{lbl}={cnt}" for lbl, cnt in top_confusions)
            print(f"  {label:<28} confused with: {confusion_str}")
        else:
            print(f"  {label:<28} no misclassifications")

    # Confidence distribution summary
    auto_count = sum(1 for r in rows if r["review_status"] == "auto")
    review_count = sum(1 for r in rows if r["review_status"] == "review")
    skip_count = sum(1 for r in rows if r["review_status"] == "skip")
    total = len(rows)
    print(f"\n=== Write-policy distribution ===")
    print(f"  auto:   {auto_count}/{total} ({100*auto_count/total:.1f}%)")
    print(f"  review: {review_count}/{total} ({100*review_count/total:.1f}%)")
    print(f"  skip:   {skip_count}/{total} ({100*skip_count/total:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Evaluate PhotoCat genre classifier on Photo-Portfolio dataset.")
    parser.add_argument(
        "--portfolio-dir",
        default=os.path.join(os.path.dirname(__file__), "..", "..", "Photo-Portfolio", "public", "photos"),
        help="Path to Photo-Portfolio/public/photos (contains city/, concert/, etc.)",
    )
    parser.add_argument(
        "--output",
        default=os.path.join(os.path.dirname(__file__), "..", "output", "genre_review.csv"),
        help="Path for output CSV file.",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Device for model inference: 'cpu', 'cuda', or None for auto-detect.",
    )
    args = parser.parse_args()

    run_eval(
        portfolio_dir=os.path.abspath(args.portfolio_dir),
        output_csv=os.path.abspath(args.output),
        device=args.device,
    )


if __name__ == "__main__":
    main()
