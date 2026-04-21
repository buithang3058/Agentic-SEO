---
name: content-writer
description: >
  SEO content writing in user's personal voice. Researches topic via web search
  and SERP analysis, generates outline for approval, then writes full article
  following writing-dna. After writing, reviews article and proposes DNA learnings.
  Use when user says "content write", "write article", "content writer", or "merge dna".
---

# Content Writer

Writes SEO content in your personal voice. Three phases: research + outline approval,
writing, then DNA review. Requires `~/.seo-voices/<name>.md` (writing-dna file).

Also handles: `merge dna` — merges accumulated learnings into your DNA file.

---

## Startup

**Step 1: Load writing-dna**

Detect DNA file path: check `~/.seo-voices/` for `.md` files. Use the first one found.
If no file exists, halt: "Writing-DNA file not found at ~/.seo-voices/ — create one from
resources/context/writing-dna.template.md and save to ~/.seo-voices/<your-name>.md"

**Step 1.5: Load active project context (if any)**

Check `~/.seo-projects/active`. If non-empty:
1. Read slug → read `~/.seo-projects/<slug>/context.md`
2. If all Brand fields are `...` → warn and skip project context
3. If partial → extract: name, url, language, content_path, Brand section, Writing Instructions
4. Show: `Project: <name> (<url>) | Language: <language> | Save to: <content_path>`
5. Read `~/.seo-projects/<slug>/marketing-context.md` if it exists:
   - If ALL fields are `...` → skip silently
   - If partial → extract: value prop, audience, positioning, angles that work/avoid, content pillars, CTA mapping
   - Skip Writing Instructions from AI Skills section (use context.md's instead)

**Step 2: Collect inputs**

Required: **Topic**. Optional: angle, audience, experience, word count (default 1200–2000).

Project context auto-merges into brief (audience, tone, CTAs, angles). User's explicit brief
always overrides project defaults.

---

## Phase 1: Research & Outline

### 1.1 Research

1. Web search topic → gather latest info from 3–5 sources
2. SERP: fetch top 3–5 ranking pages (first ~2000 tokens each: headings + first 3 paragraphs)
3. Gap analysis: what competitors cover, and more importantly what they don't

### 1.2 Generate outline

Present: **Angle** (1–2 sentences differentiating from current SERP), **Outline** (H2/H3 with
1-line stake per section), **Hook draft** (opening that never starts with a definition),
**Research notes** (per competitor: angle + gap; fresh data from web search).

### 1.3 Approval checkpoint

Ask: "Approve outline? Or tell me what to change."
- `ok` / `yes` / `approve` / `1` → proceed to Phase 2
- Anything else → revise and re-present

---

## Phase 2: Writing

### 2.1 Setup

DNA loaded from Startup — do not reload.
Word count: default 1200–2000 | "short/quick" → 800–1000 | "pillar/deep/comprehensive" → 2500–4000

### 2.2 Voice setup

Read **"Who I am"** and **"How I sound"** sections in writing-dna.
Examples are style patterns — not real events to cite as facts.

### 2.3 Write

**Opening:** break expectations by sentence 2. Use Hook draft from Phase 1 as reference.

**Body:** follow approved outline. Apply thinking pattern: theory → where reality diverges.
Priority: (1) mistakes/losses → (2) common wrong beliefs → (3) explanation.
No step lists. Specific stories with specific reasons.
After important claims: follow with a standalone sentence ≤10 words.

**Risk/disclaimer:** short, direct sentences. Specific, not generic.
Good: "Crypto can go to zero. Smart contracts can be hacked. I've lost money because of both."

### 2.4 Apply hard stops

Read **"Hard stops"** in writing-dna. Apply all. Every paragraph passes weight test:
"Does this contain: specific claim / data point / consequence / personal experience? If not → rewrite."

### 2.5 Claim attribution

| Claim type | How to write it |
|---|---|
| From brief (user-provided) | "I..." (first-person OK) |
| Market observation / AI analysis | "Based on observation..." |
| AI inference, uncertain | "I'm not certain, but..." |
| Writing-dna example pattern | Use as style only — do NOT cite as real events |

Never fabricate personal experience.

---

## Output

**Slug:** strip diacritics, lowercase, spaces → `-`, alphanumeric + hyphens, truncate to 50 chars.

**Save location:** `<content_path>/<slug>.mdx` if project set, otherwise `~/drafts/<slug>-draft.md`

**Language:** use project `language` field. Vietnamese if set, English if not.

Frontmatter: `title`, `keyword`, `date` (YYYY-MM-DD), `status: draft`, `word_count`.

After saving, output: `Saved: <full path>` then continue immediately to Phase 3.

---

## Phase 3: DNA Review

Runs automatically after save — do not ask.

### 3.1 Analyze

Re-read saved draft. Look for 4 proposal types:
- **Strong examples** — applies voice/hook/body/disclaimer well, better than or absent from DNA
- **New signature phrases** — recurring sentence structures not yet in DNA
- **Pattern refinements** — A/B/C pattern used in a subtle/different way vs current description
- **New hard stops / exceptions** — new rule emerged or exception worth remembering

If nothing new: output "DNA review: nothing new — this article added no new patterns." and stop.

### 3.2 Present proposals

For each, one at a time: show type, excerpt, reason, and diff (section + line to add).
Ask: "Save to learnings? (y/n/edit)"
- `y` → save | `n` → skip | `edit [content]` → use user's version and save

### 3.3 Save approved learnings

Append to `~/drafts/writing-dna-learnings.md` under slug + date header.
Sections: Examples, Phrases, Pattern updates, Hard stops (omit empty sections).

Output: "DNA learnings saved: X items → ~/drafts/writing-dna-learnings.md"
Next steps hint: `merge dna` | `content audit ~/drafts/<slug>-draft.md`

---

## Merge DNA Command

Triggered by: `merge dna` / `merge writing dna`

1. Read `~/drafts/writing-dna-learnings.md` — if empty, stop with "No learnings to merge."
2. Read DNA file at `~/.seo-voices/` (first `.md`)
3. Deduplicate: skip equivalents, flag conflicts for user decision
4. Show full diff preview (additions, modifications, conflicts) — resolve conflicts before final ask
5. On approval: update DNA file, bump version, update date line, archive learnings log

Output: "DNA updated to vX.Y+1 — N changes merged. Learnings archived: [path]"

---

## Trigger phrases

- `content write <topic>` / `write article <topic>` / `content writer <topic>`
- `content-writer <topic>` / `merge dna` / `merge writing dna`
