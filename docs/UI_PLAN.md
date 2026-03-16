# PhotoCat UI Plan

A desktop GUI that wraps the existing pipeline, making it easy to run, review, and correct classification results before committing any file moves.

---

## Goals

1. Select input directory and configure run flags visually.
2. Trigger pipeline runs and watch live progress.
3. Browse the audit CSV output — filtered, sorted, grouped by genre.
4. Inspect each image with its full metrics (path, rating, blur, exposure, YOLO objects, BLIP caption, OCR, SigLIP scores, evidence log).
5. Override the assigned genre per-image, then export a corrected CSV or commit `--organize`.
6. Feed corrections back into a labeled dataset for future classifier improvement.

---

## Technology Choice

**Gradio** (Python, local server, browser UI)

| Option | Why Gradio wins |
|---|---|
| Gradio | Zero JS, pure Python, ships as `pip install gradio`, file browser component, image viewer, dataframe editor, runs locally on `localhost:7860` |
| Tkinter | No image grid, painful layout, hard to iterate |
| PyQt6 | Heavyweight, compiled, harder to ship |
| Streamlit | Good but no editable dataframe cells without extra hacks |
| Electron | Requires Node, too large for this scope |

Gradio 4.x has:
- `gr.FileExplorer` — directory picker
- `gr.Image` — image viewer
- `gr.Dataframe` — editable table (user can type corrected genre inline)
- `gr.CheckboxGroup` / `gr.Dropdown` — flag selectors
- `gr.Textbox(lines=10)` — live log streaming via `gr.update`
- `gr.Gallery` — image strip with captions

---

## Screen Layout (3 Tabs)

```
┌─────────────────────────────────────────────────────────────┐
│  PhotoCat                                    [Run] [Restore] │
├──────────┬──────────┬───────────────────────────────────────┤
│  Tab 1   │  Tab 2   │  Tab 3                                │
│  Run     │  Review  │  Image Inspector                      │
└──────────┴──────────┴───────────────────────────────────────┘
```

---

## Tab 1 — Run Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│  Input Directory    [Browse…]  /path/to/photos              │
│  CSV Output         [Browse…]  output/audit.csv             │
│                                                             │
│  ┌── Pipeline Flags ──────────────────────────────────────┐ │
│  │ [ ] --recursive        [ ] --write-xmp                 │ │
│  │ [ ] --genre-only       [ ] --no-cache                  │ │
│  │ [ ] --organize         [ ] --dry-run                   │ │
│  │                                                         │ │
│  │ Min confidence  [0.55 ▼]   Workers [1 ▼]               │ │
│  │ Extensions      [.jpg,.jpeg,.png,.tiff,.webp,.cr2,.dng] │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  [▶ Run Pipeline]          [⏹ Stop]                        │
│                                                             │
│  ┌── Live Log ────────────────────────────────────────────┐ │
│  │ [1/274] Processing test2024-001.jpg                    │ │
│  │   Genre: Nature Photography (conf=0.77, status=review) │ │
│  │ ...                                                     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  Progress: ████████░░░░ 142/274   Cache: 141 hits, 1 miss  │
└─────────────────────────────────────────────────────────────┘
```

### Fields

| Field | Component | Notes |
|---|---|---|
| Input directory | `gr.Textbox` + folder button | Validated on change |
| CSV output path | `gr.Textbox` | Default: `<input_dir>/photocat_audit.csv` |
| Pipeline flags | `gr.CheckboxGroup` | Maps to CLI flags |
| Min confidence | `gr.Slider(0.3, 0.95)` | Maps to `--min-confidence` |
| Workers | `gr.Dropdown([1,2,4])` | Warning shown if > 1 (disables cache) |
| Extensions | `gr.Textbox` | Comma-separated |
| Run/Stop | `gr.Button` | Run calls subprocess, Stop sends SIGTERM |
| Live log | `gr.Textbox(lines=20)` | Streamed via `subprocess.Popen` generator |
| Progress bar | `gr.Progress` / `gr.HTML` | Parsed from log lines `[N/M]` |

---

## Tab 2 — Review Table

```
┌─────────────────────────────────────────────────────────────┐
│  CSV:  output/audit.csv          [Load CSV]  [Load Images]  │
│                                                             │
│  Filter: Genre [All ▼]   Status [All ▼]   Conf < [0.80 ▼]  │
│  Sort by: [Confidence ▼] [↓ Desc]                          │
│                                                             │
│  ┌─ Summary ────────────────────────────────────────────┐  │
│  │ 274 images  |  183 auto  |  79 review  |  12 inferred │  │
│  │ Street 95 · Portrait 59 · Product 56 · Nature 34 ...  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ Image Grid (filtered) ───────────────────────────────┐  │
│  │ [thumb] [thumb] [thumb] [thumb] [thumb] [thumb] ...   │  │
│  │  auto    review  review  auto    review  auto          │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ Read-Only Table ────────────────────────────────────┐  │
│  │ # │ File          │ Status   │ Genre      │ Override │  │
│  │ 1 │ test001.jpg   │ auto     │ Street     │          │  │
│  │ 2 │ test003.jpg   │ review   │ Street     │ Nature   │  │
│  │ 3 │ test040.jpg   │ inferred │ Architect  │          │  │
│  └───────────────────────────────────────────────────────┘  │
│  (click gallery thumbnail or table row → opens Inspector)   │
│                                                             │
│  [✓ Export Corrected CSV]   [Preview Organize]             │
└─────────────────────────────────────────────────────────────┘
```

### Features

| Feature | Detail |
|---|---|
| Load CSV | Reads `full_audit.csv`, populates table and gallery |
| Filter by genre | Dropdown of all genres found in CSV |
| Filter by status | `auto` / `review` / `title-inferred` |
| Filter by confidence | Slider — show only rows below threshold |
| Image grid | `gr.Gallery` of thumbnails (click opens Inspector) |
| Read-only table | `gr.Dataframe(interactive=False)` — shows genre, override, status, confidence |
| Genre editing | **Only in Tab 3 (Inspector)** via `gr.Dropdown` — user sees image + evidence before correcting |
| Mark correct/wrong | In Inspector only — sets `user_label` per image |
| Export corrected CSV | Writes `full_audit_corrected.csv` with `user_genre` and `user_label` columns |
| Organize preview | Shows dry-run summary before any file moves — count per genre, override count |
| Autosave | Corrections auto-saved to temp JSON every 10 changes; restored on next CSV load |

---

## Tab 3 — Image Inspector

```
┌────────────────────────────────────────┬────────────────────┐
│                                        │ File               │
│                                        │ /full/path/to/img  │
│                                        ├────────────────────┤
│         [Image Preview]                │ Rating      ★★★☆☆  │
│         1600×1067 px                   │ Blur        no     │
│                                        │ Exposure    normal │
│                                        ├────────────────────┤
│                                        │ BLIP Caption       │
│                                        │ "A clock tower     │
│                                        │  in the city..."   │
│                                        ├────────────────────┤
│                                        │ YOLO Objects       │
│                                        │ potted plant       │
│                                        ├────────────────────┤
│                                        │ OCR Text           │
│                                        │ (none)             │
│                                        ├────────────────────┤
│                                        │ SigLIP Scores      │
│                                        │ Street     0.518   │
│                                        │ Nature     0.480   │
│                                        │ Portrait   0.002   │
│                                        ├────────────────────┤
│                                        │ Evidence Log       │
│                                        │ nature_boost: 0.12 │
│                                        │ street_boost: 0.12 │
│                                        ├────────────────────┤
│                                        │ Assigned Genre     │
│                                        │ [Street Photog ▼]  │
│                                        │                    │
│                                        │ [✓ Confirm]        │
│                                        │ [✗ Mark Wrong]     │
│ [← Prev]  3 / 12 (review filter)  [→ Next]                 │
└────────────────────────────────────────┴────────────────────┘
```

### Fields shown per image

| Field | Source |
|---|---|
| Full path | `img_path` from CSV |
| Dimensions | Read from file at load time |
| Rating | `rating` column |
| Blur | `is_blurry` column |
| Exposure | `exposure` column |
| BLIP Caption | `caption` column |
| YOLO Objects | `objects_detected` column (semicolon-separated) |
| OCR Text | `ocr_text` column |
| SigLIP scores | Parsed from `model_1st`, `model_1st_conf`, `model_2nd`, `model_2nd_conf` |
| Evidence log | `evidence_log` column (JSON → formatted key: value list) |
| Assigned Genre | Editable `gr.Dropdown` of all 10 taxonomy categories |
| Confirm / Wrong | Sets `user_genre` / `user_label` in the in-memory dataframe |
| Prev / Next | Navigates within current filter set (review-only, genre-filtered, etc.) |

---

## Data Flow

```
pipeline run
    └─→ output/full_audit.csv
            └─→ Tab 2: load into DataFrame (in memory)
                    ├─→ Tab 3: inspector reads single row by index
                    │        └─→ user edits genre → writes back to in-memory DataFrame
                    └─→ Tab 2: Export corrected CSV
                                    └─→ output/full_audit_corrected.csv
                                            └─→ _organize_into_dirs() with corrected genres
```

## State Model

```
UIState
├── Base State (source of truth)
│   └── base_df: full DataFrame from CSV + user_genre + user_label columns
│
└── Derived State (recomputed on filter change)
    ├── filter_genre, filter_status, filter_max_conf
    ├── sort_col, sort_asc
    ├── visible_indices: list[int] — row indices matching current filters
    └── active_idx: int — position within visible_indices (Inspector nav)
```

Corrections are held in two new columns appended to the in-memory DataFrame:

| Column | Type | Values |
|---|---|---|
| `user_genre` | str | One of 10 taxonomy labels, or `""` (no override) |
| `user_label` | str | `"correct"` / `"wrong"` / `""` |

The corrected CSV preserves all original columns and appends these two. This file can later be used to build a labeled training dataset for classifier improvement.

---

## Implementation Phases

### Phase A — Scaffold (no pipeline integration)
- `src/ui.py` entry point: `python src/ui.py`
- 3-tab Gradio layout, all components wired up
- CSV load → DataFrame display
- Image inspector navigation from static CSV
- Corrected CSV export

**Deliverable:** Fully functional review/correction UI from any existing audit CSV.

### Phase B — Pipeline integration
- Tab 1 "Run" streams subprocess output line-by-line via `subprocess.Popen`
- Progress bar parsed from `[N/M]` tokens in log
- On completion: auto-load the generated CSV into Tab 2
- Stop button sends `process.terminate()`

**Deliverable:** Full end-to-end run-and-review loop from the UI.

### Phase C — Organize from UI
- "Organize (corrected)" button in Tab 2
- Applies `user_genre` overrides where set, falls back to `final_genre`
- Shows dry-run preview before actual move
- Calls restore logic if re-organizing after a previous run

**Deliverable:** No CLI needed for the full workflow.

### Phase D — Dataset export (future)
- "Export training data" button
- Copies images labeled `"correct"` to `datasets/genre/train/<genre>/`
- Ready for fine-tuning a lightweight classifier on top of SigLIP2 embeddings

---

## File Structure

```
src/
  ui.py              ← Gradio app entry point
  ui_state.py        ← In-memory DataFrame state, genre correction helpers
  ui_runner.py       ← Subprocess runner, log stream generator
```

No changes to existing pipeline modules. The UI is a pure wrapper.

---

## Dependencies

```
gradio>=4.40.0       # pip install gradio
Pillow               # already required by pipeline
```

No additional GPU or model dependencies. The UI only reads CSV and image files; all heavy inference stays in the existing pipeline.

---

## Launch Command

```bash
python src/ui.py
# → Gradio running on http://127.0.0.1:7860
```

Or with auto-launch:

```bash
python src/ui.py --browser
```

---

## Open Questions / Decisions Needed

| Question | Options | Recommendation |
|---|---|---|
| Image loading performance | Thumbnails on demand vs. preload all | Load on demand; cache last 20 thumbs |
| Genre dropdown per table row | Editable cell vs. separate dropdown | Separate dropdown in Inspector (cleaner) |
| Persist corrections across sessions | Write to CSV on every change vs. export only | Export only (simpler, explicit) |
| Auto-load CSV after run | Yes / No | Yes, on run completion |
| Dark mode | Default Gradio theme / custom | Default OK for now |


EVALUATION
Sí está **bien pensado** y, en general, va en la dirección correcta. Mi evaluación global sería:

**Veredicto: 8/10.**
Como plan de producto y de integración técnica, está **sólido, realista y bastante implementable**. Donde más flojea no es en la idea, sino en **algunos detalles de UX y de viabilidad técnica fina dentro de Gradio**.

## Lo que está muy bien

### 1) El objetivo está bien definido

El plan ataca exactamente el problema correcto: no solo correr el pipeline, sino **crear una capa humana de revisión antes de mover archivos**. Eso reduce errores costosos y además convierte correcciones manuales en datos útiles para mejorar el clasificador después.

### 2) La arquitectura por fases está muy sana

La secuencia A → B → C → D está muy bien planteada porque:

* primero validas la utilidad del reviewer,
* luego conectas el runner,
* después habilitas organización real,
* y al final extraes dataset.

Eso baja muchísimo el riesgo. La **Fase A sola ya entrega valor real** aunque todavía no corra el pipeline desde la UI.

### 3) La separación “UI wrapper” es una excelente decisión

Que la UI sea una capa encima del pipeline actual, sin reescribir módulos centrales, es de las decisiones más fuertes del plan. Eso mantiene:

* bajo acoplamiento,
* menor riesgo de romper inferencia,
* mejor capacidad de pruebas,
* y rollback sencillo.

### 4) Gradio sí encaja bastante bien para este caso

Gradio sigue siendo una opción muy razonable para una herramienta local en Python. Su documentación oficial confirma que `Blocks` está pensado para layouts más flexibles, `FileExplorer` permite seleccionar archivos o directorios desde una raíz local, `Dataframe` es editable cuando se usa de forma interactiva, y `Gallery` sirve para mostrar grids de imágenes con captions. ([gradio.app][1])

---

## Lo más valioso del plan

Lo mejor del documento es que ya trae una **ruta de trabajo completa**:

1. correr,
2. revisar,
3. corregir,
4. exportar,
5. organizar,
6. reutilizar correcciones como dataset.

Eso ya no es solo una GUI; es un **flujo operativo completo**. Para PhotoCat, eso tiene mucho más valor que una simple pantalla bonita.

---

## Donde veo riesgos o puntos a corregir

## 1) La tabla editable está un poco sobreprometida

Aquí está el principal ajuste que haría.

Tu plan dice:

> “Editable genre column” con dropdown por fila dentro del `gr.Dataframe`

El problema es que, según la documentación de Gradio, `Dataframe` soporta tipos de columna como `str`, `number`, `bool`, `date`, `markdown`, etc., pero no veo soporte nativo documentado para un **dropdown por celda con opciones restringidas por columna** al estilo spreadsheet avanzado. Sí es editable, pero editable no significa automáticamente “celda con selector enum”. ([gradio.app][2])

### Qué implica

Tu idea funcional sigue siendo buena, pero yo la cambiaría así:

* **La tabla solo muestra** `final_genre`, `user_genre`, `user_label`
* La edición real del género se hace en **Tab 3 / Inspector**
* Opcionalmente, en Tab 2 permites edición libre de texto solo para power users, pero no la vendería como dropdown por fila

### Mi recomendación

Haz del **Inspector** el lugar oficial para editar.
Eso además mejora consistencia, porque el usuario ve imagen + evidencia + decisión al mismo tiempo.

---

## 2) `FileExplorer` sirve, pero hay que definir bien el alcance

`gr.FileExplorer` sí permite seleccionar archivo o directorio y usar una raíz local. ([gradio.app][3])

Pero en UX real, yo cuidaría esto:

* si el usuario necesita navegar todo el disco, define bien `root_dir`
* si quieres evitar errores, limita el root a una carpeta de trabajo
* si vas a correrlo en local con fotos privadas, mejor no exponer directorios arbitrarios innecesariamente

No es un problema del plan, pero sí una decisión que conviene fijar desde el principio.

---

## 3) Ojo con seguridad de archivos si algún día se comparte

Para uso puramente local está bien.
Pero la guía oficial de Gradio advierte que, si la app se comparte o se despliega, algunos archivos locales pueden quedar accesibles a través de rutas servidas por Gradio, y recomiendan tener cuidado con qué rutas expones. ([gradio.app][4])

### Traducción práctica

Hoy está bien como app local.
Pero deja desde ya una regla clara:

* **sin `share=True`**
* sin publicar esta UI tal cual en red abierta
* y con directorios controlados

---

## 4) “Live log streaming” es viable, pero será la parte más delicada

No porque esté mal pensada, sino porque suele ser donde nacen bugs:

* buffer del subprocess,
* líneas partidas,
* progresos que no salen uniformes,
* cancelación,
* estados inconsistentes si el proceso termina con error.

Tu idea de parsear `[N/M]` está muy bien, pero yo haría una observación:

### Recomendación

No bases toda la UX en el texto del log.
Si puedes, mejor tener una salida estructurada adicional del runner, por ejemplo:

* progreso,
* archivo actual,
* conteos,
* estado final.

Aunque sea temporalmente vía JSON lines o callbacks internas.
Eso vuelve el progreso mucho más robusto que depender solo del texto.

---

## 5) Falta definir mejor el modelo de estado

`ui_state.py` está bien como idea, pero el plan todavía no define suficiente sobre:

* cuál es la fuente de verdad,
* cómo se sincroniza Tab 2 con Tab 3,
* qué pasa al cambiar filtros,
* cómo se conserva el índice actual cuando cambias ordenamiento,
* qué pasa si exportas y luego sigues editando.

### Mi sugerencia

Define explícitamente dos niveles:

**Estado base**

* dataframe completo cargado desde CSV

**Estado derivado**

* filtros actuales
* orden actual
* subset visible
* índice seleccionado
* fila activa en inspector

Eso te evitará bugs típicos de “clickeé una miniatura y se abrió otra imagen”.

---

## 6) El botón “Organize (corrected)” necesita más guardrails

La idea es buenísima, pero es el punto más peligroso del sistema porque ya toca archivos reales.

Yo aquí agregaría tres protecciones obligatorias:

1. **dry-run previo obligatorio**
2. **resumen antes de confirmar**

   * cuántos archivos se moverán
   * a qué carpetas
   * cuántos usan override
3. **restore snapshot / manifest**

   * guardar exactamente qué se movió y desde dónde

Tu plan menciona restore logic, lo cual va bien, pero yo lo volvería un requisito central, no secundario.

---

## 7) “Export only” para persistencia es simple, pero algo frágil

En el cuadro final recomiendas persistir correcciones solo al exportar.
Eso simplifica mucho, sí. Pero también aumenta el riesgo de perder trabajo si:

* se cierra la app,
* crashea,
* o el usuario se confía y no exporta.

### Mejor equilibrio

No haría “save on every click” completo, pero sí una de estas:

* autosave a un archivo temporal cada X cambios, o
* prompt al salir si hay cambios sin exportar

Eso te da seguridad sin complicar demasiado el MVP.

---

## Lo que yo cambiaría del plan, en concreto

## MVP recomendado

Yo lo aterrizaría así:

### Fase A

Déjala casi igual, pero con estos cambios:

* la **edición oficial solo en Inspector**
* Tab 2 como tabla + filtros + selección
* export corrected CSV
* autosave temporal ligero

### Fase B

Runner con:

* estado `idle/running/stopping/done/error`
* progreso estructurado si es posible
* auto-load del CSV al terminar

### Fase C

Organize con:

* preview obligatorio
* manifest JSON/CSV de movimientos
* restore seguro

### Fase D

Muy bien dejarla para después.
No la metería antes de estabilizar revisión + organización.

---

## Evaluación por componente

## Technology choice

**Buena elección.**
Para una app local, Python-first y sin querer abrir frente web complejo, Gradio tiene mucho sentido. `Blocks` da flexibilidad suficiente y evita meter Node/Electron demasiado pronto. ([gradio.app][1])

## Tab 1 — Run

**Bien diseñado.**
Especialmente:

* flags visuales,
* log en vivo,
* progreso,
* stop.

Lo único que reforzaría es el modelo de errores y estados.

## Tab 2 — Review

**Es el corazón del producto.**
Muy bien pensado. Solo ajustaría la expectativa de edición en tabla.

## Tab 3 — Inspector

**Excelente.**
Probablemente es la mejor parte del plan.
Aquí es donde más valor recibe el usuario porque junta imagen + evidencia + acción.

## Data flow

**Correcto y limpio.**
Solo falta formalizar mejor qué es “estado temporal”, qué es “exportado” y qué es “confirmado”.

## File structure

**Suficiente para empezar.**
Yo quizá añadiría:

* `ui_actions.py` o `services/organize_service.py`
* `ui_models.py` para tipos/constantes de estado

Pero no es obligatorio en el arranque.

---

## Mi conclusión honesta

Tu plan está **muy bien encaminado**.
No lo veo como humo ni como algo “bonito en papel pero imposible”. Sí lo veo **implementable** y con buen criterio de producto.

### Sus mayores fortalezas

* flujo completo real,
* fases inteligentes,
* bajo acoplamiento,
* foco en revisión humana antes de mover archivos,
* base útil para dataset futuro.

### Sus mayores debilidades

* algunas expectativas de Gradio están un poco idealizadas,
* falta formalizar mejor el estado,
* y la parte de organización necesita más medidas de seguridad.

## Mi nota final

**8/10 como plan técnico-producto**
**9/10 como MVP si ajustas la edición al Inspector y agregas autosave + manifest de organize**

La decisión más importante que tomaría desde ya es esta:

**No intentes que Tab 2 sea un spreadsheet “inteligente”.
Haz que Tab 2 sea para filtrar/seleccionar y Tab 3 sea para decidir/corregir.**

Eso te simplifica muchísimo la implementación y te da una UX más robusta.

Puedo convertirte esto en una **revisión tipo tech lead**, con secciones de “aprobado / riesgos / cambios obligatorios / backlog recomendado”.

[1]: https://www.gradio.app/docs/gradio/blocks?utm_source=chatgpt.com "Blocks"
[2]: https://www.gradio.app/docs/gradio/dataframe "Gradio  Docs"
[3]: https://www.gradio.app/docs/gradio/fileexplorer "Gradio  Docs"
[4]: https://www.gradio.app/guides/file-access "File Access"
