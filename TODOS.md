# TODOS

## P3 — After Phase 2.5 (Competitor Benchmark) validated

### TODO-5: Parallelize --competitors benchmark loop

**What:** Run competitor benchmarks concurrently instead of sequentially. Currently 3 competitors
run one after another — each benchmark takes ~60s, so 3 competitors = ~4 extra minutes.
Use `concurrent.futures.ThreadPoolExecutor` to run all competitor `run_benchmark()` calls in
parallel (within each run, questions are already parallelized).

**Why:** `--competitors` is most useful when comparing 3-5 domains at once. The sequential
loop means each additional competitor adds a full benchmark run to the wait time.
With parallelization, 5 competitors would take ~same time as 1.

**Pros:** Dramatically cuts wait time for users with 2+ competitors. Pattern already exists
in the codebase (`run_benchmark` is thread-safe — it creates its own executor internally).

**Cons:** Increases concurrent API load (could trigger rate limits if many competitors).
Needs rate-limit-aware design: cap outer parallelism at 3-4 concurrent runs.

**Context:** Found in CEO review 2026-04-27. The sequential design is correct for now
(simplicity, avoids rate limits). Revisit once --competitors usage patterns are known.

**Effort:** S (team ~2h / CC ~15min) | **Priority:** P3
**Depends on:** --competitors used in production 5+ times to confirm demand for speed

**Start:** Wrap the competitors loop in `ThreadPoolExecutor(max_workers=3)`.
Each worker calls `run_benchmark()` for one competitor domain. Collect results, build
`competitor_rows` from futures. Rate-limit guard: add `time.sleep(1)` between starts.

---

### TODO-4: Page-level GEO Score (`--page-level` flag)

**What:** Thêm flag `--page-level` vào `geo_benchmark.py`. Khi pass, citation check dùng
full URL path (`example.com/blog/seo-guide`) thay vì chỉ domain (`example.com`).
Chỉ count citation đến đúng trang đó, bỏ qua citation đến các trang khác của cùng domain.

**Why:** Domain-level score đo khả năng AI cite *site*, page-level đo khả năng AI cite
*một trang cụ thể*. Hữu ích khi muốn biết bài blog cụ thể có được AI nhắc đến không.

**Pros:** Granular hơn. Useful cho content marketing (đo từng bài viết).

**Cons:** Cần validate use case thực — ai sẽ dùng và tại sao? Page-level có thể
cho score rất thấp (AI hay cite homepage, không cite deep pages), gây confusion.

**Context:** Đề xuất từ CEO review 2026-04-14. User hỏi về page-level checking.
Defer để validate demand trước.

**Effort:** S (team ~2h / CC ~15min) | **Priority:** P3
**Depends on:** --competitors validated qua ít nhất 2-3 lần chạy thực

**Start:** `extract_domain()` — thêm option giữ lại path. Citation parsers không cần sửa.

---

## P2 — After Phase 2 (GEO Score Integration) is shipped

### ~~TODO-1: Competitor GEO Benchmark~~ DONE

**Shipped:** `--competitors domain1.com,domain2.com` flag in `geo_benchmark.py`.
Runs same questions against all domains, outputs comparison table with gap analysis.
JSON output includes `domains[]` array. 4 new tests added (65 total).

---

### ~~TODO-2: GEO Score trong seo-plan sub-skill~~ DONE

**Shipped:** Added Step 5.5 "AI Visibility Plan (GEO)" to `seo-plan.md` — GEO Score baseline,
score interpretation table, uncited query actions, quarterly timeline, new `AI-VISIBILITY-PLAN.md`
deliverable, and GEO Score row in KPI table.

---

### TODO-2 (archived):

**What:** Khi user chạy `seo plan <url>`, thêm section "AI Visibility Plan" sau các
section Technical/Content/Links hiện tại. Section này bao gồm:
- GEO Score hiện tại (nếu có từ `geo_benchmark.py`)
- Priority actions từ uncited queries
- Timeline gợi ý (Q2: llms.txt, Q3: FAQ sections, Q4: entity building)

**Why:** Kế hoạch chiến lược SEO không có AI visibility thì thiếu một chân quan trọng.
Users sẽ hỏi "làm sao tăng GEO Score" — seo-plan là đúng nơi để trả lời.

**Pros:** Recommendations actionable, gắn với data thực từ benchmark.

**Cons:** `seo-plan` hiện là markdown template — cần quyết định xây lại hay append.
Recommend: append section mới ở cuối, backward-compatible.

**Context:** Deferred from Phase 2 CEO review (2026-04-14).

**Effort:** S (team ~2h / CC ~10min) | **Priority:** P2
**Depends on:** Phase 2 shipped

---

### ~~TODO-3: Improve --generate-with-llm to use page content~~ DONE

**Shipped:** Added `fetch_page_text()` helper — fetches page, strips scripts/styles/nav/footer,
truncates to 3000 chars. `generate_questions_with_llm()` now passes page content to LLM.
Falls back to URL-only if fetch fails. 5 new tests added (70 total).

---

### TODO-3 (archived):

**What:** In `generate_questions_with_llm()`, fetch the page content first (reuse `fetch_headings` or a plain text extract), then pass it to the LLM alongside the URL. Currently the LLM receives only the URL string and has to guess site topic coverage.

**Why:** `--generate-with-llm` is supposed to produce higher-quality questions than heading parsing. But heading parsing reads the actual page — the LLM-based path doesn't. A benchmark on `https://stripe.com` gets generic "payment" questions, not questions about specific Stripe features. Better input = better benchmark quality.

**Pros:** Makes `--generate-with-llm` actually better than heading parse as intended.

**Cons:** Adds one HTTP fetch before the LLM call. For long pages, need to truncate content passed to LLM (e.g., first 3000 chars of visible text). Minor API cost increase.

**Context:** Found in Phase 2 eng review (2026-04-14) via outside voice review.

**Effort:** S (team ~1h / CC ~10min) | **Priority:** P3
**Depends on:** Phase 2 shipped

---

## P3 — After Marketing Skills shipped and used

### TODO-M1: Marketing evolve command

**What:** `marketing evolve` — review and refine an existing `marketing-context.md`.
Ask user about any context that has changed (new positioning, new audience discovered,
channel shift). Compare with existing file, highlight contradictions, propose updates.
Similar to `merge dna` for writing-dna.

**Why:** Marketing context becomes stale over 6–12 months as products evolve and
channels shift. The interview creates it; evolve keeps it current.

**Pros:** Context doesn't go stale. Pattern already proven with `merge dna`. XS effort.

**Cons:** YAGNI risk — don't know yet how often marketing context actually changes
or whether users will run the interview more than once.

**Context:** Proposed in CEO review 2026-04-18 as follow-up to marketing-interviewer.md.
Defer until interview skill has been used 3+ times to validate the need.

**Effort:** S (team ~2h / CC ~20min) | **Priority:** P3
**Depends on:** marketing-interviewer.md shipped and used at least 3 times

**Start:** Fork `merge dna` pattern from `content-writer.md`. Read existing marketing-context.md,
run targeted 10-question interview on changed areas only.

---

### TODO-M2: Portfolio marketing status

**What:** A `marketing status` command that shows all projects with their marketing-context
status: empty / partial / complete, last updated date, and a priority recommendation
("diverFi: calendar outdated — update content calendar").

**Why:** Solo operator managing 3 projects loses track of which project's marketing
context needs attention. A single-screen dashboard prevents context decay across projects.

**Pros:** High leverage for solo 3-project operator. Minimal effort (reads files only,
generates no content). Directly solves the "which project needs my attention?" problem.

**Cons:** Needs marketing-context populated for at least 2 projects to be useful.
Too early to build before the interview skill is proven.

**Context:** Proposed in CEO review 2026-04-18. Deferred until interview has run
for 2+ projects.

**Effort:** XS (team ~1h / CC ~15min) | **Priority:** P3
**Depends on:** marketing-interviewer.md used for 2+ projects

**Start:** `project list`-style skill. Read `~/.seo-projects/*/marketing-context.md`,
check field count vs `...` count, compute completeness %, show last `updated:` date.

---

### TODO-MC1: Marketing context interview cho diverFi

**What:** Chạy `marketing interview` cho dự án diverFi để tạo marketing-context.md.

**Why:** diverFi đang trong giai đoạn tìm hiểu — founder vừa học vừa làm, chưa đủ clarity
để định nghĩa positioning, channel, content pillars. Cần thêm 2 tháng vận hành thực tế
trước khi marketing context có giá trị thực sự.

**Context:** marketing-context.md đã bị xoá ngày 2026-04-20. Framing mới: diverFi =
build-in-public DeFi learner documenting the journey. Value proposition: "Tôi đang học DeFi
từ đầu và ghi lại mọi thứ — kể cả những lần sai — để bạn không phải trả học phí đó."
Đã confirm tại Q2 trong interview 2026-04-20.

**Khi resume:** Bắt đầu fresh interview với framing mới. Global market (US/EU + VN).
Tagline EN: "DeFi explained honestly." Tagline VI: "DeFi không hype. Không shill."

**Effort:** S (CC ~30min interview) | **Priority:** P2
**Review date:** 2026-06-20 (2 tháng sau)
**Depends on:** diverFi có ít nhất 100 users hoặc 10 bài content đã publish

---

### TODO-T1: Token usage tracking hook

**What:** A post-session hook that logs estimated token cost to `~/.seo-stats/YYYY-MM-DD.jsonl`.
Each entry: `{session_id, skill_invoked, files_read: [{path, lines, est_tokens}], total_est_tokens}`.
A `token stats` command shows per-skill average and week-over-week trend.

**Why:** The token efficiency changes (CEO plan 2026-04-20) will save ~10,500 tokens/session
by estimate. Without measurement, there's no way to verify the ROI or catch regressions
if skill files grow back to their original size.

**Pros:** Makes optimization ROI visible. Enables future budget-gating (warn if session
exceeds threshold). Pattern reusable across projects.

**Cons:** Hook needs to intercept Read tool calls — may require Claude Code hooks config.
Estimated token counts are approximate (line × token rate heuristic).

**Context:** Deferred from CEO review 2026-04-20 (token efficiency plan). Implement after
the optimization changes have been shipped and validated for 1-2 weeks.

**Effort:** S (team ~2h / CC ~20min) | **Priority:** P3
**Depends on:** Token efficiency changes shipped (CLAUDE.md consolidation + skill compression)

**Start:** Add a `UserPromptSubmit` hook in Claude Code settings that logs Read tool calls.
Read `~/.claude/settings.json` to see existing hooks pattern.
