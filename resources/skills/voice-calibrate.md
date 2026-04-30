---
name: voice-calibrate
description: >
  Captures correction pairs from articles and appends them to the voice calibration file.
  Supports two modes: automated extraction via API (extract-pairs.js) and manual WoZ via
  Claude.ai when no API key is available.
  Use when user says "voice correct", "voice calibrate add", or "voice calibrate".
---

# Voice Calibrate

Captures the diff between an AI draft and the founder's corrected version, extracts
voice rules, and appends them to calibration.

---

## When to invoke

```text
voice correct <article>
voice calibrate add
voice calibrate
```

---

## Mode A: API available (ANTHROPIC_API_KEY is set)

Run the extraction pipeline:

```bash
node scripts/voice/extract-pairs.js \
  --voice bui-thang \
  --ai-draft <path-to-ai-draft> \
  --preferred <path-to-corrected-version> \
  --next-draft <path-to-next-article-to-rewrite>
```

Calibration file: `resources/context/voices/bui-thang/calibration.md`
Schema: `templates/calibration-entry.md`

The script handles extraction, interactive review, appending, and rewrite in one pass.

---

## Mode B: No API key (WoZ — Wizard of Oz via Claude.ai)

Use the extraction prompt below. Paste into Claude.ai, replace INPUT_A and INPUT_B.
Review the proposed entries. Manually append approved ones to calibration.

**Extraction prompt:**

```
You are a voice pattern extractor. INPUT_A is the AI draft (what was wrong).
INPUT_B is the corrected version (what was actually sent).

For each substantive correction, extract one entry with exactly these four fields:

AI-ish: [copy the specific phrase from INPUT_A that was changed]
Preferred: [copy the corresponding phrase from INPUT_B that replaced it]
Why: [1 sentence — specific WHY, not WHAT]
Pattern: [1 reusable instruction in imperative form — no adjectives, must be testable]

Rules:
- Extract 2-4 entries. Ignore typo fixes and word swaps with identical meaning.
- If fewer than 2 substantive corrections exist, output only: "Input pair too similar for meaningful extraction."
- Good Pattern: "Avoid sentence-final slogans. End on a fact or natural observation instead."
- Bad Pattern: "Write more naturally." (untestable adjective)
- Separate entries with a blank line. Output only entries. No preamble, no summary.

INPUT_A: [paste AI draft here]
INPUT_B: [paste corrected version here]
```

After review, append approved entries to:
`resources/context/voices/bui-thang/calibration.md`

Use the schema in `templates/calibration-entry.md` for formatting.

---

## Calibration file location

`resources/context/voices/bui-thang/calibration.md`

Entry format:
```
## Entry N: Short title
AI-ish: [original phrase]
Preferred: [corrected phrase]
Why: [voice judgment]
Pattern: [reusable rule]
```

---

## After adding entries

Run voice status to confirm:

```bash
VOICES_DIR=resources/context/voices bash scripts/voice/voice-status.sh bui-thang
```
