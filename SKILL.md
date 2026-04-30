---
name: seo
description: >
  SEO toolkit with project management, content writing, and 15 audit sub-skills.
  Use this when the user asks to "perform SEO analysis", "run SEO audit",
  "analyze SEO", "check technical SEO", "create project", "content write",
  "SEO plan", "GEO", "AEO", or any SEO-related task. Includes project
  management, AI-powered content writer, and deterministic audit scripts.
---

# SEO Agentic (Antigravity / Claude / Codex)

LLM-first SEO toolkit: project management, content writing, and 15 audit sub-skills with 7 specialist agents and 25 scripts.

## On Load — Display Full Menu

When this skill is loaded (user types `/seo` or triggers the skill), ALWAYS display the full command table below. Do not abbreviate or show a subset.

Show this exact message:

```
SEO Agentic loaded. Available commands:

📋 Project Management
  project new <name> <url>    — Create new SEO project
  project list                — List all projects
  project switch <name>       — Switch active project
  project status              — Show active project context

✍️ Content
  content write <topic>       — Write SEO content in your voice
  content audit <url>         — Content quality & E-E-A-T analysis
  marketing interview         — Extract marketing context via 30-question interview
  content calendar            — Generate 7-day content calendar (or: 30-day calendar)

🔍 Audits
  seo audit <url>             — Full website audit with scoring
  seo page <url>              — Deep single-page analysis
  seo technical <url>         — Technical SEO checks
  seo schema <url>            — Schema detection/validation
  seo images <url>            — Image optimization audit
  seo sitemap <url>           — Sitemap analysis
  seo links <url>             — Backlink profile & link health

📊 Strategy
  seo plan <url>              — Strategic SEO planning
  seo geo <url>               — AI search optimization (GEO)
  seo aeo <url>               — Answer Engine Optimization
  seo competitors <url>       — Competitor page analysis
  seo hreflang <url>          — International SEO validation
  seo programmatic <url>      — Programmatic SEO safeguards
  seo article <url>           — Article data extraction

Tip: Use project name instead of URL after creating a project.
     Example: seo audit diverfi (instead of seo audit https://diverfi.xyz)
```

After displaying the menu, wait for the user to type a command. Do not run any audit or analysis until the user specifies one.

## Deterministic Trigger Mapping

For prompt reliability in Codex/agent IDEs, map common user wording to a fixed workflow:

- If user says `perform seo analysis on <url>` (or similar generic SEO request with a URL), treat it as a **single-URL full audit**.
- If no explicit sub-skill is specified, run the full/page audit path with **LLM-first reasoning** and script-backed evidence.
- For full/page audits, always produce:
  - `FULL-AUDIT-REPORT.md` (detailed findings)
  - `ACTION-PLAN.md` (prioritized fixes)
- If `generate_report.py` is run, also return the saved HTML path (for example `SEO-REPORT.html`).

## Available Commands

| Command | Sub-Skill | Description |
|---------|-----------|-------------|
| `seo audit <url>` | [seo-audit](resources/skills/seo-audit.md) | Full website audit with scoring |
| `seo page <url>` | [seo-page](resources/skills/seo-page.md) | Deep single-page analysis |
| `seo technical <url>` | [seo-technical](resources/skills/seo-technical.md) | Technical SEO checks |
| `content audit <url>` | [content-audit](resources/skills/content-audit.md) | Content quality & E-E-A-T |
| `content write <topic>` | [content-writer](resources/skills/content-writer.md) | SEO content in your writing voice |
| `marketing interview` | [marketing-interviewer](resources/skills/marketing-interviewer.md) | Extract marketing context via 30-question interview |
| `content calendar` / `30-day calendar` | [content-calendar](resources/skills/content-calendar.md) | Generate 7-day or 30-day content calendar |
| `seo schema <url>` | [seo-schema](resources/skills/seo-schema.md) | Schema detection/validation/generation |
| `seo sitemap <url>` | [seo-sitemap](resources/skills/seo-sitemap.md) | Sitemap analysis & generation |
| `seo images <url>` | [seo-images](resources/skills/seo-images.md) | Image optimization audit |
| `seo geo <url>` | [seo-geo](resources/skills/seo-geo.md) | AI search optimization (GEO) |
| `seo programmatic <url>` | [seo-programmatic](resources/skills/seo-programmatic.md) | Programmatic SEO safeguards |
| `seo competitors <url>` | [seo-competitor-pages](resources/skills/seo-competitor-pages.md) | Comparison/alternatives pages |
| `seo hreflang <url>` | [seo-hreflang](resources/skills/seo-hreflang.md) | International SEO validation |
| `seo plan <url>` | [seo-plan](resources/skills/seo-plan.md) | Strategic SEO planning |
| `seo article <url>` | [seo-article](resources/skills/seo-article.md) | Article data extraction & LLM optimization |
| `seo links <url>` | [seo-links](resources/skills/seo-links.md) | External backlink profile & link health |
| `seo aeo <url>` | [seo-aeo](resources/skills/seo-aeo.md) | Answer Engine Optimization (Featured Snippets, PAA, Knowledge Panel) |
| `project list` | [seo-project](resources/skills/seo-project.md) | List all projects + active |
| `project switch <name>` | [seo-project](resources/skills/seo-project.md) | Switch active project |
| `project new <name> <url>` | [seo-project](resources/skills/seo-project.md) | Create new project |
| `project status` | [seo-project](resources/skills/seo-project.md) | Show active project context |
| `voice correct` / `voice calibrate add` | [voice-calibrate](resources/skills/voice-calibrate.md) | Correct AI voice; add calibration entries |
| `voice status` | `VOICES_DIR=resources/context/voices bash scripts/voice/voice-status.sh bui-thang` | Show calibration entry count and recent patterns |

---

> Full orchestration docs, script reference, quality gates, critical rules, and dependencies
> are in [SKILL-DOCS.md](SKILL-DOCS.md). Read it when needed — not on every load.

