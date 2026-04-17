---
name: content-writer
description: >
  SEO content writing in user's personal voice. Researches topic via web search
  and SERP analysis, generates outline for approval, then writes full article
  following writing-dna. After writing, reviews article and proposes DNA learnings.
  Use when user says "write content", "write article", "viết bài", "viết content",
  "content writer", or "merge dna".
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

**Step 2: Collect inputs**

Required:
- **Topic**: chủ đề bài viết

Optional:
- **Brief**: góc nhìn muốn thể hiện, target audience, experience cá nhân liên quan,
  word count target (default: 1200–2000 từ)

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

Using research findings + user brief + writing-dna "How I sound" examples:

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

Đọc section **"Who I am"** trong writing-dna để nắm giọng văn tổng thể.

Đọc **"How I sound"** examples. Đây là pattern để viết —
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
date: [YYYY-MM-DD]
status: draft
word_count: [approximate]
---

[full article]
```

Sau khi save, output:
```
Saved: ~/drafts/<slug>-draft.md
```

Tiếp tục ngay Phase 3: DNA Review.

---

## Phase 3: DNA Review

Chạy tự động ngay sau khi file draft được save. Không hỏi user có muốn chạy không.

### 3.1 Analyze article

Đọc lại `~/drafts/<slug>-draft.md`. Phân tích theo 4 loại đề xuất:

**Examples hay** — đoạn nào áp dụng tốt voice/hook/body/disclaimer pattern, chưa có
trong DNA hoặc hay hơn example hiện tại.

**Signature phrases mới** — cụm từ/cấu trúc câu đặc trưng xuất hiện trong bài
mà chưa có trong DNA.

**Pattern refinements** — Pattern A/B/C được dùng theo cách tinh tế hoặc khác so với
mô tả hiện tại trong DNA.

**Hard stops mới / exceptions** — rule mới xuất hiện, hoặc trường hợp ngoại lệ
với rule hiện tại cần ghi nhớ.

Nếu không có đề xuất nào (bài không có gì mới so với DNA): output
`DNA review: nothing new — bài này không thêm pattern mới.` và dừng.

### 3.2 Present proposals

Với mỗi đề xuất, hiển thị theo format:

```
DNA Proposal #N — [Loại: Examples | Phrases | Pattern | Hard stop]

"[excerpt hoặc phrase]"

Lý do: [tại sao hay, tại sao quan trọng]

Diff:
  Section: [tên section trong DNA]
+ [dòng sẽ thêm]

Lưu vào learnings? (y/n/edit)
```

- `y` hoặc `yes` → lưu đề xuất này
- `n` hoặc `no` → bỏ qua
- `edit [nội dung]` → dùng nội dung user nhập thay vì đề xuất gốc, sau đó lưu

Hỏi từng đề xuất một. Không batch.

### 3.3 Save approved learnings

Các đề xuất được approve (kể cả `edit`) → append vào `~/drafts/writing-dna-learnings.md`:

```markdown
## [slug] — [YYYY-MM-DD]

### Examples
- "[excerpt]" ← [lý do ngắn]

### Phrases
- "[phrase]" — [khi nào dùng]

### Pattern updates
- Pattern [A/B/C]: [refinement]

### Hard stops
- [rule mới hoặc exception]
```

Chỉ ghi các section có nội dung. Bỏ section rỗng.

Output sau khi xong:
```
DNA learnings saved: X items → ~/drafts/writing-dna-learnings.md

Next steps (optional):
  merge dna       ← gộp learnings vào DNA khi đủ nhiều bài
  content audit ~/drafts/<slug>-draft.md
```

---

## Merge DNA Command

Trigger khi user nói: `merge dna`, `merge writing dna`, `gộp dna`

### Step 1: Load learnings log

Đọc `~/drafts/writing-dna-learnings.md`.
Nếu file không tồn tại hoặc rỗng:
```
No learnings to merge. Viết thêm bài để tích lũy learnings.
```
Dừng.

### Step 2: Load current DNA

Đọc DNA file tại `~/.seo-voices/` (file `.md` đầu tiên tìm thấy).

### Step 3: Dedup và tổng hợp

So sánh từng learning với DNA hiện tại:
- Nếu trùng nội dung hoặc đã có tương đương → bỏ qua
- Nếu mâu thuẫn với rule hiện tại → flag riêng, hỏi user

### Step 4: Present full diff

Hiển thị diff DNA trước/sau — toàn bộ những gì sẽ thay đổi:

```
DNA Merge Preview (vX.Y → vX.Y+1)
[date]

Changes:
+ [dòng mới]
+ [dòng mới]
~ [dòng sửa] (cũ: "...")

Conflicts (cần quyết định):
! [conflict #1]: learning "[...]" mâu thuẫn với hard stop "[...]"
  Giữ hard stop / Cập nhật hard stop / Bỏ learning? (1/2/3)

Merge vào DNA? (y/n)
```

Giải quyết conflicts trước khi hỏi merge tổng thể.

### Step 5: Update DNA

Nếu user approve:

1. Cập nhật `~/.seo-voices/<name>.md` với các changes đã duyệt
2. Bump version trong frontmatter/footer: `vX.Y → vX.Y+1`
3. Cập nhật dòng `Cập nhật:` ở cuối file với ngày hiện tại và tóm tắt
4. Archive learnings log: create `~/drafts/writing-dna-learnings-archive/` if it does not exist,
   then copy `~/drafts/writing-dna-learnings.md`
   → `~/drafts/writing-dna-learnings-archive/[YYYY-MM-DD].md`
5. Xóa nội dung `~/drafts/writing-dna-learnings.md` (giữ file, clear content)

Output:
```
DNA updated to vX.Y+1 — [N] changes merged.
Learnings archived: ~/drafts/writing-dna-learnings-archive/[date].md
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
- `merge dna`
- `merge writing dna`
- `gộp dna`
