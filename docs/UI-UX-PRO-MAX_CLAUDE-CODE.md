# UI UX Pro Max - Guia Completa para Claude Code

## Que es?

**UI UX Pro Max** es un AI Skill de design intelligence para Claude Code (y otros AI coding assistants). Proporciona una base de datos buscable de estilos UI, paletas de color, font pairings, chart types, y UX guidelines que se activa automaticamente cuando trabajas en tareas de UI/UX.

**Repo:** https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
**Web:** https://ui-ux-pro-max-skill.nextlevelbuilder.io/
**npm:** https://www.npmjs.com/package/uipro-cli
**Version actual:** v2.5.0 (Marzo 2025)

### Contenido incluido

| Recurso | Cantidad |
|---------|----------|
| UI Styles | 67 (Minimalism, Glassmorphism, Brutalism, Neumorphism, Bento Grid, Cyberpunk, etc.) |
| Color Palettes | 161 (alineadas por industria/producto) |
| Font Pairings | 57 (Google Fonts curados) |
| Product Types | 161 (con reasoning rules por industria) |
| UX Guidelines | 99 (best practices y accesibilidad) |
| Chart Types | 25 (recomendaciones para dashboards) |
| Tech Stacks | 15 (React, Next.js, Vue, Svelte, Flutter, SwiftUI, etc.) |
| Google Fonts | 1,923 |

---

## Instalacion en Claude Code

### Metodo 1: CLI (Recomendado)

```bash
# 1. Instalar CLI global
npm install -g uipro-cli

# 2. Ir a tu proyecto
cd /path/to/your/project

# 3. Inicializar para Claude Code
uipro init --ai claude
```

Esto crea la estructura `.claude/skills/ui-ux-pro-max/` con todos los archivos necesarios.

### Metodo 2: Instalacion Global (aplica a todos los proyectos)

```bash
uipro init --ai claude --global
```

### Metodo 3: Claude Marketplace

```
/plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill
/plugin install ui-ux-pro-max@ui-ux-pro-max-skill
```

### Comandos CLI adicionales

```bash
uipro versions          # Ver versiones disponibles
uipro update            # Actualizar a la ultima version
uipro init --offline    # Usar assets bundled (sin descargar de GitHub)
uipro init --force      # Sobreescribir archivos existentes
uipro uninstall         # Remover skill
```

### Prerequisitos

- **Python 3.x** requerido para el script de busqueda
  - macOS: `brew install python3`
  - Ubuntu/Debian: `sudo apt update && sudo apt install python3`
  - Windows: `winget install Python.Python.3.12`

---

## Como funciona

### Activacion automatica (Skill Mode)

El skill se activa automaticamente cuando pides trabajo de UI/UX en Claude Code. No necesitas invocar nada manualmente.

**Triggers:** plan, build, create, design, implement, review, fix, improve, optimize, enhance, refactor, check UI/UX code.

**Ejemplos de prompts que lo activan:**
- "Build a landing page for my SaaS product"
- "Design a dashboard for a fintech app"
- "Review this component for accessibility issues"
- "Create a mobile-first navigation"

### Cuando se usa vs cuando no

**DEBE usarse cuando:**
- Disenando nuevas paginas (Landing, Dashboard, Admin, SaaS, Mobile App)
- Creando o refactorizando componentes UI (buttons, modals, forms, tables, charts)
- Eligiendo color schemes, typography, spacing
- Revisando UI code para UX, accesibilidad, o consistencia visual
- Implementando navigation, animations, responsive behavior

**NO se usa cuando:**
- Backend logic puro
- API o database design
- Performance optimization no relacionada con UI
- Infrastructure/DevOps
- Scripts no-visuales

**Criterio:** Usa el skill si la tarea cambia como un feature "se ve, se siente, se mueve, o se interactua".

---

## Uso del Design System Generator

El flagship feature de v2.0 es el **Design System Generator** — un reasoning engine que analiza tus requerimientos y genera un design system completo.

### Generar Design System

```bash
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<product_type> <industry> <keywords>" --design-system
```

### Con nombre de proyecto

```bash
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "beauty spa wellness service" --design-system -p "Serenity Spa"
```

### Persistir a archivos (Master + Overrides Pattern)

```bash
# Master design system
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "fintech dashboard" --design-system --persist -p "TradePro"

# Override por pagina
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "fintech dashboard" --design-system --persist -p "TradePro" --page "settings"
```

Crea estructura: `design-system/MASTER.md` con overrides por pagina.

---

## Busquedas por Dominio

```bash
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<query>" --domain <domain>
```

### Dominios disponibles

| Dominio | Descripcion |
|---------|-------------|
| `product` | Product types y patterns |
| `style` | Design styles (glassmorphism, minimalism, etc.) |
| `color` | Color palettes y sistemas |
| `typography` | Font pairings y type systems |
| `ux` | User experience guidelines |
| `chart` | Data visualization types |
| `landing` | Landing page patterns |
| `element` | UI components |
| `animation` | Motion y transition rules |

### Busquedas por Tech Stack

```bash
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<feature>" --stack <stack>
```

**Stacks soportados:** react, react-native, next.js, vue, svelte, swiftui, flutter, tailwind, shadcn/ui, html/css, nuxt.js, nuxt-ui, angular, laravel, astro, jetpack-compose

---

## Ejemplo Completo: Fintech Dashboard

```bash
# 1. Generar design system completo
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "financial dashboard trading fintech" --design-system -p "TradePro"

# 2. Buscar chart types especificos
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "real-time data charts" --domain chart

# 3. Navigation patterns
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "dashboard navigation sidebar" --domain ux

# 4. Dark mode specifics
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "dark mode professional" --domain style

# 5. React Native guidelines
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "performance real-time updates" --stack react-native
```

---

## Quick Reference: Reglas Criticas de UI/UX

### Prioridades del Skill (1-10)

| # | Categoria | Impacto | Checks clave |
|---|-----------|---------|-------------|
| 1 | Accessibility | CRITICAL | Contraste 4.5:1, Alt text, Keyboard nav, Aria-labels |
| 2 | Touch & Interaction | CRITICAL | Min 44x44px, 8px+ spacing, Loading feedback |
| 3 | Performance | HIGH | WebP/AVIF, Lazy loading, CLS < 0.1 |
| 4 | Style Selection | HIGH | Match product type, Consistency, SVG icons |
| 5 | Layout & Responsive | HIGH | Mobile-first, Viewport meta, No horizontal scroll |
| 6 | Typography & Color | MEDIUM | Base 16px, Line-height 1.5, Semantic tokens |
| 7 | Animation | MEDIUM | 150-300ms, transform/opacity only, reduced-motion |
| 8 | Forms & Feedback | MEDIUM | Visible labels, Error near field, Progressive disclosure |
| 9 | Navigation | HIGH | Predictable back, Bottom nav <=5, Deep linking |
| 10 | Charts & Data | LOW | Legends, Tooltips, Accessible colors |

### Pre-Delivery Checklist

- [ ] Colores con contraste minimo 4.5:1
- [ ] Typography consistente con el pairing elegido
- [ ] Spacing usa escala definida (4pt/8dp)
- [ ] Touch targets minimo 44x44pt
- [ ] Loading states con spinner/progress
- [ ] Error messages cerca de los campos
- [ ] No horizontal scroll en mobile
- [ ] Alt text en todas las imagenes
- [ ] Heading hierarchy secuencial (h1-h6)
- [ ] Keyboard navigation completa
- [ ] Light/Dark mode testeados por contraste

---

## Estructura de archivos (post-instalacion)

```
.claude/
  skills/
    ui-ux-pro-max/
      SKILL.md              # Definicion del skill y triggers
      scripts/
        search.py           # Motor de busqueda BM25 + regex
      data/
        *.csv               # Databases (styles, colors, fonts, etc.)
```

## Links utiles

- **GitHub:** https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- **npm:** https://www.npmjs.com/package/uipro-cli
- **FastMCP:** https://fastmcp.me/skills/details/191/ui-ux-pro-max
- **Claudetory:** https://claudetory.com/skills/ui-ux-pro-max
- **Skills.sh:** https://skills.sh/nextlevelbuilder/ui-ux-pro-max-skill/ui-ux-pro-max
- **DeepWiki:** https://deepwiki.com/nextlevelbuilder/ui-ux-pro-max-skill/1.1-getting-started
- **Mintlify Docs:** https://mintlify.com/explore/nextlevelbuilder/ui-ux-pro-max-skill
