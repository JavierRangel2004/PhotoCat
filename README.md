# PhotoCat

**PhotoCat** is an AI-powered photo categorization tool that analyzes, classifies, and organizes your image library using state-of-the-art vision models. It automatically sorts photos into genre categories (Street, Concert, Nature, Portraits, Product, Food, and more), generates descriptive metadata, and moves files into organized directories -- all running **locally on your hardware** with no cloud APIs.

Built for photographers, digital archivists, and anyone with large Lightroom exports or photo libraries that need fast, automated organization.

## Key Features

- **Genre Classification** -- Classifies images into photography genres using [SigLIP2](https://huggingface.co/google/siglip2-base-patch16-224) zero-shot vision-language embeddings with evidence fusion from YOLO object detection and BLIP captioning
- **Automatic File Organization** -- Moves categorized photos into genre subdirectories (`--organize`) so you can go from one flat export folder to sorted categories in minutes
- **Audit CSV Reports** -- Generates a CSV with 1st/2nd predictions, confidence scores, and review status for every image -- useful for quality review before committing to organization
- **Confidence-Gated Decisions** -- Three-tier write policy (auto / review / title-inferred) prevents low-confidence labels from being written without review
- **Object Detection** -- YOLOv8 real-time object detection provides supporting evidence for classification
- **Image Captioning** -- BLIP model generates descriptive captions used as titles and classification evidence
- **Exposure & Blur Analysis** -- Flags underexposed, overexposed, and blurry images
- **XMP Metadata Writing** -- Writes ratings, tags, titles, and genre labels into XMP sidecar files compatible with Lightroom, Capture One, and other DAM software
- **GPU Accelerated** -- Automatic detection of CUDA (NVIDIA) and MPS (Apple Silicon) for fast batch processing
- **Batch Processing** -- Processes hundreds of images sequentially with ~1s/image on GPU

## Quick Start

### Prerequisites

- Python 3.8+
- Git
- (Optional) NVIDIA GPU with CUDA for acceleration
- (Optional) [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for text detection

### Installation

```bash
git clone https://github.com/JavierRangel2004/PhotoCat.git
cd PhotoCat
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

For CUDA GPU support (recommended):
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

### Basic Usage

**Dry run** (analyze only, no file changes):
```bash
python src/main.py --input-dir /path/to/photos
```

**Classify and organize into folders**:
```bash
python src/main.py --input-dir /path/to/photos --organize
```

**Genre-only mode** (faster, skips blur/exposure/OCR/captioning):
```bash
python src/main.py --input-dir /path/to/photos --genre-only --organize
```

**Full pipeline with XMP writing**:
```bash
python src/main.py --input-dir /path/to/photos --write-xmp --organize
```

## CLI Reference

| Flag | Default | Description |
|------|---------|-------------|
| `--input-dir` | `images/` | Directory of images to process |
| `--recursive` | `false` | Recurse into subdirectories |
| `--extensions` | `.jpg,.jpeg,.png,.tiff,.webp,.cr2,.cr3,.dng` | Comma-separated file extensions |
| `--write-xmp` | `false` | Write XMP sidecar files with metadata |
| `--genre-only` | `false` | Run only genre classification (skip blur, exposure, OCR, captioning) |
| `--organize` | `false` | Move images into genre subdirectories after classification |
| `--csv` | `<input-dir>/photocat_audit.csv` | Path for the audit CSV report |
| `--min-confidence` | `0.55` | Minimum confidence threshold for genre output |
| `--workers` | `1` | Parallel workers (keep at 1 for GPU) |

## How It Works

### Pipeline Stages

1. **Image Loading** -- Reads JPG, PNG, TIFF, RAW (CR2/CR3/DNG) with preprocessing and noise reduction
2. **Quality Checks** -- Blur detection (Laplacian variance) and exposure analysis
3. **Object Detection** -- YOLOv8 identifies objects as supporting evidence for genre classification
4. **OCR** -- Tesseract extracts text for brand/scene detection
5. **Captioning** -- BLIP generates a natural language description
6. **Genre Classification** -- SigLIP2 zero-shot classifier with prompt ensembles, fused with YOLO + caption evidence
7. **Decision Gate** -- Confidence-based write policy determines if genre is written automatically, flagged for review, or inferred from title
8. **Output** -- CSV audit report + optional XMP writing + optional file organization

### Genre Categories

| Category | Description |
|----------|-------------|
| Street Photography | Urban scenes, candid city life |
| Concert Photography | Live music, stages, performers |
| Nature Photography | Landscapes, wildlife, plants |
| Portraits Photography | People-focused, posed or close-up |
| Product Photography | Commercial objects, studio-style |
| Food Photography | Dishes, cooking, culinary scenes |
| Wedding Photography | Bride, groom, ceremonies, receptions |
| Architecture Photography | Buildings, landmarks, structures (title-inferred) |
| Beach Photography | Coastal, ocean, shore scenes (title-inferred) |
| Event Photography | Festivals, parades, performances (title-inferred) |
| Sports Photography | Athletic activities (title-inferred) |

### Quality Rating (1-5)

The rating is computed from image quality signals, not genre classification:

| Factor | Effect |
|--------|--------|
| **Composition** | Number of detected objects: 0 = 1pt, 1 = 2pt, 2+ = 3pt |
| **Blur** | Blurry image: -1pt |
| **Exposure** | Under/overexposed: -1pt; Normal exposure: +1pt |

Final rating is clamped to 1-5. Only available in full pipeline mode (skipped in `--genre-only`).

### Confidence Tiers

| Tier | Confidence | Behavior |
|------|-----------|----------|
| **HIGH** | >= 0.80 | Genre written automatically (`status=auto`) |
| **MEDIUM** | 0.55 - 0.79 | Genre written with `genre-needs-review` tag (`status=review`) |
| **LOW** | < 0.55 | Genre inferred from image title keywords (`status=title-inferred`) |

### File Organization

When `--organize` is used, PhotoCat creates subdirectories named after each genre category inside your input directory and moves the classified images there:

```
input-dir/
  Street Photography/
    IMG_001.jpg
    IMG_003.jpg
  Nature Photography/
    IMG_002.jpg
  Portraits Photography/
    IMG_004.jpg
  photocat_audit.csv
```

These category directories are **reserved names** -- PhotoCat automatically skips them when scanning for images, so you can safely re-run on the same directory without double-processing already-categorized photos.

### Audit CSV

Every run generates a CSV report (by default at `<input-dir>/photocat_audit.csv`) with columns:

| Column | Description |
|--------|-------------|
| `filename` | Image file name |
| `rating` | Quality rating (1-5) |
| `final_genre` | Final assigned genre (matches the directory the file is moved to) |
| `review_status` | `auto`, `review`, `title-inferred`, or `skipped` |
| `model_1st` | Raw model top prediction (before contradiction checks / title fallback) |
| `model_1st_conf` | Confidence score for raw top prediction |
| `model_2nd` | Raw model second prediction |
| `model_2nd_conf` | Confidence score for second prediction |
| `title` | Generated image title/caption |

## Project Structure

```
PhotoCat/
  README.md
  requirements.txt
  .gitignore
  src/
    main.py              # Entry point and batch pipeline
    cli.py               # Argument parser and image collection
    device.py            # Hardware detection (CUDA/MPS/CPU)
    scene_classifier.py  # SigLIP2 zero-shot genre classifier
    genre_decision.py    # Evidence fusion and confidence gating
    image_captioning.py  # BLIP image captioning
    object_detection.py  # YOLOv8 object detection (singleton)
    image_analysis.py    # Blur, exposure, color analysis
    metadata_writer.py   # XMP sidecar file writer
    utilities.py         # Helper functions
  docs/
    RUFLO_IMPLEMENTATION_GUIDE.md
```

## Models Used

| Model | Purpose | License |
|-------|---------|---------|
| [SigLIP2](https://huggingface.co/google/siglip2-base-patch16-224) | Primary genre classifier (zero-shot) | Apache-2.0 |
| [BLIP](https://huggingface.co/Salesforce/blip-image-captioning-large) | Image captioning | BSD-3 |
| [YOLOv8n](https://docs.ultralytics.com/) | Object detection | AGPL-3.0 |

All models run locally. No data is sent to external services.

## Performance

Real-world benchmarks from tested hardware:

| Hardware | Mode | Speed | Notes |
|----------|------|-------|-------|
| NVIDIA RTX 3060 Ti (8GB VRAM) | Full pipeline | **~1.1 s/image** | 274 images in 305s |
| NVIDIA RTX 3060 Ti (8GB VRAM) | Genre-only | **~0.3 s/image** | Skips YOLO, OCR, BLIP |
| Apple Silicon M-series (MPS) | Full pipeline | **~3 min/image** | YOLO on MPS is the bottleneck (1-2s inference vs 10ms on CUDA) |
| Apple Silicon M-series (MPS) | Genre-only | **~5-10 s/image** | Recommended mode for Mac — skips YOLO entirely |
| CPU only | Full pipeline | **~5-10 s/image** | Not recommended for large batches |

> **Why is Mac so much slower?** YOLO inference on MPS runs at 1200-2000ms per image vs 10-12ms on CUDA — a ~170x difference. Additionally, CUDA enables float16 precision which halves memory bandwidth. If you're on Mac, use `--genre-only` to skip the YOLO bottleneck entirely.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

## License

This project is licensed under the [MIT License](LICENSE).

## Contact

- **Email:** [inspec_jrm@gmail.com](mailto:inspec_jrm@gmail.com)

---

*Built with PyTorch, Hugging Face Transformers, and Ultralytics.*
