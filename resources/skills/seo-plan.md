---
name: seo-plan
description: >
  Strategic SEO planning for new or existing websites. Industry-specific
  templates, competitive analysis, content strategy, and implementation
  roadmap. Use when user says "SEO plan", "SEO strategy", "content strategy",
  "site architecture", or "SEO roadmap".
---

# Strategic SEO Planning

## Process

### 1. Discovery
Business type, target audience, competitors, goals, current site assessment, budget/timeline, KPIs.

### 2. Competitive Analysis
Top 5 competitors: content strategy, schema, technical setup, keyword gaps, E-E-A-T signals, domain authority.

### 3. Architecture Design
Load industry template from `resources/templates/`. Design URL hierarchy, content pillars, internal linking, sitemap, information architecture.

### 4. Content Strategy
Content gaps vs competitors (`scripts/competitor_gap.py`). Page types and counts. Blog topics and cadence. E-E-A-T building (author bios, credentials). Content calendar with priorities.

### 4.5 Topical Authority Cluster Planning

**Hub-and-spoke model:** Pillar page (3–5K words, head term, covers all subtopics) → Cluster articles (1.5–3K words, long-tail variants, deep dive). Every cluster links back to pillar + 2–3 siblings.

**Planning steps:**
1. Identify 3–5 pillar topics from core competencies
2. Generate 8–15 cluster topics per pillar (Google Autocomplete, PAA, `competitor_gap.py`)
3. Map to URLs: `/pillar/cluster-article`
4. Track with topic-cluster spreadsheet (status, publish dates)

**Industry cluster templates:**

| Industry | Example Pillar | Cluster Sample |
|----------|---------------|----------------|
| Cybersecurity | Penetration Testing | OSINT, Web App, Network, Tools, Reporting |
| SaaS | Product Documentation | Getting Started, API, Integrations, FAQ |
| E-commerce | Product Category | Buying Guide, Comparison, Reviews, FAQ |
| Local Service | Service Area | City pages, FAQ, Pricing, Testimonials |

### 5. Technical Foundation
Hosting/performance, schema per page type, Core Web Vitals targets, AI search readiness, mobile-first.

### 5.5 AI Visibility Plan (GEO)

```bash
python3 <SKILL_DIR>/scripts/geo_benchmark.py <url> --n 20
```

Embed `## AI Visibility Score` into `SEO-STRATEGY.md`. If no key: note `[GEO Score skipped — set PERPLEXITY_API_KEY]`

| GEO Score | Signal | Priority actions |
|-----------|--------|-----------------|
| 0–20 | Rarely cited | llms.txt, FAQ pages, unblock crawlers |
| 21–49 | Partial visibility | Expand thin content, structured data |
| 50–79 | Good citation rate | Freshness, entity signals |
| 80–100 | Strong | Monitor competitors, protect lead |

For each uncited query: create/expand page, add FAQ with exact phrasing, add to `/llms.txt`. Cap at top 5, commercial intent first.

**Timeline:** Q1 `/llms.txt` + unblock crawlers | Q2 FAQ for top 5 uncited | Q3 entity-building content | Q4 re-run benchmark

### 6. Implementation Roadmap

| Phase | Timeline | Focus |
|-------|----------|-------|
| Foundation | Weeks 1–4 | Technical setup, core pages, schema, analytics |
| Expansion | Weeks 5–12 | Content creation, blog launch, internal linking, local SEO |
| Scale | Weeks 13–24 | Advanced content, link building, GEO optimization |
| Authority | Months 7–12 | Thought leadership, PR/media, advanced schema |

## Industry Templates

Load from `resources/templates/`: `saas.md` · `local-service.md` · `ecommerce.md` · `publisher.md` · `agency.md` · `generic.md`

## Output

**Deliverables:** `SEO-STRATEGY.md` · `COMPETITOR-ANALYSIS.md` · `CONTENT-CALENDAR.md` · `IMPLEMENTATION-ROADMAP.md` · `SITE-STRUCTURE.md` · `TOPIC-CLUSTERS.md` · `AI-VISIBILITY-PLAN.md`

**KPI table:** Organic Traffic · Keyword Rankings · Domain Authority · Indexed Pages · Core Web Vitals · Topical Coverage % · GEO Score (baseline → 3mo → 6mo → 12mo targets)
