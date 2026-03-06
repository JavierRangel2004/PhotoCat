# PhotoCat Ruflo Implementation Guide

This document is the execution guide for adding photography genre classification to PhotoCat with Ruflo-only orchestration.

## Goal

Extend PhotoCat so it can analyze a user-specified directory of Lightroom-exported JPG images and classify each image into:

- Street Photography
- Concert Photography
- Nature Photography
- Portraits Photography
- Product Photography

## Constraints

- Free to use
- Runs on local hardware only
- Must use the existing Claude Flow V3 / agent workflow
- Must not rely on direct single-agent "just start coding" behavior
- Inside Claude Code, orchestration must use Claude Flow MCP tools, not `npx @claude-flow/cli` task/agent commands

## Why YOLO Alone Is Not Enough

YOLO-style detectors are good at finding objects. Your new labels are not object labels; they are scene and photographic-intent labels.

Examples:

- Street vs Portrait can both contain people
- Concert vs Street can both contain crowds
- Product vs Portrait can both contain a single centered subject
- Nature scenes may contain no canonical object class at all

For this task, the best primary classifier is a vision-language model that understands whole-image semantics. Detection and captioning should be supporting signals.

## Model Analysis

### Best primary choice: SigLIP 2

Recommended starting model:

- `google/siglip2-base-patch16-224` for broad compatibility

Why:

- Designed for zero-shot image classification
- Open local inference through Hugging Face Transformers
- Apache-2.0 license
- Strong fit for prompt-based class matching and embedding extraction

Use it in one of two modes:

1. Zero-shot prompt ensemble
2. Embedding extractor + lightweight classifier trained on your own labeled examples

This is the best first implementation because it is lighter and more controllable than using a full instruction VLM for every image.

Source:

- https://huggingface.co/google/siglip2-base-patch16-224

### Best secondary explainer: Florence-2

Recommended model:

- `microsoft/Florence-2-base-ft`

Why:

- Strong general vision understanding
- Useful for captioning and region-aware descriptions
- Good as a second-pass explainer for borderline cases
- MIT license

Do not use this as the only classifier at first. Use it to explain or re-rank ambiguous SigLIP2 results.

Source:

- https://huggingface.co/microsoft/Florence-2-base-ft

### Best object-cue model: YOLO11 or YOLO-World

Why:

- Good for supportive evidence
- Useful for detecting stage, microphone, speakers, instruments, person density, packaged objects, bottles, screens, trees, cars
- Helpful for rule boosts such as concert or product confidence

Use detector outputs as features, not as the final class.

Sources:

- https://docs.ultralytics.com/models/yolo11/
- https://docs.ultralytics.com/models/yolo-world/
- https://docs.ultralytics.com/tasks/classify/

### Optional heavy tie-breaker: Qwen2.5-VL-3B or InternVL3-2B

Use these only if:

- confidence is low
- you are doing offline evaluation
- you want richer reasoning for hard edge cases

Do not make them the default batch classifier unless your machine handles them comfortably.

Sources:

- https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct
- https://huggingface.co/OpenGVLab/InternVL3-2B

## Recommended Production Strategy

Use a 3-layer classification stack.

### Layer 1: Primary genre score

Run SigLIP2 against prompt ensembles for each target class.

Example prompt families:

- Street Photography
  - "a street photograph in an urban environment"
  - "candid street photography with people in a city"
  - "documentary street photo taken outdoors in town"
- Concert Photography
  - "a concert photograph with stage lighting"
  - "live music performance photography"
  - "concert scene with musician, stage, or audience"
- Nature Photography
  - "a nature photograph of landscape, plants, or wildlife"
  - "outdoor nature photography"
  - "landscape or natural scene photography"
- Portraits Photography
  - "a portrait photograph focused on a person"
  - "portrait photography with subject emphasis"
  - "close-up or posed portrait photo"
- Product Photography
  - "a product photograph with isolated commercial presentation"
  - "product photography showing an object as the main subject"
  - "studio-style product shot"

Average text embeddings per class, compare to image embedding, and keep:

- top class
- top-2 classes
- confidence margin

### Layer 2: Evidence fusion

Add supportive signals:

- YOLO11 or YOLO-World detections
- Florence-2 caption / short description
- existing OCR
- existing technical features

Examples of useful boosts:

- microphone + stage light + crowd -> boost Concert
- tree + mountain + sky + no dominant person -> boost Nature
- centered object + clean background + brand text -> boost Product
- single face/person + shallow depth cues + centered framing -> boost Portrait
- city street + car + sidewalk + candid people mix -> boost Street

### Layer 3: Confidence policy

Before writing metadata, define thresholds:

- high confidence: write genre automatically
- medium confidence: write genre plus review tag
- low confidence: keep top-2 predictions and skip automatic genre write

This avoids poisoning Lightroom metadata with weak labels.

## Best Implementation Path

### Phase 0: Research and acceptance criteria

Ruflo agents:

- `researcher`
- `planner`
- `system-architect`

Deliverables:

- chosen primary model
- chosen fallback model
- prompt set for each class
- evaluation metric targets
- hardware profile assumptions

### Phase 1: Implement the core modules first

Build the first working version before introducing hard acceptance gates.

Required modules:

- `src/scene_classifier.py`
- `src/genre_decision.py`
- `src/cli.py`

The first implementation should be usable immediately against the existing labeled portfolio folders.

### Phase 2: Add a real directory-based input path

The current code hard-codes `images/` in [src/main.py](/C:/Users/javar/GITHUB/PhotoCat/src/main.py). Change that in implementation, but only after the architecture phase.

Required CLI behavior:

- `--input-dir <path>`
- `--recursive`
- `--extensions .jpg,.jpeg`
- optional `--write-xmp`
- optional `--genre-only`
- optional `--min-confidence <float>`

### Phase 3: Add a scene classifier module

Create a dedicated module such as `src/scene_classifier.py`.

Responsibilities:

- load the primary SigLIP2 model once
- expose `classify_scene(image)` or similar
- return:
  - `genre_label`
  - `confidence`
  - `top_k`
  - `supporting_evidence`

Do not bury this logic inside `main.py`.

### Phase 4: Add evidence fusion

Use a second module such as:

- `src/genre_decision.py`

Responsibilities:

- combine SigLIP2 score
- combine detector evidence
- combine caption evidence
- combine OCR evidence
- output final label and review status

This keeps the system testable and lets you evolve scoring without rewriting the whole pipeline.

### Phase 5: Run iterative evaluation against the existing labeled dataset

Use the existing labeled portfolio as the first evaluation set.

Available folders:

- `C:\Users\javar\GITHUB\Photo-Portfolio\public\photos\nature`
- `C:\Users\javar\GITHUB\Photo-Portfolio\public\photos\portraits`
- `C:\Users\javar\GITHUB\Photo-Portfolio\public\photos\product`
- `C:\Users\javar\GITHUB\Photo-Portfolio\public\photos\concert`
- `C:\Users\javar\GITHUB\Photo-Portfolio\public\photos\city`

Folder-to-label mapping:

- `nature` -> `Nature Photography`
- `portraits` -> `Portraits Photography`
- `product` -> `Product Photography`
- `concert` -> `Concert Photography`
- `city` -> `Street Photography`

Notes:

- These folders contain `webp` images, not Lightroom JPG exports.
- They are still valid for iterative classifier tuning and error analysis.
- Do not block implementation waiting for a new labeled dataset.

Required evaluation behavior:

- run the classifier over these folders automatically
- infer the true label from the folder name
- compute per-class precision, recall, and F1
- log all misclassifications to `output/genre_review.csv`

Required `output/genre_review.csv` columns:

- `filename`
- `true_label`
- `predicted_label`
- `confidence`
- `top2_alternative`

The user then reviews the log and decides whether to:

- adjust the prompt ensemble
- adjust confidence thresholds
- accept the current accuracy and proceed

This is the default execution mode: iterative trial-and-error with review, not a hard blocked gate.

### Phase 6: Fix existing bottlenecks before scale-up

Current bottlenecks in the repo:

1. YOLO is loaded inside `detect_objects()` for every image.
2. `main.py` mixes orchestration, scoring, OCR, captioning, and metadata logic.
3. NLTK downloads run at startup.
4. Input path is fixed to `images/`.

Ruflo implementation should address these as part of the feature branch because they will hurt JPG batch throughput.

### Phase 7: Production rollout on Lightroom JPG exports

Once the user approves the iterative evaluation results, run on new Lightroom JPG exports through `--input-dir`.

Recommended XMP write policy:

- `>= 0.80`: auto-write genre metadata
- `0.55 - 0.79`: write genre plus review flag
- `< 0.55`: skip genre write

### Phase 8: Metadata strategy

Use one of these approaches:

1. Conservative:
   - write the genre as a tag only
   - write confidence as a custom field or review note
2. Stronger:
   - write the genre as both tag and title keyword
   - keep raw confidence in a custom namespace

For rollout, start with the conservative strategy.

## Ruflo-Only Operating Procedure

This is the recommended execution sequence for this repo.

### Core rule: orchestration uses MCP tools inside Claude Code

Inside Claude Code:

- use Claude Flow MCP tools for `swarm_init`, `agent_spawn`, and memory operations
- do not use Bash `npx @claude-flow/cli@latest ...` for orchestration
- do not use CLI task/agent orchestration commands from Claude Code

CLI is setup-only and allowed only for:

- `init`
- `doctor`
- `daemon start`

MCP tools coordinate. Claude Code performs file reads, edits, tests, and local command execution.

### 1. Setup-only CLI commands if needed

These are allowed only when Claude Flow setup or health needs manual initialization outside MCP:

```bash
npx @claude-flow/cli@latest doctor --fix
npx @claude-flow/cli@latest init --wizard
npx @claude-flow/cli@latest daemon start
```

Do not use CLI `swarm init`, `agent spawn`, or memory orchestration commands from Claude Code.

### 2. Start the swarm and store memory in one BatchTool message

Inside Claude Code, the first orchestration step must bundle swarm and memory setup into a single BatchTool message.

Required rule:

- all `swarm_init`
- all `agent_spawn`
- all `memory_usage`

must happen in a single BatchTool message.

Correct pattern:

```text
BatchTool:
  mcp__claude-flow__swarm_init { topology: "hierarchical", maxAgents: 6, strategy: "specialized" }
  mcp__claude-flow__agent_spawn { type: "researcher", name: "genre-research" }
  mcp__claude-flow__agent_spawn { type: "planner", name: "genre-planner" }
  mcp__claude-flow__agent_spawn { type: "system-architect", name: "genre-architect" }
  mcp__claude-flow__memory_usage { action: "store", key: "photocat/genre-feature/goal", value: "Classify local Lightroom JPG exports into street, concert, nature, portraits, product." }
  mcp__claude-flow__memory_usage { action: "store", key: "photocat/genre-feature/constraint", value: "Free and local-only. No paid APIs." }
  mcp__claude-flow__memory_usage { action: "store", key: "photocat/genre-feature/current-stack", value: "main.py + YOLOv8 + BLIP + OCR + XMP writer" }
```

Claude Code should then continue with file operations and implementation work after the MCP orchestration step is complete.

### 3. Spawn implementation and validation agents the same way

When moving from research/architecture into implementation, use another single BatchTool message for the next agent set.

Recommended implementation-phase agent set:

- `coder`
- `tester`
- `reviewer`

Keep the same rule: use MCP tools, not Bash CLI orchestration.

### 4. Use swarm tasks, not direct implementation

Recommended tasks:

```text
Research task:
Select the best free local model stack for PhotoCat genre classification and define a confidence-aware evaluation plan.

Architecture task:
Design the PhotoCat genre-classification pipeline with scene classifier, evidence fusion, CLI directory input, and safe XMP integration.

Implementation task:
Implement scene classification, configurable JPG directory input, and confidence-aware genre writing without regressing the existing pipeline.

Testing task:
Create validation scripts and tests for per-class metrics, confidence thresholds, and metadata-writing safety.
```

### 5. Keep memory updated at every checkpoint

Use MCP memory operations, not CLI memory commands.

Examples:

```text
mcp__claude-flow__memory_usage { action: "store", key: "photocat/decision/primary-model", value: "SigLIP2 for primary genre classification" }
mcp__claude-flow__memory_usage { action: "store", key: "photocat/decision/fallback-model", value: "Florence-2 for ambiguous-case explanation and reranking" }
mcp__claude-flow__memory_usage { action: "store", key: "photocat/decision/write-policy", value: ">=0.80 auto-write, 0.55-0.79 write+review-flag, <0.55 skip" }
```

### 6. Monitor and review

Use Claude Flow MCP monitoring/status tools if exposed in the active session. Avoid falling back to Bash CLI orchestration for normal agent control.

## Recommended Final Architecture

Target module layout:

```text
src/
  main.py
  image_analysis.py
  object_detection.py
  image_captioning.py
  scene_classifier.py
  genre_decision.py
  metadata_writer.py
  utilities.py
  cli.py
```

Responsibilities:

- `cli.py`: parse directory path and execution options
- `scene_classifier.py`: primary VLM classification
- `genre_decision.py`: evidence fusion and thresholds
- `object_detection.py`: reusable detector loaded once
- `image_captioning.py`: optional second-pass captioning
- `metadata_writer.py`: XMP writes only after final decision

## Hardware Guidance

Use these defaults:

- If GPU is available: run SigLIP2 and Florence-2 on GPU, keep detector batched
- If CPU only: start with SigLIP2 zero-shot only, then enable detector or captioner selectively
- For large directories: process in batches and cache results

Avoid loading large VLMs per image.

## Practical Recommendation

If you want the shortest path to a good result, do this:

1. Start with SigLIP2 zero-shot prompt ensemble.
2. Add confidence margins and top-2 output.
3. Add YOLO11 or YOLO-World rule boosts.
4. Add Florence-2 only for ambiguous cases.
5. Build a labeled dataset from your own JPG exports.
6. Train a lightweight classifier on top of SigLIP2 embeddings if zero-shot is not stable enough.

That path is cheaper, faster, and easier to debug than jumping directly to a heavy VLM-only classifier.

## Sources

- SigLIP 2 model card: https://huggingface.co/google/siglip2-base-patch16-224
- Florence-2 model card: https://huggingface.co/microsoft/Florence-2-base-ft
- Qwen2.5-VL-3B-Instruct model card: https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct
- InternVL3-2B model card: https://huggingface.co/OpenGVLab/InternVL3-2B
- Ultralytics YOLO11 docs: https://docs.ultralytics.com/models/yolo11/
- Ultralytics YOLO-World docs: https://docs.ultralytics.com/models/yolo-world/
- Ultralytics classification docs: https://docs.ultralytics.com/tasks/classify/
