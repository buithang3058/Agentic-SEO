# Changelog

All notable changes to this project will be documented in this file.

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
