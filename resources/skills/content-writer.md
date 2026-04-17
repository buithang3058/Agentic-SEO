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
If no file exists, halt immediately:

```
Writing-DNA file not found at ~/.seo-voices/
Please create one from the template at resources/context/writing-dna.template.md
and save it to ~/.seo-voices/<your-name>.md
```

**Step 1.5: Load active project context (if any)**

Check `~/.seo-projects/active`. If the file exists and is non-empty:
1. Read the slug from `~/.seo-projects/active`
2. Read `~/.seo-projects/<slug>/context.md`
3. Check if brand fields are filled: scan the Brand section for lines containing only `...`
   - If ALL brand fields are placeholder (`...`): warn and skip project context:
     ```
     Project context is empty. Fill in ~/.seo-projects/<slug>/context.md for better results.
     Continuing with DNA only.
     ```
   - If at least some fields are filled: extract and hold in memory:
     - `name`, `url`, `language`, `content_path` from frontmatter
     - Brand section (audience, tone, value prop) — skip fields still showing `...`
     - Writing Instructions section (CTA, angles) — skip fields still showing `...`
4. Show: `Project: <name> (<url>) | Language: <language> | Save to: <content_path or ~/drafts/>`

If `~/.seo-projects/active` does not exist or is empty, continue without project context.

**Step 2: Collect inputs**

Required:
- **Topic**: article topic

Optional:
- **Brief**: angle/perspective, target audience, relevant personal experience,
  word count target (default: 1200–2000 words)

If active project context was loaded in Step 1.5, merge it into the brief automatically:
- Audience from project context → default target audience (brief can override)
- Tone from project context → writing tone hint
- Writing Instructions (CTA, angles) → appended to brief context
- User's explicit brief always takes precedence over project defaults

---

## Phase 1: Research & Outline

### 1.1 Research

1. **Web search** topic → gather latest information, data, perspectives from 3–5 sources
2. **SERP analysis**: fetch top 3–5 pages currently ranking for the main keyword
   - Truncate each page to first ~2000 tokens: prioritize headings + first 3 paragraphs
   - If a URL returns error/empty: use the WebSearch snippet for that URL instead
3. **Gap analysis**: synthesize — what angles/formats do they cover, and more importantly:
   what they *don't* cover, or cover without enough depth or honesty

### 1.2 Generate outline

Using research findings + user brief + writing-dna "How I sound" examples:

- **Angle**: 1–2 sentence summary of the differentiating approach vs current SERP
- **Outline**: H2/H3 with 1-line description of each section's stake
- **Hook draft**: 1 example opening applying hard stop #1 (never open with a definition,
  break expectations by sentence 2)

Output format:

```
## Angle
[1-2 sentences]

## Outline
- H2: [title] — [what's at stake in this section]
  - H3: [sub-point]
- H2: ...

## Hook draft
[Example opening]

## Research notes
- [Competitor 1]: angle + what's missing
- [Competitor 2]: ...
- [Fresh data]: key finding from web search
```

### 1.3 Approval checkpoint

After presenting the outline, ask:
```
Approve outline? Or tell me what to change.
```

Wait for response.
- Approval signal: `ok` / `approve` / `yes` / `1` → proceed to Phase 2
- Anything else → revise outline based on feedback, then re-present and ask again

---

## Phase 2: Writing

### 2.1 Setup

- Writing-dna already loaded from Startup — do not reload
- Word count:
  - Default: **1200–2000 words** unless brief specifies otherwise
  - Brief contains "short" / "quick" → 800–1000 words
  - Brief contains "pillar" / "deep" / "comprehensive" → 2500–4000 words

### 2.2 Voice setup

Read the **"Who I am"** section in writing-dna to understand the overall voice.

Read **"How I sound"** examples. These are writing patterns to follow —
not real events to cite as facts.

### 2.3 Write the article

**Opening** — apply hard stop #1 (never open with a definition):
- Break expectations by sentence 2
- Or immediately acknowledge something the reader doesn't expect
- Use the Hook draft from Phase 1 as reference

**Body** — each H2/H3 following the approved outline:
- Apply the **thinking pattern** from writing-dna: What theory says → where reality diverges
- Priority order: (1) Mistakes/losses → (2) Common beliefs that are wrong → (3) Explanation if needed
- No step lists, no "first step is..." — tell it as a specific story with specific reasons

**Line breaks**: after an important claim or data point, follow with 1 standalone sentence ≤10 words.
```
[Example — write in the user's voice, not this placeholder]
```

**Risk/disclaimer** (when applicable):
- Short, direct sentences. Not generic.
- Good: "Crypto can go to zero. Smart contracts can be hacked. I've lost money because of both."
- Bad: "As with any investment, please do thorough research before participating."

### 2.4 Apply hard stops

Read the **"Hard stops"** section in writing-dna. Apply all of them — do not duplicate here.

Every paragraph must pass the **weight test** before continuing:
> "Does this paragraph contain: a specific claim / data point / consequence / personal experience?
> If it's only filler/transition → rewrite or delete."

### 2.5 Claim attribution

Since AI writes on your behalf, be explicit about claim origins:

| Claim type | How to write it |
|---|---|
| From brief (user-provided) | "I..." (first-person OK) |
| Market observation / AI analysis | "Based on observation..." |
| AI inference, uncertain | "I'm not certain, but..." |
| Writing-dna example pattern | Use as style template only — do NOT cite as real events |

**Never fabricate personal experience.** If the brief has no specific experience,
do not add "I once..." from thin air.

---

## Output

**Slug:** strip diacritics, lowercase, replace spaces with `-`, keep alphanumeric + hyphens, truncate to 50 chars.
- English: `"What is DeFi" → what-is-defi`
- Vietnamese: `"DeFi là gì" → defi-la-gi`

**Save location:**
- If active project has `content_path` set → save to `<content_path>/<slug>.mdx`
- Otherwise → save to `~/drafts/<slug>-draft.md`

**Language:** Write the article in the language specified by the active project's `language` field.
- If `language: Vietnamese` → write in Vietnamese
- If not set → write in English (default)

Create the file with this frontmatter:

```markdown
---
title: [H1 title]
keyword: [primary target keyword]
date: [YYYY-MM-DD]
status: draft
word_count: [approximate]
---

[full article]
```

After saving, output:
```
Saved: <full path to saved file>
```

Continue immediately to Phase 3: DNA Review.

---

## Phase 3: DNA Review

Runs automatically after the draft file is saved. Do not ask the user if they want to run it.

### 3.1 Analyze article

Re-read `~/drafts/<slug>-draft.md`. Analyze for 4 types of proposals:

**Strong examples** — passages that apply voice/hook/body/disclaimer patterns well,
not yet in DNA or better than the current DNA example.

**New signature phrases** — recurring phrases or sentence structures that appear in the article
and are not yet in the DNA.

**Pattern refinements** — Pattern A/B/C used in a subtle or different way compared to
its current description in the DNA.

**New hard stops / exceptions** — a new rule emerged, or an exception to an existing rule worth remembering.

If no proposals (article adds nothing new vs DNA): output
`DNA review: nothing new — this article added no new patterns.` and stop.

### 3.2 Present proposals

For each proposal, display in this format:

```
DNA Proposal #N — [Type: Examples | Phrases | Pattern | Hard stop]

"[excerpt or phrase]"

Reason: [why it's good, why it matters]

Diff:
  Section: [section name in DNA]
+ [line to add]

Save to learnings? (y/n/edit)
```

- `y` or `yes` → save this proposal
- `n` or `no` → skip
- `edit [content]` → use the user's version instead of the original proposal, then save

Ask about each proposal one at a time. Do not batch.

### 3.3 Save approved learnings

Approved proposals (including `edit`) → append to `~/drafts/writing-dna-learnings.md`:

```markdown
## [slug] — [YYYY-MM-DD]

### Examples
- "[excerpt]" ← [short reason]

### Phrases
- "[phrase]" — [when to use]

### Pattern updates
- Pattern [A/B/C]: [refinement]

### Hard stops
- [new rule or exception]
```

Only write sections that have content. Omit empty sections.

Output when done:
```
DNA learnings saved: X items → ~/drafts/writing-dna-learnings.md

Next steps (optional):
  merge dna       ← fold learnings into DNA when you have enough articles
  content audit ~/drafts/<slug>-draft.md
```

---

## Merge DNA Command

Triggered when user says: `merge dna`, `merge writing dna`

### Step 1: Load learnings log

Read `~/drafts/writing-dna-learnings.md`.
If file does not exist or is empty:
```
No learnings to merge. Write more articles to accumulate learnings.
```
Stop.

### Step 2: Load current DNA

Read DNA file at `~/.seo-voices/` (first `.md` file found).

### Step 3: Deduplicate and synthesize

Compare each learning against the current DNA:
- If content is duplicate or equivalent already exists → skip
- If it conflicts with an existing rule → flag separately, ask user

### Step 4: Present full diff

Show the before/after DNA diff — everything that will change:

```
DNA Merge Preview (vX.Y → vX.Y+1)
[date]

Changes:
+ [new line]
+ [new line]
~ [modified line] (was: "...")

Conflicts (need decision):
! [conflict #1]: learning "[...]" conflicts with hard stop "[...]"
  Keep hard stop / Update hard stop / Drop learning? (1/2/3)

Merge into DNA? (y/n)
```

Resolve conflicts before asking for the final merge approval.

### Step 5: Update DNA

If user approves:

1. Update `~/.seo-voices/<name>.md` with the approved changes
2. Bump version in frontmatter/footer: `vX.Y → vX.Y+1`
3. Update the `Updated:` line at the bottom of the file with today's date and a summary
4. Archive learnings log: create `~/drafts/writing-dna-learnings-archive/` if it does not exist,
   then copy `~/drafts/writing-dna-learnings.md`
   → `~/drafts/writing-dna-learnings-archive/[YYYY-MM-DD].md`
5. Clear the content of `~/drafts/writing-dna-learnings.md` (keep the file, clear the content)

Output:
```
DNA updated to vX.Y+1 — [N] changes merged.
Learnings archived: ~/drafts/writing-dna-learnings-archive/[date].md
```

---

## Trigger phrases

User says any of:
- `content write <topic>`
- `write article <topic>`
- `content writer <topic>`
- `content-writer <topic>`
- `merge dna`
- `merge writing dna`
