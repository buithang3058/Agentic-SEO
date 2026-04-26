---
name: content-calendar
description: >
  Content calendar generator. Reads project context and marketing context,
  collects SEO evidence via scripts, then generates an actionable content plan.
  Default: 7-day calendar. Use "30-day calendar" for a longer plan.
  Use when user says "content calendar", "generate calendar", or "30-day calendar".
---

# Content Calendar

Generates an actionable content plan for the active project. Uses project context,
marketing context, existing content, and SEO scripts as evidence.

Default output: 7-day plan (5–7 articles). User can request "30-day calendar".

---

## Step 1: Load Active Project

Check `~/.seo-projects/active`. If the file does not exist or is empty:
```
No active project. Run: project switch <name>
```
Stop.

Read slug from `~/.seo-projects/active`.

Detect calendar length:
- If user typed "30-day calendar" or "30 day" anywhere in their command → `LENGTH=30`
- Otherwise → `LENGTH=7`

---

## Step 2: Load Project Context

Read `~/.seo-projects/<slug>/context.md`. Extract:
- `name:`, `url:`, `language:`, `content_path:` from frontmatter
- Brand section: audience, tone, value prop, competitors
- Writing Instructions: CTA, angles that work, angles to avoid
- Content Calendar section: any existing planned items

If context.md not found:
```
Project context not found: ~/.seo-projects/<slug>/context.md
Run: project new <name> <url>
```
Stop.

---

## Step 3: Load Marketing Context

Read `~/.seo-projects/<slug>/marketing-context.md` if it exists.

- Scan all fields for lines containing only `...`
- If ALL fields are placeholder or file not found:
  ```
  Marketing context not found — calendar based on SEO context only.
  Run `marketing interview` first for stronger angles and positioning.
  ```
  Continue without marketing context.
- If some fields are filled: extract and hold in memory:
  - Brand & Product: value prop, audience, positioning
  - Core Messages: angles that work, angles to avoid
  - Content Strategy: content pillars, content funnel stages
  - Channels & Distribution: primary channels

---

## Step 4: Discover Existing Content

If `content_path` is set in project context (not `...`):
1. List all `.md` and `.mdx` files in `<content_path>/`
2. For each file, read frontmatter to extract `title:` and `keyword:` (if present)
3. Build a list: `[title — keyword]` of existing content

This prevents recommending content that already exists.

If `content_path` is not set or empty: skip this step.

---

## Step 5: Collect SEO Evidence (non-blocking)

Run evidence scripts. If any script fails (network error, missing dependency, timeout):
note "Evidence unavailable: [script name]" and continue — calendar generation does not depend on scripts.

**Extract competitor URLs** from context.md Brand > Competitors field:
- If field is `...` or empty: skip competitor script
- If URLs present: use the first 1–2 URLs

**Script invocations:**

```bash
python3 <SKILL_DIR>/scripts/article_seo.py <project_url> --json
```
Use to understand: existing keyword coverage, related terms, content gaps.

```bash
python3 <SKILL_DIR>/scripts/competitor_gap.py <project_url> --competitor <competitor_url> --json
```
Use to understand: topics competitors cover that you don't. Run once per competitor URL found.

Parse JSON output. Extract:
- From article_seo: top keywords, missing meta signals, related terms
- From competitor_gap: topic clusters present in competitors but absent from your site

---

## Step 6: Generate Calendar

Using all loaded context (project + marketing + existing content + script evidence):

Generate `LENGTH` article proposals. For each article:

```
Article N:
  Title: [compelling H1]
  Keyword: [primary target keyword]
  Funnel stage: Awareness / Consideration / Conversion
  Angle: [one sentence — why this angle vs existing SERP]
  Word count: [600-1000 for Awareness, 1200-2000 for Consideration, 800-1500 for Conversion]
  Source: [why included — competitor gap / pillar topic / audience pain point / existing demand]
```

Prioritization order:
1. Conversion topics (highest ROI) — max 20% of calendar
2. Consideration topics (audience already problem-aware) — 40%
3. Awareness topics (broad reach, brand building) — 40%

Do not repeat topics from existing content (Step 4).
Align angles with marketing-context "Angles that work" where possible.
Avoid angles listed in "Angles to avoid".

---

## Step 7: Adversarial Review

For each article proposed:

Ask internally: "Why would someone NOT click this title?"

If no compelling reason exists to click (generic topic, weak angle, similar to SERP top results): cut the article and replace with a stronger alternative.

Minimum bar: each article must have one of:
- A contrarian angle ("Why X doesn't work the way you think")
- A specific claim ("N things / X% / by [date]")
- A personal/trust signal aligned with brand positioning
- A gap clearly absent from top 3 SERP results (based on competitor evidence)

If fewer than LENGTH articles pass the bar after review: show what you have and explain what was cut.

---

## Step 8: Write Calendar

Write to `~/.seo-projects/<slug>/content-calendar.md`:

```markdown
---
project: <name>
generated: <today's date>
length: <7 or 30>
---

# Content Calendar — <project name>
Generated: <today's date>

## Articles

| # | Title | Keyword | Funnel Stage | Words | Source |
|---|-------|---------|-------------|-------|--------|
| 1 | [title] | [keyword] | Awareness | 1200 | [source] |
...

## Notes

- Marketing context: [loaded / not found]
- SEO evidence: article_seo [OK / unavailable], competitor_gap [OK / unavailable]
- Existing content: [N articles found / not scanned — content_path not set]
- Articles cut in adversarial review: [N]
```

If write fails (permission denied):
```
Error: Could not write to ~/.seo-projects/<slug>/content-calendar.md
Check: ls -la ~/.seo-projects/<slug>/
```

After writing:
```
Content calendar saved: ~/.seo-projects/<slug>/content-calendar.md
<N> articles planned over <LENGTH> days.

Next: content write <title from calendar>
```

---

## Trigger phrases

- `content calendar`
- `generate calendar`
- `30-day calendar`
- `content plan`
