# PhotoCat Taxonomy Strategy

## Overview

PhotoCat classifies images into a primary set of **Commercial Taxonomy** categories. This taxonomy was intentionally designed to align with how photography services are sold and organized in portfolios, moving away from purely descriptive or academic labels.

## The 6-Category Primary Taxonomy

The core taxonomy processed by the ML engine (SigLIP2 zero-shot + evidence fusion) consists of:

1. **Street Photography**
   - **Definition:** Candid, documentary-style photography in public or urban spaces.
   - **Characteristics:** People in natural settings, cityscapes, spontaneous moments.
2. **Portrait Photography**
   - **Definition:** Focused on a person or group of people, emphasizing expression and mood.
   - **Characteristics:** Close-ups, posed subjects, shallow depth of field, cosplay, standard headshots.
3. **Product Photography**
   - **Definition:** Isolated or styled shots of objects intended for commercial or showcase purposes.
   - **Characteristics:** Clean backgrounds, macro shots, food/beverage, jewelry.
4. **Nature Photography**
   - **Definition:** Landscapes, wildlife, and natural environments.
   - **Characteristics:** Trees, mountains, animals, outdoor scenes without dominant human structures.
5. **Music Photography**
   - **Definition:** Live music events, concerts, or studio shots of musicians.
   - **Characteristics:** Stage lighting, microphones, instruments, crowds.
6. **Architecture & Spaces (Recently Added)**
   - **Definition:** Buildings, interiors, and structural environments.
   - **Characteristics:** City buildings without dominant street life, real estate interiors, geometric structures.

## Fallback & Specialty Categories

When the model detects specific keywords in the file title/tags or is uncertain, it can route to these secondary categories:
- **Wedding Photography**: Triggers on keywords like "bride", "groom", "wedding". Often overlaps visually with Portrait or Event.
- **Event Photography**: Festivals, parades, corporate events.
- **Sports Photography**: Athletic events.
- **Other Photography**: Catch-all for ambiguous images or extreme edge cases (e.g., abstract textures).

## Decision Logic & Rules

The categorization isn't just a raw ML output. It uses a fusion system (`genre_decision.py`):
1. **Primary Score:** SigLIP2 gives base confidences for the primary genres.
2. **Contradiction Rules:** E.g., If the scene is pure nature but SigLIP thinks it's "Product" (common with isolated subjects like the moon or a shark on black), explicit rules override it.
3. **Boosts:** Detections from YOLO (like a `microphone`) boost the Concert/Music score.
4. **Confidence Gates:**
   - `High (>0.80)`: Automatically written.
   - `Medium (0.50 - 0.80)`: Tagged for manual review.
   - `Low (<0.50)`: Stays unassigned or falls back to title-inferred.

## Continuous Tuning

The taxonomy requires continuous tuning to avoid "Category Pollution". For example, before adding *Architecture*, building photos polluted the *Street Photography* bucket. When reviewing edge cases, developers should adjust `genre_decision.py` rather than retraining the base model.
