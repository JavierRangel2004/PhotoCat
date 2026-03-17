# Photography Category Strategy — Final Decision Guide
**Javier Rangel / JRMGraphy · Prepared 2026-03-16**

---

## 1. Your Catalog by the Numbers

Derived from `output/full_audit_corrected.csv` — 274 images, manually audited.

| Category | Images | % of catalog | Avg rating | 3+ star quality | Model confidence |
|---|---|---|---|---|---|
| Street Photography | 95 | **34.7%** | 2.51 | 47% | 83.8% |
| Portrait Photography | 59 | **21.5%** | **2.54** | **53%** | 80.5% |
| Product Photography | 56 | **20.4%** | 2.14 | 36% | 86.9% |
| Nature Photography | 34 | 12.4% | 2.24 | 32% | **91.8%** |
| Music Photography | 23 | 8.4% | 2.13 | 39% | 83.8% |
| Architecture Photography | 4 | 1.5% | 2.00 | 25% | 46.0% |

**Key ratings fact**: Only 17.2% of your total catalog is 4-star. No 5-star images. There is significant room to grow both quality and volume in every category.

---

## 2. The "Street Photography" Problem (Critical Finding)

Your single biggest category (34.7%) is hiding multiple sub-genres.

During the Gemini manual review of these 274 images, **43 images labeled as Street Photography were consistently recommended as Architecture Photography** — things like:
- Clock tower facades
- Plaza cityscapes (Plaça d'Espanya, Barcelona skyline, Granada rooftops)
- Monuments and statues
- Architectural details

The PhotoCat model labeled these as Street because it saw urban outdoor environments but had no Architecture category to fall back on. This means:

| What's actually inside "Street Photography" | Est. count |
|---|---|
| True candid street documentary (people, moments) | ~45–55 images |
| Travel / cityscape / architectural shots | ~30–43 images |
| Ambiguous/overlapping (markets, public life) | ~5–10 images |

**Implication**: Your genuine street documentary work is probably closer to **16–20% of your catalog**, not 35%.

---

## 3. What ChatGPT Diagnosed vs. What the Data Confirms

ChatGPT's recommendation (from `gptNicheRecommendations.md`):
> "Retrato documental / lifestyle / branding humano" as primary, with events/music as secondary, and nature as personal.

The catalog data validates this:

| ChatGPT suggested | What the numbers say |
|---|---|
| Portrait/Branding as primary commercial line | Highest quality (53% 3+ stars), 21.5% of catalog — **confirmed** |
| Events/Music as secondary | Clear 8.4% block, reliable confidence — **confirmed** |
| Nature as personal/autoral line | Highest model confidence (91.8%), but lowest commercial ratings — **confirmed** |
| Product as "lower priority unless you want it" | 20.4% of catalog but avg rating 2.14 — **confirmed lower quality** |
| Street is not a clean commercial sell | Category is contaminated with architectural/travel shots — **confirmed** |

---

## 4. The Three-Category Commercial Framework

Based on all evidence, here is the recommended structure for jrmgraphy.com.

### Tier 1 — Primary Commercial Offering
**"Retrato Documental & Personal Branding"**

- **Feeds from**: Portrait Photography (59 imgs, best quality) + food/market documentary shots within Product
- **Client types**: Chefs, baristas, artisans, small-business owners, creatives, entrepreneurs
- **Why this wins**:
  - Best quality score in your catalog (53% 3+ stars)
  - Most direct path to paying clients in CDMX
  - Aligns with what you described enjoying most: "chefs cocinando, personas haciendo cosas"
  - Personal branding photography is growing fast in the creator/SMB market
- **Monetization**: Per-session rates (₱3,000–8,000 per session is realistic for CDMX market), brand packages, editorial licensing

### Tier 2 — Secondary Commercial Offering
**"Eventos & Música / Cobertura Cultural"**

- **Feeds from**: Music Photography (23 imgs, 83.8% confidence) + curated candid street event shots
- **Client types**: Concert venues, music labels, cultural organizers, festival producers, pop-up brands
- **Why this works**:
  - You have a natural 8.4% block of work already; this is a proven capability
  - Clear deliverable: photographers are hired per event, not per "style"
  - Complements Tier 1 (clients who need branding often also run events)
  - $4,396/weekend rates exist for concert photographers (per Gemini's cited video)
- **Monetization**: Per-event coverage fees, editorial licensing, press credentials that build visibility

### Tier 3 — Personal Autoral Line
**"Naturaleza & Paisaje" (prints, stock, brand identity)**

- **Feeds from**: Nature Photography (34 imgs, 91.8% confidence) + the architectural/travel subset extracted from Street
- **Why to keep it alive**:
  - Highest model confidence = most visually coherent body of work
  - Serves as your aesthetic signature (the "why Javier" behind the brand)
  - Monetizes differently: print sales, stock licensing (Getty, 500px, Adobe Stock), editorial pitches to travel/nature publications
  - Does NOT need to be your client funnel — it's your long-term IP

---

## 5. What to Do With "Product Photography" (20.4%)

This category has the second-lowest quality score (avg 2.14, 36% 3+ stars). It contains two very different things:

| Sub-type | Recommendation |
|---|---|
| Documentary food/market shots (vendors, stalls, Lady Dumpling, spiral potatoes) | Move to **Tier 1** as "gastronomía documental" — this is your strongest cross-sell to chef clients |
| Isolated product still-lifes (Estrella Damm bottles, arranged objects) | Keep for **commercial product clients** if you want that work, but don't lead with it on the homepage |

ChatGPT explicitly said: "Si no quieres posicionarte como fotógrafo de producto, yo no le daría ese mismo peso."

---

## 6. Self-Assessment Questions (Answer These Before Finalizing)

These are not rhetorical — your answers will determine whether Tier 1 or Tier 2 should be your primary focus.

### About energy and sustainability
1. If you had to do 20 portrait/branding sessions in the next 6 months, would you be excited or would that feel draining?
2. When you photographed the chefs, was the energy before, during, or after the session the highest? (Before = passion-driven; after = relief-driven)
3. What made you describe weddings as "pesada" — was it the clients, the length of the day, the editing volume, or the emotional pressure?

### About market fit
4. Do you have 5–10 people in your immediate network (friends, contacts, social media) who run small businesses, have personal brands, or organize events — people who would realistically hire you or refer you within 90 days?
5. Have you ever been paid for photography? If yes, which category produced that income?
6. Is your current job in a creative or business environment where potential clients (marketing managers, brand owners, event organizers) already know you?

### About your work quality
7. Looking at your 59 portrait images: are at least 10–12 of them strong enough to publish as a portfolio today, or would you need new sessions first?
8. Looking at your 23 music/concert images: do they represent venues and artists that match the kind of clients you want to attract?
9. Is your Nature body of work (34 images) coherent enough to function as a prints store, or is it scattered across different environments and styles?

### About commitment
10. Are you willing to do 2–3 free or low-cost sessions specifically to build each commercial category's portfolio before charging full rates?
11. Can you consistently post 2–3 times per week on Instagram in one of the two commercial lanes for the next 6 months?
12. Are you willing to reach out directly (DMs, emails, in-person) to at least 5 potential clients per month in your target niches?

---

## 7. The Missing Category You Should Add to PhotoCat

The audit revealed a systematic classification gap. Your current 5 categories (Street, Concert, Nature, Portraits, Product) need one more:

**Add: `Travel / Architecture / Cityscape`**

Approximately 40–50 images currently mislabeled as Street Photography are actually travel/architectural shots from Barcelona, Granada, and other locations. Creating this category would:
1. Clean up Street Photography into a coherent candid/documentary body of work
2. Give your travel shots a proper home (useful for editorial/stock)
3. Reduce the Street category from 34.7% to ~18–20%, making it less dominant and more accurate

This is a data quality fix, not a commercial strategy — but it affects how you curate your portfolio.

---

## 8. Recommended Action Sequence (6-Week Sprint)

### Week 1–2: Clean the data
- Run the PhotoCat audit again with an added `Travel/Architecture/Cityscape` category
- Move ~40 misclassified Street photos to the correct bucket
- Cull your Product category: tag each image as "documentary food" or "product still-life"

### Week 3: Answer the 12 self-assessment questions
- Write down your answers (5–10 min each)
- Whichever lane feels energizing across questions 1–6 becomes your Tier 1

### Week 4–5: Build the portfolio for your chosen Tier 1
- Identify 3 people in your network you can shoot (chef, artist, entrepreneur)
- Do the sessions, edit a set of 10–15 strong images per session
- Use those as your first real Tier 1 portfolio block

### Week 6: Launch the repositioned web presence
- Apply ChatGPT's web restructuring recommendations (fix 404s first)
- Homepage: clear value proposition for Tier 1 + Tier 2
- Portfolio: 3 sections only (Branding/Retrato, Eventos/Música, Naturaleza)
- Remove "amateur" from bio
- Maximum 12–15 images per section

---

## 9. Monetization Paths by Category (Realistic for CDMX, 2026)

| Category | Monetization method | Realistic early rates | Timeline to first client |
|---|---|---|---|
| Retrato / Personal Branding | Per-session fees | ₱3,500–7,000 | 1–4 weeks (network referrals) |
| Eventos & Música | Per-event coverage | ₱2,500–5,000/event | 2–6 weeks (outreach to small venues) |
| Gastronomía documental | Package with branding | Add-on to portrait packages | 2–8 weeks |
| Naturaleza — Stock | Licensing (Getty/Adobe) | $0.25–$2/download | 3–12 months to meaningful income |
| Naturaleza — Prints | Direct print sales via web | ₱500–2,500/print | After building audience (Instagram) |
| Product still-life | Per-product or day rate | ₱1,500–4,000 | 2–6 weeks (if you pursue it) |

**Reality check from ChatGPT**: Nature photography is not a "client contacts me tomorrow" category. It is a long game: build Instagram audience, then offer prints, then pitch editorial. Keep it alive but don't count on it for revenue in 2026.

---

## 10. Final Recommendation (TL;DR)

Based on your catalog data (274 images), ChatGPT's analysis, and Gemini's per-image audit:

**Your best commercial category is Retrato Documental / Personal Branding.**
- It has the highest quality in your existing catalog (53% 3+ stars)
- It aligns with what you described enjoying: "personas en contexto, cocinando, trabajando, viviendo su oficio"
- It is the easiest path to a paying client in CDMX within 30–60 days
- It is broad enough to include chefs, musicians, entrepreneurs, and creatives without feeling scattered

**Your best complementary category is Eventos & Música.**
- It is already a distinct, coherent body of work (23 images at 83.8% confidence)
- It complements Tier 1 naturally (the same clients who do personal branding often run events)
- It gives you a second revenue stream with different deliverable timelines

**Your Nature/Paisaje work is your brand identity, not your sales funnel.**
- Keep it. Curate it aggressively. Post it on Instagram as your aesthetic signature.
- Build toward print sales and stock licensing, but do not count on it for primary income in the next 12 months.

**Your web positioning should say:**

> "Fotografía documental y retrato para personas, marcas y proyectos en acción — CDMX."

That sentence covers all three tiers, sounds professional, and does not overpromise.

---

*Document generated from: `gptNicheRecommendations.md`, `output/full_audit_corrected.csv` (274 images), and Gemini's per-image manual review transcript (`output/full_audit_corrected.txt`).*
