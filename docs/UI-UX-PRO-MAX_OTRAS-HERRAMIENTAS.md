# UI UX Pro Max - Guia para Cursor, Antigravity, Windsurf y Otras Herramientas

## Que es?

**UI UX Pro Max** es un AI Skill de design intelligence que funciona con multiples AI coding assistants. Proporciona 67 estilos UI, 161 paletas de color, 57 font pairings, 161 product types, 99 UX guidelines, y 25 chart types.

**Repo:** https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
**npm:** https://www.npmjs.com/package/uipro-cli
**Version:** v2.5.0

---

## Herramientas Soportadas

### Modo Auto-Activate (Skill Mode)
Se activa automaticamente al pedir trabajo de UI/UX:

| Herramienta | Comando de instalacion |
|-------------|----------------------|
| **Claude Code** | `uipro init --ai claude` |
| **Cursor** | `uipro init --ai cursor` |
| **Windsurf** | `uipro init --ai windsurf` |
| **Antigravity** | `uipro init --ai antigravity` |
| **Codex CLI** | `uipro init --ai codex` |
| **Continue** | `uipro init --ai continue` |
| **Gemini CLI** | `uipro init --ai gemini` |
| **OpenCode** | `uipro init --ai opencode` |
| **Qoder** | `uipro init --ai qoder` |
| **CodeBuddy** | `uipro init --ai codebuddy` |
| **Droid** | `uipro init --ai droid` |
| **KiloCode** | `uipro init --ai kilocode` |
| **Warp** | `uipro init --ai warp` |
| **Augment** | `uipro init --ai augment` |
| **Trae** | `uipro init --ai trae` |

### Modo Slash Command (Workflow Mode)
Requiere invocar manualmente con `/ui-ux-pro-max`:

| Herramienta | Uso |
|-------------|-----|
| **Kiro** | `/ui-ux-pro-max Build a landing page` |
| **GitHub Copilot** | `/ui-ux-pro-max Design a dashboard` |
| **Roo Code** | `/ui-ux-pro-max Create a form component` |
| **KiloCode** | `/ui-ux-pro-max Review accessibility` |

### Instalar para TODAS las herramientas a la vez

```bash
uipro init --ai all
```

---

## Instalacion Paso a Paso

### 1. Instalar CLI

```bash
npm install -g uipro-cli
```

### 2. Prerequisito: Python 3.x

El script de busqueda requiere Python 3:

```bash
# macOS
brew install python3

# Ubuntu/Debian
sudo apt update && sudo apt install python3

# Windows
winget install Python.Python.3.12
```

### 3. Inicializar en tu proyecto

```bash
cd /path/to/your/project

# Para una herramienta especifica:
uipro init --ai cursor

# Global (aplica a todos los proyectos):
uipro init --ai cursor --global

# Offline (sin descargar de GitHub):
uipro init --ai cursor --offline
```

### 4. Verificar instalacion

```bash
uipro versions    # Ver versiones disponibles
uipro update      # Actualizar
```

---

## Configuracion por Herramienta

### Cursor

```bash
uipro init --ai cursor
```

**Que crea:**
- `.cursor/rules/` o `.cursorrules` con las reglas de design intelligence
- Scripts de busqueda en el directorio de skills

**Uso en Cursor:**
- Simplemente pide trabajo de UI/UX en el chat: "Design a landing page for my SaaS"
- Cursor detecta las rules y aplica el skill automaticamente

**Tips para Cursor:**
- Las rules se cargan como contexto en cada conversacion de Composer/Chat
- Puedes referenciar archivos generados con `@file` para dar mas contexto
- Usa "Cursor Rules" en settings para verificar que se cargaron

---

### Antigravity

```bash
uipro init --ai antigravity
```

**Que crea:**
- Archivos de configuracion en el formato que Antigravity espera
- Design intelligence rules integradas

**Uso en Antigravity:**
- Pide trabajo de UI/UX normalmente en el chat
- El skill se activa automaticamente

---

### Windsurf

```bash
uipro init --ai windsurf
```

**Que crea:**
- `.windsurfrules` o equivalente con las design rules
- Scripts de busqueda

**Uso en Windsurf:**
- Cascade (el agente de Windsurf) detecta las rules automaticamente
- Pide disenar, crear, o mejorar UI como lo harias normalmente

---

### GitHub Copilot

```bash
uipro init --ai copilot
```

**Modo:** Slash Command (Workflow Mode)

**Uso:**
```
/ui-ux-pro-max Build a responsive dashboard
```

---

### Kiro

```bash
uipro init --ai kiro
```

**Modo:** Slash Command (Workflow Mode)

**Uso:**
```
/ui-ux-pro-max Design a mobile-first navigation
```

---

### Gemini CLI

```bash
uipro init --ai gemini
```

**Modo:** Auto-Activate (Skill Mode)

---

### Codex CLI (OpenAI)

```bash
uipro init --ai codex
```

**Modo:** Auto-Activate (Skill Mode)

---

## Uso del Design System Generator (Aplica a todas las herramientas)

Una vez instalado, el script de busqueda funciona igual independientemente de la herramienta:

### Generar Design System completo

```bash
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<product_type> <industry>" --design-system -p "ProjectName"
```

> **Nota:** La ruta del script puede variar segun la herramienta. Consulta la estructura creada por `uipro init`.

### Busquedas por dominio

```bash
python3 scripts/search.py "dark mode professional" --domain style
python3 scripts/search.py "dashboard charts" --domain chart
python3 scripts/search.py "mobile navigation" --domain ux
python3 scripts/search.py "modern sans-serif" --domain typography
python3 scripts/search.py "fintech blue palette" --domain color
```

### Busquedas por tech stack

```bash
python3 scripts/search.py "responsive layout" --stack react
python3 scripts/search.py "animations" --stack svelte
python3 scripts/search.py "native components" --stack swiftui
python3 scripts/search.py "material design" --stack flutter
```

---

## Tech Stacks Soportados (todas las herramientas)

### Web
- HTML + Tailwind CSS
- React
- Next.js
- shadcn/ui
- Vue
- Nuxt.js
- Nuxt UI
- Angular
- Laravel
- Svelte
- Astro

### Mobile
- SwiftUI (iOS)
- React Native
- Flutter
- Jetpack Compose (Android)

---

## Comparacion: Skill Mode vs Workflow Mode

| Aspecto | Skill Mode (Auto) | Workflow Mode (Slash) |
|---------|-------------------|----------------------|
| Activacion | Automatica al detectar tarea UI/UX | Manual con `/ui-ux-pro-max` |
| Herramientas | Claude Code, Cursor, Windsurf, Antigravity, Codex, Continue, Gemini, OpenCode, Qoder, CodeBuddy, Droid, KiloCode, Warp, Augment, Trae | Kiro, GitHub Copilot, Roo Code, KiloCode |
| Ventaja | Sin friccion, siempre disponible | Control explicito de cuando se usa |
| Desventaja | Puede activarse cuando no se necesita | Requiere recordar el comando |

---

## Comandos CLI Completos

```bash
# Instalar
npm install -g uipro-cli

# Inicializar (proyecto local)
uipro init --ai <tool>

# Inicializar (global)
uipro init --ai <tool> --global

# Inicializar para todas las herramientas
uipro init --ai all

# Offline (assets bundled, sin GitHub)
uipro init --ai <tool> --offline

# Forzar sobreescritura
uipro init --ai <tool> --force

# Ver versiones
uipro versions

# Actualizar
uipro update

# Desinstalar
uipro uninstall
```

---

## Troubleshooting

### Python no encontrado
```bash
# Verificar
python3 --version || python --version

# Instalar
brew install python3          # macOS
sudo apt install python3      # Ubuntu
winget install Python.Python.3.12  # Windows
```

### Skill no se activa en Cursor
- Verifica que `.cursor/rules/` contiene los archivos del skill
- Reinicia Cursor despues de la instalacion
- Revisa Settings > Cursor Rules

### Skill no se activa en Windsurf
- Verifica que `.windsurfrules` existe en la raiz del proyecto
- Reinicia Windsurf/Cascade

### Actualizar a nueva version
```bash
uipro update
# o reinstalar
uipro init --ai <tool> --force
```

---

## Links

- **GitHub:** https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- **npm:** https://www.npmjs.com/package/uipro-cli
- **Releases:** https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/releases
- **Smithery:** https://smithery.ai/skills/nextlevelbuilder/ui-ux-pro-max
- **FastMCP:** https://fastmcp.me/skills/details/191/ui-ux-pro-max
- **DeepWiki:** https://deepwiki.com/nextlevelbuilder/ui-ux-pro-max-skill/1.1-getting-started
- **Mintlify Docs:** https://mintlify.com/explore/nextlevelbuilder/ui-ux-pro-max-skill
- **x-cmd:** https://www.x-cmd.com/skill/nextlevelbuilder/ui-ux-pro-max-skill/
