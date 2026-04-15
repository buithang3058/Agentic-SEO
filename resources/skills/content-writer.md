---
name: content-writer
description: >
  SEO content writing in user's personal voice. Researches topic via web search
  and SERP analysis, generates outline for approval, then writes full article
  following writing-dna. Use when user says "write content", "write article",
  "viết bài", "viết content", or "content writer".
---

# Content Writer

Writes SEO content in your personal voice. Two phases: research + outline approval,
then writing. Requires `~/.seo-voices/bui-thang.md` (writing-dna file).

---

## Startup

**Step 1: Load writing-dna**

Read `~/.seo-voices/bui-thang.md`. If file does not exist, halt immediately:

```
Writing-DNA file not found at ~/.seo-voices/bui-thang.md
Please create it before running this skill.
```

**Step 2: Collect inputs**

Required:
- **Topic**: chủ đề bài viết
- **Context**: `diverFi` (cá nhân, thẳng, có thể thô) hoặc `Simplize` (chuyên gia, tiết chế, logic)

Optional:
- **Brief**: góc nhìn muốn thể hiện, target audience, experience cá nhân liên quan,
  word count target (default: 1200–2000 từ)

If context is not provided, ask before continuing:
```
Context là gì? diverFi hay Simplize?
```

---

## Phase 1: Research & Outline

### 1.1 Research

1. **Web search** topic → thu thập thông tin mới nhất, data, góc nhìn từ 3–5 sources
2. **SERP analysis**: fetch top 3–5 pages currently ranking for the main keyword
   - Truncate each page to first ~2000 tokens: prioritize headings + first 3 paragraphs
   - If a URL returns error/empty: use the WebSearch snippet for that URL instead
3. **Gap analysis**: tổng hợp — họ viết gì, angle nào, format nào, và quan trọng hơn:
   họ *không* viết gì, hoặc viết chưa đủ sâu, chưa đủ trung thực

### 1.2 Generate outline

Using research findings + user brief + writing-dna "How I sound" examples for the given context:

- **Angle**: 1–2 câu tóm tắt góc tiếp cận khác biệt so với SERP hiện tại
- **Outline**: H2/H3 với 1-line mô tả stake của từng section
- **Hook draft**: 1 ví dụ mở bài áp dụng đúng hard stop #1 (không mở bằng định nghĩa,
  phá vỡ kỳ vọng ngay câu 2)

Output format:

```
## Angle
[1-2 câu]

## Outline
- H2: [tên] — [stake của section này là gì]
  - H3: [sub-point]
- H2: ...

## Hook draft
[Ví dụ mở bài]

## Research notes
- [Competitor 1]: angle + điểm thiếu
- [Competitor 2]: ...
- [Fresh data]: điểm nổi bật từ web search
```

### 1.3 Approval checkpoint

Sau khi output outline, hỏi:
```
Approve outline? Hoặc cho tôi biết cần sửa gì.
```

Wait for response.
- Approval signal: `ok` / `approve` / `được` / `đồng ý` / `yes` / `1` → proceed to Phase 2
- Anything else → revise outline based on feedback, then re-present and ask again

---

## Phase 2: Writing

### 2.1 Setup

- Writing-dna đã loaded từ Startup — không load lại
- Word count:
  - Default: **1200–2000 từ** nếu brief không chỉ định
  - Brief có "ngắn" / "quick" → 800–1000 từ
  - Brief có "pillar" / "deep" / "comprehensive" → 2500–4000 từ

### 2.2 Voice setup

Đọc section **"Who I am"** trong writing-dna, lấy context-specific tone:
- `diverFi` → cá nhân, thẳng, có thể thô. Sẵn sàng thừa nhận sai lầm.
- `Simplize` → chuyên gia, tiết chế, logic. Tiết chế cảm xúc.

Đọc **"How I sound"** examples cho context đang dùng. Đây là pattern để viết —
không phải nguồn sự kiện để trích dẫn.

### 2.3 Write the article

**Mở bài** — apply hard stop #1 (không bao giờ mở bằng định nghĩa):
- Phá vỡ kỳ vọng ngay câu 2
- Hoặc thừa nhận ngay điều người đọc không ngờ
- Xem Hook draft từ Phase 1 làm reference

**Body** — mỗi H2/H3 theo outline đã approve:
- Dùng **thinking pattern** từ writing-dna: Lý thuyết nói gì → thực tế sai ở đâu
- Priority order: (1) Sai lầm/mất tiền → (2) Niềm tin phổ biến nhưng sai → (3) Giải thích nếu cần
- Không list bước, không "bước đầu tiên là..." — kể bằng câu chuyện cụ thể với lý do cụ thể

**Ngắt dòng**: sau một claim hoặc data point quan trọng, follow bằng 1 câu độc lập ≤10 từ.
```
Tôi bị ám ảnh bởi câu chuyện gửi tiết kiệm ngân hàng.
Bởi,
… tôi sợ lạm phát.
```

**Risk/disclaimer** (khi có):
- Câu ngắn, dứt khoát. Không chung chung.
- Đúng: "Crypto có thể về 0. Smart contract có thể bị hack. **Tôi đã mất tiền vì những điều này.**"
- Sai: "Như với mọi khoản đầu tư, cần nghiên cứu kỹ trước khi tham gia."

### 2.4 Apply hard stops

Đọc section **"Hard stops"** trong writing-dna. Apply tất cả — không duplicate ở đây.

Mỗi đoạn phải pass **weight test** trước khi tiếp tục:
> "Đoạn này có chứa: claim cụ thể / số liệu / hệ quả / trải nghiệm cá nhân không?
> Nếu chỉ là filler/transition → viết lại hoặc xóa."

### 2.5 Claim attribution

Vì AI viết thay mặt bạn, cần rõ ràng về nguồn gốc claim:

| Loại claim | Cách viết |
|---|---|
| Từ brief (user tự cung cấp) | "tôi..." (first-person OK) |
| Quan sát thị trường / AI analysis | "theo quan sát..." |
| AI suy luận, chưa chắc | "tôi chưa chắc nhưng..." |
| Writing-dna example pattern | Dùng làm style template, KHÔNG trích dẫn như sự kiện thật |

**Không fabricate trải nghiệm cá nhân.** Nếu brief không có experience cụ thể,
đừng thêm "tôi đã..." từ không khí.

---

## Output

Slug từ topic: lowercase, bỏ dấu tiếng Việt, thay space bằng `-`, giữ chữ+số, truncate 40 ký tự.
Ví dụ: `"DeFi là gì" → defi-la-gi`

Tạo file tại `~/drafts/<slug>-draft.md`:

```markdown
---
title: [H1 title]
keyword: [target keyword chính]
context: [diverFi | Simplize]
date: [YYYY-MM-DD]
status: draft
word_count: [approximate]
---

[full article]
```

Sau khi save, output:
```
Saved: ~/drafts/<slug>-draft.md

Next step (optional):
  content audit ~/drafts/<slug>-draft.md
```

---

## Trigger phrases

User says any of:
- `write content <topic>`
- `write article <topic>`
- `content writer <topic>`
- `viết bài <topic>`
- `viết content <topic>`
- `content-writer <topic>`
