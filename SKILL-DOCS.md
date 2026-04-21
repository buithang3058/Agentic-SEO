# SEO Agentic — Full Documentation

Extended docs for SKILL.md. Load this file when user asks for command details,
script reference, or orchestration specifics.

---

## Orchestration Logic

When the user requests SEO analysis, follow this routing:

### Step 0.5 — Project name resolution

Before any skill runs, check if the `<url>` argument looks like a project name (no dots, no `http`):

1. Slugify the argument (lowercase, strip spaces/diacritics)
2. Check `~/.seo-projects/<slug>/context.md`
3. If found: extract the `url:` field from frontmatter and use it as the target URL
4. If not found: treat the argument as a raw URL

Example: `seo audit diverFi` → slug `diverfi` → reads `~/.seo-projects/diverfi/context.md` → URL `https://diverfi.xyz`

### Step 1 — Identify the Task

- **Project commands** (`project list/switch/new/status`): Read `resources/skills/seo-project.md`
- **Full audit**: Read `resources/skills/seo-audit.md`
- **Single page**: Read `resources/skills/seo-page.md`
- **Specific area**: Read the matching `resources/skills/seo-*.md`
- **Strategic plan**: Read `resources/skills/seo-plan.md` + matching `resources/templates/*.md`
- **Generic `perform seo analysis on <url>`**: treat as single-page full audit → `seo-page.md` → `FULL-AUDIT-REPORT.md` + `ACTION-PLAN.md`

### Step 2 — Collect Evidence

**Primary (LLM-first):** `read_url_content(url)` → baseline evidence.

**Deterministic verification:**
```bash
python3 <SKILL_DIR>/scripts/fetch_page.py <url> --output /tmp/page.html
python3 <SKILL_DIR>/scripts/parse_html.py /tmp/page.html --url <url> --json
python3 <SKILL_DIR>/scripts/generate_report.py <url> --output SEO-REPORT.html  # optional
```

> Do not use third-party mirrors (e.g., `r.jina.ai`) when direct fetch or scripts are available.
> `<SKILL_DIR>` = absolute path to the skill directory containing SKILL.md.

### Step 3 — LLM-First Analysis

Produce findings with: `Finding` / `Evidence` / `Impact` / `Fix`.
Prioritize by impact + effort. Separate confirmed, likely, and unknown issues.
Apply `resources/references/llm-audit-rubric.md` for scoring consistency.

### Step 4 — Baseline Verification Scripts

```bash
python3 <SKILL_DIR>/scripts/robots_checker.py <url>
python3 <SKILL_DIR>/scripts/llms_txt_checker.py <url>
python3 <SKILL_DIR>/scripts/pagespeed.py <url> --strategy mobile
python3 <SKILL_DIR>/scripts/security_headers.py <url>
python3 <SKILL_DIR>/scripts/broken_links.py <url> --workers 5
python3 <SKILL_DIR>/scripts/redirect_checker.py <url>
python3 <SKILL_DIR>/scripts/readability.py /tmp/page.html --json
python3 <SKILL_DIR>/scripts/social_meta.py <url>
python3 <SKILL_DIR>/scripts/internal_links.py <url> --depth 1 --max-pages 20
python3 <SKILL_DIR>/scripts/article_seo.py <url> --keyword "<keyword>" --json
```

Visual (requires Playwright / `conda activate pentest`):
```bash
python3 <SKILL_DIR>/scripts/capture_screenshot.py <url> --all
python3 <SKILL_DIR>/scripts/analyze_visual.py <url> --json
```

If a check fails: report as **environment limitation**, not site issue. Confidence: `Hypothesis`.
Retry at most once, then finalize. Do not loop on web-search fallbacks.

### Step 5 — Specialist Agents

| Agent | File | Focus Area |
|-------|------|------------|
| Technical SEO | [seo-technical.md](resources/agents/seo-technical.md) | Crawlability, indexability, security, URLs, mobile, CWV |
| Content Quality | [seo-content.md](resources/agents/seo-content.md) | E-E-A-T, content metrics, AI content detection |
| Performance | [seo-performance.md](resources/agents/seo-performance.md) | Core Web Vitals (LCP, INP, CLS) |
| Schema Markup | [seo-schema.md](resources/agents/seo-schema.md) | JSON-LD detection, validation, generation |
| Sitemap | [seo-sitemap.md](resources/agents/seo-sitemap.md) | XML sitemap validation and generation |
| Visual Analysis | [seo-visual.md](resources/agents/seo-visual.md) | Screenshots, above-the-fold, responsiveness |
| Verifier | [seo-verifier.md](resources/agents/seo-verifier.md) | Deduplicate findings, validate evidence before final report |

### Step 6 — Quality Gates

- Content minimums: [quality-gates.md](resources/references/quality-gates.md)
- Schema types: [schema-types.md](resources/references/schema-types.md)
- CWV thresholds: [cwv-thresholds.md](resources/references/cwv-thresholds.md)
- E-E-A-T framework: [eeat-framework.md](resources/references/eeat-framework.md)
- Google reference: [google-seo-reference.md](resources/references/google-seo-reference.md)
- LLM rubric: [llm-audit-rubric.md](resources/references/llm-audit-rubric.md)

### Step 6.5 — Verify Findings

```bash
python3 <SKILL_DIR>/scripts/finding_verifier.py --findings-json <raw_findings.json> --json
```

Use verified output for final report tables.

### Step 7 — Score and Report

Default scoring weights (canonical source — also in `seo-audit.md`):

| Category | Weight |
|----------|--------|
| Technical SEO | 25% |
| Content Quality | 20% |
| On-Page SEO | 15% |
| Schema / Structured Data | 15% |
| Performance (CWV) | 10% |
| Image Optimization | 10% |
| AI Search Readiness (GEO) | 5% |

Score interpretation: 90–100 Excellent | 70–89 Good | 50–69 Needs Improvement | 30–49 Poor | 0–29 Critical

### Step 8 — Mandatory Deliverables

For `seo audit`, `seo page`, generic analysis flows:
1. `FULL-AUDIT-REPORT.md` — create at start, update as evidence collected
2. `ACTION-PLAN.md` — create at start, update with prioritized fixes
3. Include HTML report path if generated
4. List all artifacts in final response
5. If blocked by env limits, still write both files + "Environment Limitations" section

---

## Industry Detection

For `seo plan` — detect business type and load matching template:

| Industry | Template |
|----------|----------|
| SaaS / Software | [saas.md](resources/templates/saas.md) |
| Local Service | [local-service.md](resources/templates/local-service.md) |
| E-commerce | [ecommerce.md](resources/templates/ecommerce.md) |
| Publisher / Media | [publisher.md](resources/templates/publisher.md) |
| Agency / Consultancy | [agency.md](resources/templates/agency.md) |
| Other / Generic | [generic.md](resources/templates/generic.md) |

Signals: SaaS = pricing/docs/API/trial | Local = address/phone/GBP | E-commerce = cart/checkout/collections | Publisher = dates/authors/news | Agency = case studies/portfolio

---

## Schema Templates

Pre-built JSON-LD in [templates.json](resources/schema/templates.json):
- Common: BlogPosting, Article, Organization, LocalBusiness, BreadcrumbList, WebSite
- Video: VideoObject, BroadcastEvent, Clip, SeekToAction
- E-commerce: ProductGroup, OfferShippingDetails, Certification
- Other: SoftwareSourceCode, ProfilePage

---

## Validation Scripts

```bash
bash <SKILL_DIR>/scripts/pre_commit_seo_check.sh          # staged HTML: schema placeholders, title length, alt, deprecated types, FID refs
python3 <SKILL_DIR>/scripts/validate_schema.py <file>     # JSON-LD: syntax, @context/@type, placeholders, deprecated types
```

---

## Output Format

Severity: 🔴 Critical (fix now) | ⚠️ Warning (fix within 1 month) | ✅ Pass | ℹ️ Info

Structure: summary table → findings by category → recommendations by impact

---

## Critical Rules

1. **INP not FID** — FID removed 2024-09-09. Sole interactivity metric is INP.
2. **FAQ schema restricted** — government/healthcare only (Aug 2023). Not for commercial sites.
3. **HowTo schema deprecated** — rich results removed Sep 2023. Never recommend.
4. **JSON-LD only** — `<script type="application/ld+json">`. Never Microdata or RDFa.
5. **E-E-A-T everywhere** — applies to ALL competitive queries since Dec 2025.
6. **Mobile-first complete** — 100% since 2024-07-05.
7. **Location page limits** — warn at 30+, hard stop at 50+.
8. **AI crawler management** — check robots.txt for GPTBot, ClaudeBot, PerplexityBot, Applebot-Extended, Google-Extended, Bytespider, CCBot.
9. **LLM-first, resilient** — if scripts fail, still produce complete analysis (confidence: `Likely`).
10. **Always produce artifacts** — `FULL-AUDIT-REPORT.md` + `ACTION-PLAN.md` required for audit flows.
11. **Bound retries** — if core checks fail, finalize with confidence labels. No long loops.
12. **No redundant fallbacks** — if direct fetch + one fallback fail, stop and report limitations.
13. **Freshness tracking** — reference files need `<!-- Updated: YYYY-MM-DD -->`. Flag files >90 days old.

---

## Dependencies

```bash
pip install requests beautifulsoup4
pip install playwright && playwright install chromium  # for visual scripts
# Or: conda activate pentest
```
