# Changelog

All notable changes to this project will be documented in this file.

## [0.0.3.0] - 2026-04-29

### Added

- **Voice calibration system**: `voice correct` / `voice calibrate add` records correction pairs (AI-ish / Preferred / Why / Pattern) in `resources/context/voices/<voice>/calibration.md`; entries persist across sessions and are loaded alongside writing-dna during content generation
- **`extract-pairs.js`**: 5-step Node.js script that diffs an AI draft vs the human-preferred version, extracts 2–4 calibration entries via Claude, runs interactive review, appends approved entries, and rewrites the next draft — all in one run
- **`voice-status.sh`**: shows entry count, merge readiness, DNA word count (warns >500), and last 5 patterns for any voice
- **Voice calibration templates**: `calibration.template.md` and `dna.template.md` in `resources/context/voices/`
- **`scripts/lib/extract-lib.js`**: shared parsing helpers (`countEntries`, `parseEntries`, `formatEntry`) used by `extract-pairs.js` and tests
- **28 tests total** (13 Node.js + 15 bash): covers parseEntries edge cases, entry formatting, voice script edge cases (resolve_voice fallback, header non-duplication, title truncation, DNA word count, merge reminder threshold)

### Changed

- **content-writer Step 1.3**: now derives voice name from the DNA filename detected in Step 1 (`~/.seo-voices/<name>.md` → `<name>`), instead of hardcoding `bui-thang`
- **Command routing**: SKILL.md is now the single canonical routing table; CLAUDE.md references it instead of duplicating rows; 3 voice commands added to SKILL.md

### Fixed

- `extract-lib.js` regex `\s*` consumed newlines, causing empty field values to silently capture the next line's content — changed to `[ \t]*`
- `voice-calibrate-add.sh` sed character class `[#*_\`\[\]]` was a no-op on macOS BSD sed — replaced with `tr -d`
- `extract-pairs.js` readline interface leaked on error paths — `rl` is now module-level, closed in `.catch()`
- `extract-pairs.js` `parseArgs` silently swallowed flags when a flag value started with `--` — now validates and exits with error
- `voice-status.sh` negative `ENTRIES_SINCE_MERGE` (when calibration.md is manually edited after a merge) now warns and clamps to 0 instead of triggering a false merge reminder

## [0.0.2.0] - 2026-04-26

### Added

- **Marketing Interviewer skill** (`marketing interview`): structured 14-question interview to extract positioning, channel strategy, and content pillars into `marketing-context.md`
- **Content Calendar skill** (`content calendar` / `30-day calendar`): generates a 30-day content plan from marketing context and writing DNA, with date-stamped entries and format distribution
- **Marketing context template**: `resources/context/marketing-context.template.md` for bootstrapping new project marketing context
- **Track-based save in content-writer**: when project context has a `track:` field, drafts save to `~/drafts/<project>/<track>/` for structured project management
- **Motivation balance check in content-writer**: beginner/awareness articles get an outline audit that flags risk-dominated structures before approval

### Changed

- **Token efficiency — 71% reduction**: SKILL.md split into routing table (102 lines, always-loaded) + SKILL-DOCS.md (on-demand); seo-geo/seo-plan/content-writer/marketing-interviewer skill files compressed by ~55–65%
- **seo-project `new` command**: now creates `marketing-context.md` from template and suggests `marketing interview` as next step
- **writing-dna.template.md**: essentials section added; context freshness rules enforce >7-day staleness warnings before writing

### Fixed

- 6 new tests for previously uncovered paths: `query_engine_with_retry` stderr warning, `_format_comparison_table` tied/empty edge cases, `--competitors` valid/malformed/all-skipped scenarios (78 tests total, all pass)

## [0.0.1.0] - 2026-04-17

### Added

- **GEO Score per-engine breakdown**: see which engines (Perplexity, ChatGPT) cite your site, not just an aggregate score
- **Competitor comparison** (`--competitors`): benchmark your GEO Score against competitors side by side
- **LLM-generated questions** (`--generate-with-llm`): now fetches page content so questions are topic-specific, not generic
- **llms.txt hints**: when score is low, the report recommends specific uncited queries to target
- **`--save` flag**: persist GEO scores to `~/.seo-geo-history/` and see deltas between runs
- **Content Writer skill** (`content write <topic>`): write SEO articles in your personal voice with research, outline approval, and DNA learning loop
- **DNA learning loop**: every draft triggers a review that proposes voice learnings, accumulates in `~/drafts/writing-dna-learnings.md`
- **Multi-project management**: `project new`, `project list`, `project switch`, `project status` for managing multiple SEO projects
- **AI Visibility Plan section** in `seo plan` skill: generates GEO strategy with llms.txt template, AI crawler rules, and content structure recommendations
- **On Load menu**: `/seo` now displays the full 20-command menu on first load, not just audit commands
- **Interviewer skill**: extract writing voice DNA from existing articles
- **Project template**: `project.template.md` for structured project context

### Changed

- Renamed `seo content` to `content audit` for clarity
- Renamed `write content` to `content write` for consistent command naming
- CLAUDE.md routing split: seo-agentic commands use direct file reads, gstack skills use Skill tool
- README.md: added Getting Started guide with full command reference

### Fixed

- Empty domain guard in `extract_domain()` no longer causes false-positive citation matches
- Retry logging now prints warning to stderr on second failure
- Engine pair mismatch warning when comparing runs with different engine configurations
- Delta/MOE comparison correctly flags non-significant changes
