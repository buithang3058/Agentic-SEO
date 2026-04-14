---
status: ACTIVE
source: CEO Plan (plan-ceo-review 2026-04-14)
---
# GEO Score Integration — Unified SEO Audit

Branch: main | Mode: SELECTIVE EXPANSION
Repo: Bhanunamikaze/Agentic-SEO-Skill

## Vision

Không có tool miễn phí, open-source, chạy trong IDE để đo AI citation rate.
SaaS tools bắt đầu từ $29/tháng. Kế hoạch này là bước đầu xây thứ Semrush không làm:
GEO Score chạy trong Claude Code / Codex, không cần account bên ngoài.
Per-engine breakdown trong bước này là building block để sau làm competitive share-of-voice.

## GEO Score Formula

```
GEO Score = cited_count / answered_count * 100

cited_count    = số questions mà ít nhất 1 engine cite (not skipped)
answered_count = tổng questions trừ questions bị skip (cả 2 engines fail)

"Citation" = domain substring trong citations[] array (Perplexity)
             hoặc trong annotations[].url (OpenAI). Không tính text match.
Scale: 0-100 linear.
MOE   = 1.96 * sqrt(p * (1-p) / n) * 100  (95% CI, binary outcome)
```

## Scope Table

| # | Item | Effort | Decision | Step |
|---|------|--------|----------|------|
| 0 | Fix skipped-tracking bug | S | ACCEPTED | 1 |
| 1 | Commit untracked files | S | ACCEPTED | 2 |
| 2 | Commit GitHub SEO cleanup | S | ACCEPTED | 2 |
| 3 | Per-engine breakdown trong output | S | ACCEPTED | 3 |
| 4 | llms.txt gap topic hints | S | ACCEPTED | 3 |
| 5 | seo-geo.md integration | S | ACCEPTED | 4 |
| 6 | seo-audit.md integration | M | ACCEPTED | 5 |
| 7 | Historical tracking (--save flag) | M | ACCEPTED | 6 |
| 8 | Tests for all new code | S | ACCEPTED | alongside each step |
| 9 | URL scheme normalization | XS | ACCEPTED | Step 1 |
| 10 | Delta within MOE note | XS | ACCEPTED | Step 6 |
| 11 | Single-engine mode (either key) | XS | ACCEPTED | Step 1 |
| — | Competitor GEO benchmark | S | DEFERRED | After Phase 2 |
| — | GEO Score trong seo-plan | S | DEFERRED | After Phase 2 |

## Step 1 — Fix skipped-tracking bug + single-engine mode

**File:** `scripts/geo_benchmark.py`

### Fix 1a: skipped-tracking bug in `query_question()`

Replace the current `skipped = False` logic:

```python
def query_question(question: str) -> dict:
    engines_citing = []
    failed_engines = 0

    for engine_name, api_fn in engines:
        response = query_engine_with_retry(lambda q, fn=api_fn: fn(q), question)
        if response is None:
            failed_engines += 1
            continue
        if parsers[engine_name](response, domain):
            engines_citing.append(engine_name)

    # Skipped = ALL engines failed for this question
    skipped = failed_engines == len(engines)
    cited = len(engines_citing) > 0

    return {
        "query": question,
        "cited": cited,
        "engines_citing": engines_citing,
        "skipped": skipped,
    }
```

In `run_benchmark()`:
```python
skipped_count = sum(1 for r in results if r.get("skipped"))
```

Remove dead code block (`all_failed = True` + `break`).

Note: `domain` is captured by closure from `run_benchmark(domain=...)`.

### Fix 1b: single-engine mode in `main()`

Replace the current hard-required Perplexity check:

```python
# Before:
if not perplexity_key:
    print("Error: PERPLEXITY_API_KEY not set...", file=sys.stderr)
    sys.exit(1)

# After:
if not perplexity_key and not openai_key:
    print(
        "Error: No API key found.\n"
        "Set PERPLEXITY_API_KEY and/or OPENAI_API_KEY.\n"
        "  PERPLEXITY_API_KEY: https://www.perplexity.ai/settings/api\n"
        "  OPENAI_API_KEY: https://platform.openai.com/api-keys",
        file=sys.stderr,
    )
    sys.exit(1)

if not perplexity_key:
    print("Note: PERPLEXITY_API_KEY not set — running OpenAI-only mode", file=sys.stderr)
if not openai_key:
    print("Note: OPENAI_API_KEY not set — running Perplexity-only mode", file=sys.stderr)
```

### Fix 1c: URL scheme normalization in `main()`

Add before any URL processing:

```python
if not args.url.startswith(("http://", "https://")):
    args.url = "https://" + args.url
```

## Step 2 — Commit untracked files (before any changes)

```bash
# Stage new files
git add scripts/geo_benchmark.py tests/

# Stage modifications
git add scripts/fetch_page.py LICENSE README.md SKILL.md install.ps1 install.sh \
        resources/references/readme-audit-rubric.md

# Stage deletions
git rm resources/agents/seo-github-analyst.md \
       resources/agents/seo-github-benchmark.md \
       resources/agents/seo-github-data.md \
       resources/references/github-api-ops.md \
       resources/references/github-ranking-factors.md \
       resources/skills/seo-github.md \
       resources/templates/github-seo-report.md \
       resources/templates/github-weekly-scorecard.md \
       scripts/github_api.py scripts/github_community_health.py \
       scripts/github_competitor_research.py scripts/github_readme_lint.py \
       scripts/github_repo_audit.py scripts/github_search_benchmark.py \
       scripts/github_seo_report.py scripts/github_traffic_archiver.py

git commit -m "feat: add GEO benchmark script and tests; remove GitHub SEO scope"
```

Use explicit file paths, not globs, to avoid failure if any file was already removed.

## Step 3 — Update geo_benchmark.py output format

### Per-engine breakdown

Add to `format_text_report()` after the main GEO Score line:

```
Per-engine breakdown:
  Perplexity (sonar):      X% (A/N)
  OpenAI (gpt-4o-search):  Y% (B/N)
  Both engines cited:      Z% (C/N)    [where C = |A ∩ B|]
  Either engine (GEO):     S% (D/N)    [where D = A+B-C, identical to GEO Score]
```

Math: D = A + B - C. Example: A=9, B=7, C=6 → D=10 (50%).
`GEO Score = D / N * 100`.

Add to JSON output (`total` = global N for all engines):
```json
"per_engine": {
  "perplexity": {"cited": 9, "total": 20},
  "openai":     {"cited": 7, "total": 20}
}
```

### llms.txt gap topic hints

Trigger: any not-cited question, cap at 5. Append to `format_text_report()`.

Output format:
```
## llms.txt Content Gap Hints

Based on uncited queries, consider adding these topic pointers to /llms.txt:

  "How to audit Core Web Vitals?"  → add a pointer to your CWV guide page in /llms.txt
  "What is E-E-A-T?"               → add a pointer to your E-E-A-T content in /llms.txt
  (5 suggestions max)

See https://llmstxt.org for format.
```

Implementation:
```python
for q in not_cited_questions[:5]:
    topic = q.rstrip("?")
    lines.append(f'  "{q}" → add a pointer to your {topic} page in /llms.txt')
```

No URL generation — user fills in the actual paths.

## Step 4 — Update seo-geo.md

Add to the "Output" section of `resources/skills/seo-geo.md`:

```markdown
## Measured GEO Score

Run geo_benchmark.py for empirical citation rate (requires at least one API key):

    python3 <SKILL_DIR>/scripts/geo_benchmark.py <url> --n 20

Keys: PERPLEXITY_API_KEY and/or OPENAI_API_KEY. Either alone enables single-engine mode.

`<SKILL_DIR>` = the skill install path (e.g., `~/.claude/skills/seo` or the
project-local `.claude/skills/seo`). The executing agent resolves this from context.

Embed the full text output (the `## AI Visibility Score` section) into GEO-ANALYSIS.md.
The qualitative analysis sections above are retained alongside the measured score.
```

## Step 5 — Update seo-audit.md

Add to `resources/skills/seo-audit.md`, in the script evidence collection section:

```markdown
### GEO Score (AI Visibility)

Only for URL targets. If PERPLEXITY_API_KEY or OPENAI_API_KEY is set:

    python3 <SKILL_DIR>/scripts/geo_benchmark.py <url> --n 20

Append the output (the `## AI Visibility Score` block) to the end of FULL-AUDIT-REPORT.md.
This section is append-only — does not modify existing report format.

If neither key is set, append:
`[GEO Score skipped: set PERPLEXITY_API_KEY or OPENAI_API_KEY to enable]`

Performance: adds ~30-60s at N=20, workers=5.
For faster iterative work: `--n 10` (~15-30s, MOE ±31%).
```

## Step 6 — Historical tracking (--save flag)

Add `--save` flag to `geo_benchmark.py` CLI.

When `--save` is passed:
1. `os.makedirs("~/.seo-geo-history/", exist_ok=True)`
2. Write JSON to `~/.seo-geo-history/<domain>-YYYY-MM-DD-HHMMSS.json`
3. Previous = newest file by filename sort matching `<domain>-*.json`, excluding just-written file
4. Display delta if previous exists

JSON schema:
```json
{
  "domain": "example.com",
  "url": "https://example.com",
  "timestamp": "2026-04-14T10:30:00Z",
  "score": 40.0,
  "n": 20,
  "margin_of_error": 21.91,
  "engine_pair": "perplexity+openai",
  "per_engine": {
    "perplexity": {"cited": 9, "total": 20},
    "openai": {"cited": 7, "total": 20}
  },
  "results": [...]
}
```

Delta output with MOE note:
```
Previous run: 2026-04-07 → Score: 40/100
This run: 2026-04-14 → Score: 45/100 (+5 points)
Note: delta (+5) is within margin of error (±22) — not statistically significant
```

Note: only show "not statistically significant" note when `abs(delta) < current_moe`.

Error handling for --save:
```python
try:
    os.makedirs(history_dir, exist_ok=True)
    with open(save_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Saved to {save_path}", file=sys.stderr)
except Exception as e:
    print(f"Warning: could not save history: {e}", file=sys.stderr)
    # Do not fail — benchmark output is still shown
```

Limitation: `~/.seo-geo-history/` is hardcoded. In CI/Docker, skip `--save` or set `HOME`.

## Deferred to TODOS.md

See `TODOS.md` for:
1. Competitor GEO benchmark (P2)
2. GEO Score in seo-plan sub-skill (P2)

## Success Criteria

1. `seo audit <url>` with key set → report has `## AI Visibility Score` at end
2. `seo audit <url>` without key → report has skip note, no error
3. `geo_benchmark.py ... --save` → writes JSON, next run shows delta with MOE note
4. `check_data_sufficiency` returns `reliable: False` when >50% questions skipped
5. Single-engine mode works with only Perplexity OR only OpenAI key
6. URL without scheme (`example.com`) works correctly
7. All test groups pass: citation parsers, score formula, error/retry, skip threshold,
   per-engine breakdown, llms.txt hints, --save, delta, URL scheme normalization
