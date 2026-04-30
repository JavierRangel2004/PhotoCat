# ARM / CPU Performance Analysis

Date: 2026-03-17

Source run evaluated:
- Log: [output/armrun17_03_1833/armrun17_03_1833.txt](/Users/javierrangel/github/PhotoCat/output/armrun17_03_1833/armrun17_03_1833.txt)

## Summary

The evaluated run completed successfully on Apple Silicon and averaged:

- `154 images in 1607.3s`
- `10.44s/image avg`

This is substantially slower than a Windows machine with a dedicated CUDA GPU, but the gap is not surprising given the current model stack and execution strategy.

The important distinction is this:

- Some slowdown is expected on Apple Silicon MPS vs NVIDIA CUDA.
- A meaningful part of the slowdown is repo-level and should be improvable for both Apple Silicon and CPU-only devices.

## Evidence From The Evaluated Run

The saved run shows:

- Full pipeline execution, not genre-only.
- Per-image wall times commonly in the `8s` to `16s` range.
- YOLO object detection itself is usually only a fraction of the total per-image time.
- Batch result: `10.44s/image avg`.

Relevant evidence from the log:

- Batch total at [output/armrun17_03_1833/armrun17_03_1833.txt](/Users/javierrangel/github/PhotoCat/output/armrun17_03_1833/armrun17_03_1833.txt)
  `Batch complete: 154 images in 1607.3s (10.44s/image avg)`
- Typical YOLO timings at [output/armrun17_03_1833/armrun17_03_1833.txt](/Users/javierrangel/github/PhotoCat/output/armrun17_03_1833/armrun17_03_1833.txt)
  examples range roughly from `~30ms` to `~530ms` inference, with some heavier postprocess cases.
- Typical full-image completion times at [output/armrun17_03_1833/armrun17_03_1833.txt](/Users/javierrangel/github/PhotoCat/output/armrun17_03_1833/armrun17_03_1833.txt)
  many examples land around `~8s` to `~16s`.

Inference:

- YOLO is not the dominant bottleneck in this run.
- Captioning and full multi-stage processing are likely dominating total image latency.

## Current Pipeline Behavior Relevant To Performance

The full pipeline in [src/main.py](/Users/javierrangel/github/PhotoCat/src/main.py#L261) does all of the following on cache miss:

- image load
- preprocessing
- blur/exposure checks
- YOLO object detection
- OCR
- BLIP captioning
- title generation
- SigLIP-based genre classification

The code uses:

- BLIP large in [src/image_captioning.py](/Users/javierrangel/github/PhotoCat/src/image_captioning.py#L8)
- SigLIP2 zero-shot image classification in [src/scene_classifier.py](/Users/javierrangel/github/PhotoCat/src/scene_classifier.py#L64)

Those are both relatively heavy stages for non-CUDA devices.

## Main Findings

### 1. The observed slowdown is real, but not primarily because of ARM CPU

The run is not CPU-only. Device detection supports MPS in [src/device.py](/Users/javierrangel/github/PhotoCat/src/device.py#L36), and the earlier live logs showed MPS was selected. That means Apple Silicon acceleration is being used, but MPS still trails a dedicated CUDA GPU by a lot for this workload.

Conclusion:

- The Windows-to-Mac slowdown is partly expected.
- It should not be framed as "ARM CPU only" performance, because this run is actually using MPS.

### 2. Full pipeline latency is dominated by stages beyond YOLO

In the evaluated output, YOLO is usually sub-second, while the image-level completion is usually many seconds. That means the expensive stages are more likely:

- BLIP caption generation
- OCR
- SigLIP zero-shot classification
- cumulative model/device overhead around those stages

Conclusion:

- Reducing YOLO alone will not materially fix the end-to-end runtime.

### 3. The current code clears accelerator cache after every image

The helper in [src/main.py](/Users/javierrangel/github/PhotoCat/src/main.py#L198) calls:

- `gc.collect()`
- `torch.cuda.empty_cache()`
- `torch.mps.empty_cache()`

This helper is invoked after each image in:

- genre-only path at [src/main.py](/Users/javierrangel/github/PhotoCat/src/main.py#L280)
- full pipeline path at [src/main.py](/Users/javierrangel/github/PhotoCat/src/main.py#L336)

This is a strong candidate for avoidable slowdown on Apple Silicon and also potentially on CPU-only systems, because repeated cache flushing and collection can increase memory churn and reduce steady-state throughput.

Conclusion:

- This is a repo-level optimization opportunity.

### 4. The pipeline is optimized for correctness first, not device-specific throughput

Examples:

- `workers` defaults to `1` in [src/cli.py](/Users/javierrangel/github/PhotoCat/src/cli.py#L72)
- multi-worker mode disables cache in [src/main.py](/Users/javierrangel/github/PhotoCat/src/main.py#L527)
- the same heavy model stack is used regardless of CUDA, MPS, or CPU

Conclusion:

- The code currently lacks a device-aware performance mode.

### 5. CPU-only performance will likely be significantly worse than this Apple Silicon run

Because the current measured run is on MPS and still averages `10.44s/image`, a true CPU-only machine is likely to be noticeably slower unless the pipeline changes behavior.

Conclusion:

- CPU-only support should not simply reuse the same default stack and expectations.

## Why Windows CUDA Feels Much Better

The current stack benefits strongly from CUDA:

- BLIP and SigLIP inference are more mature and generally faster on NVIDIA CUDA.
- Dedicated GPU VRAM and memory bandwidth help sustained batch workloads.
- Apple MPS works, but it is usually less predictable and slower for mixed-model inference pipelines.

Conclusion:

- The Windows result is not an anomaly.
- The Apple result is plausible.
- There is still room to improve the Apple and CPU-only path materially.

## Recommended Optimization Plan

No code changes are included here. This is the recommended plan of attack.

### Priority 1: Add Per-Stage Timing

Add explicit timings for:

- image load
- preprocess
- blur/exposure
- YOLO
- OCR
- BLIP
- SigLIP
- CSV write / XMP write
- cache read / cache write

Why:

- The current logs expose YOLO timing well, but not the heavy text/captioning stages.
- Without per-stage timing, performance work will stay guess-based.

Expected payoff:

- High diagnostic value
- Low implementation risk

### Priority 2: Stop Clearing Model Cache After Every Image

Evaluate removing or reducing per-image calls to:

- `gc.collect()`
- `torch.cuda.empty_cache()`
- `torch.mps.empty_cache()`

Better options to test:

- clear only every `N` images
- clear only on memory pressure / failure
- clear only at batch end

Why:

- Per-image cache clearing is likely harming steady-state inference throughput.

Expected payoff:

- Medium to high on MPS
- Medium on CPU-only

### Priority 3: Add a Device-Aware Performance Preset

Recommended runtime modes:

- `quality`
  current behavior
- `balanced`
  lighter captioning, retain genre classification
- `fast`
  minimize heavy stages on MPS and CPU-only

For `balanced` and `fast`, consider:

- smaller caption model
- optional OCR skip unless scene/object evidence suggests text matters
- optional skip of captioning when genre confidence is already decisive
- optional lower image resolution for some stages

Why:

- CUDA and non-CUDA should not pay the same default cost.

Expected payoff:

- High on MPS
- Very high on CPU-only

### Priority 4: Make Captioning Optional Or Conditional

BLIP large is likely one of the main throughput costs in [src/image_captioning.py](/Users/javierrangel/github/PhotoCat/src/image_captioning.py#L8).

Possible strategies:

- replace BLIP large with a smaller caption model for non-CUDA devices
- only run captioning when title output is required
- skip captioning when object detection plus genre confidence are already strong

Why:

- The current pipeline pays captioning cost on every full run.

Expected payoff:

- Very high for Apple Silicon
- Very high for CPU-only

### Priority 5: Add A True Fast Review Pass

The existing `--genre-only` path in [src/main.py](/Users/javierrangel/github/PhotoCat/src/main.py#L271) already skips major work. A review workflow can build on that:

- first pass: genre-only audit
- second pass: run full pipeline only for images needing deeper metadata

Why:

- Many review workflows do not need titles and full metadata for every image immediately.

Expected payoff:

- Very high for large libraries

### Priority 6: Revisit Worker Strategy Separately For CPU-Only

The current guidance is conservative and centers on GPU safety. CPU-only hardware may benefit from a different strategy:

- smaller models
- controlled multiprocessing
- stage-level parallelism rather than full-process duplication

Why:

- CPU-only and GPU-backed runs should not share the same tuning assumptions.

Expected payoff:

- Medium to high on CPU-only

## Suggested Validation Matrix

When performance work begins, validate at least these configurations:

1. Windows + CUDA + current mode
2. macOS Apple Silicon + MPS + current mode
3. macOS Apple Silicon + MPS + balanced mode
4. CPU-only machine + current mode
5. CPU-only machine + fast mode

Track:

- total batch time
- average seconds per image
- p50 / p95 per-image time
- memory usage stability
- quality deltas in genre/title outputs

## Practical Expectations

Realistic expectations:

- Apple Silicon MPS will still remain slower than Windows CUDA.
- Repo-level changes should still reduce the current Apple path meaningfully.
- CPU-only should get a dedicated "fast enough to use" mode rather than trying to mirror CUDA-quality defaults.

## Recommended First Changes

If work starts on this area, the first changes should be:

1. Add per-stage timings.
2. Remove or relax per-image accelerator cache clearing.
3. Introduce a non-CUDA performance preset.
4. Make captioning conditional or lighter for MPS and CPU-only.

That order gives the best chance of measurable speed gains with low ambiguity.
