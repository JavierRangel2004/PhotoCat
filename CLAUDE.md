# CLAUDE.md

This repository must use a Ruflo-first workflow for non-trivial work.

In this project, "Ruflo" means the Claude Flow V3 + RuVector + agent swarm stack already configured in:

- `.mcp.json`
- `.claude/`
- `.claude-flow/`

## Non-Negotiable Rules

1. Do not start feature work in direct single-agent coding mode.
2. Do not use `claude-flow claude spawn` for implementation in this repository.
3. The top-level assistant acts as the operator and coordinator, not the primary coder.
4. All feature work must go through agents and swarm orchestration first:
   - research
   - architecture
   - implementation
   - testing
   - review
   - documentation
5. Before code changes, store the task goal, constraints, and model decision in Claude Flow memory.
6. For this repository, prefer `npx @claude-flow/cli@latest ...` over ad hoc custom wrappers.

## Current Project Context

PhotoCat is currently a batch pipeline driven by [src/main.py](/C:/Users/javar/GITHUB/PhotoCat/src/main.py). The active stages are:

1. Load image from `images/`
2. Blur and exposure checks
3. YOLO object detection via [src/object_detection.py](/C:/Users/javar/GITHUB/PhotoCat/src/object_detection.py)
4. OCR with Tesseract
5. Captioning with BLIP via [src/image_captioning.py](/C:/Users/javar/GITHUB/PhotoCat/src/image_captioning.py)
6. Rating, tags, title generation
7. XMP writing via [src/metadata_writer.py](/C:/Users/javar/GITHUB/PhotoCat/src/metadata_writer.py)

Important implementation detail: YOLO is currently loaded inside `detect_objects()` on every call, which is inefficient for large batches.

## Target Feature

Add support for analyzing a user-specified directory of Lightroom-exported JPG files and classify each image into one of:

- Street Photography
- Concert Photography
- Nature Photography
- Portraits Photography
- Product Photography

## Recommended Technical Direction

Do not treat this as an object-detection-only problem. These categories are scene and intent categories, so the primary classifier should be a vision-language embedding model, with detector/caption outputs used as supporting evidence.

Recommended stack:

1. Primary classifier: SigLIP 2 zero-shot or embedding-based classifier
2. Secondary evidence: Florence-2 caption / scene description
3. Object cues: YOLO11 or YOLO-World for stage, microphone, person, tree, product-like object evidence
4. Optional tie-breaker only: Qwen2.5-VL-3B or InternVL3-2B

Use a small labeled local dataset from the user's own catalog to calibrate or train a lightweight classifier on top of embeddings before trusting automatic metadata writes.

Full guide: [docs/RUFLO_IMPLEMENTATION_GUIDE.md](/C:/Users/javar/GITHUB/PhotoCat/docs/RUFLO_IMPLEMENTATION_GUIDE.md)

## Ruflo Execution Workflow

### 1. Start and validate Claude Flow

```bash
npx @claude-flow/cli@latest doctor --fix
npx @claude-flow/cli@latest memory init --force
npx @claude-flow/cli@latest swarm init --topology hierarchical --max-agents 7 --strategy specialized
```

### 2. Store the task before implementation

```bash
npx @claude-flow/cli@latest memory store --key "photocat/goal" --value "Add local JPG directory genre classification for street, concert, nature, portraits, product." --namespace project
npx @claude-flow/cli@latest memory store --key "photocat/constraint" --value "Free, local-only inference on user hardware. No paid APIs." --namespace project
```

### 3. Run agent phases in order

1. `planner` or `researcher`: model selection and success criteria
2. `system-architect`: pipeline placement, CLI, module boundaries
3. `coder`: implementation only after architecture is approved
4. `tester`: evaluation harness, confidence thresholds, regression checks
5. `reviewer`: verify no metadata regressions and no direct-mode drift
6. `api-docs` or documenter: usage guide and examples

### 4. Required implementation checkpoints

1. Research checkpoint
   Save model choice, fallback models, and reasons in memory.
2. Architecture checkpoint
   Save module plan and CLI contract in memory.
3. Evaluation checkpoint
   Save per-class metrics before enabling automatic XMP writes for the new genre label.

## Default Task Template

Use this kind of swarm task description:

```text
Research and implement a local-only photography genre classifier for PhotoCat.
Constraints:
- JPG input from arbitrary user directory
- categories: street, concert, nature, portraits, product
- free local models only
- use SigLIP2 as primary classifier candidate
- use Florence-2 and YOLO11/YOLO-World as supporting signals
- no direct single-agent coding
- store decisions in Claude Flow memory
```

## Anti-Drift Guardrails

1. No coding until research and architecture outputs exist.
2. No replacing the whole pipeline with a large VLM by default.
3. No writing genre metadata automatically until confidence thresholds are defined.
4. No silent fallback to generic "best guess" labels without confidence recording.
5. No hard-coding `images/` as the only input path for the new feature.

## Project-Specific Priorities

1. Local execution over cloud accuracy.
2. Predictable batch throughput over flashy one-off demos.
3. Confidence + reviewability over forced labels.
4. Backward-compatible XMP writing.
5. Reuse existing dependencies where reasonable, but replace weak model choices if they block quality.
