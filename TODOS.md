# TODOS

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

### TODO-3: Improve --generate-with-llm to use page content

**What:** In `generate_questions_with_llm()`, fetch the page content first (reuse `fetch_headings` or a plain text extract), then pass it to the LLM alongside the URL. Currently the LLM receives only the URL string and has to guess site topic coverage.

**Why:** `--generate-with-llm` is supposed to produce higher-quality questions than heading parsing. But heading parsing reads the actual page — the LLM-based path doesn't. A benchmark on `https://stripe.com` gets generic "payment" questions, not questions about specific Stripe features. Better input = better benchmark quality.

**Pros:** Makes `--generate-with-llm` actually better than heading parse as intended.

**Cons:** Adds one HTTP fetch before the LLM call. For long pages, need to truncate content passed to LLM (e.g., first 3000 chars of visible text). Minor API cost increase.

**Context:** Found in Phase 2 eng review (2026-04-14) via outside voice review.

**Effort:** S (team ~1h / CC ~10min) | **Priority:** P3
**Depends on:** Phase 2 shipped
