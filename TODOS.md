# TODOS

## P2 — After Phase 2 (GEO Score Integration) is shipped

### TODO-1: Competitor GEO Benchmark

**What:** Thêm flag `--competitors domain1.com,domain2.com` vào `geo_benchmark.py`.
Chạy cùng bộ câu hỏi trên tất cả domains. Output bảng so sánh GEO Score.

**Why:** Câu hỏi thực tế nhất là "tôi đang thắng hay thua đối thủ trong AI search?"
Absolute GEO Score không có ý nghĩa nếu không có context.

**Pros:** Metric có ngữ cảnh. Tìm được gap cụ thể — câu nào competitor được cite mà mình không.

**Cons:** Cần validate metric của chính site mình trước khi so sánh. Competitor list từ user.

**Context:** Deferred from Phase 2 CEO review (2026-04-14). Phase 2 phải ship trước để
validate metric. Competitor benchmark là Phase 2.5.

**Effort:** S (team ~3h / CC ~15min) | **Priority:** P2
**Depends on:** Phase 2 shipped + metric validated qua ít nhất 2-3 lần chạy thực

**Start:** `geo_benchmark.py`, thêm `--competitors` flag sau `--url`. Chạy `run_benchmark()`
cho mỗi domain với cùng bộ câu hỏi sinh từ primary URL. Output JSON có `domains[]` array.

---

### TODO-2: GEO Score trong seo-plan sub-skill

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
