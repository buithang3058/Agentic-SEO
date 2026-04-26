
## SEO Agentic commands

These commands are handled by reading skill files directly — do NOT use the Skill tool for them.
When `/seo` is loaded, display the full menu from SKILL.md's "On Load" section before doing anything else.

| User types | Read this file and follow its instructions |
|-----------|-------------------------------------------|
| `project list` / `project switch` / `project new` / `project status` | `resources/skills/seo-project.md` |
| `content write <topic>` | `resources/skills/content-writer.md` |
| `content audit <url>` | `resources/skills/content-audit.md` |
| `marketing interview` | `resources/skills/marketing-interviewer.md` |
| `content calendar` / `30-day calendar` | `resources/skills/content-calendar.md` |
| `seo audit <url>` | `resources/skills/seo-audit.md` |
| `seo page <url>` | `resources/skills/seo-page.md` |
| `seo plan <url>` | `resources/skills/seo-plan.md` |
| `seo geo <url>` | `resources/skills/seo-geo.md` |
| `seo aeo <url>` | `resources/skills/seo-aeo.md` |
| `seo links <url>` | `resources/skills/seo-links.md` |
| `seo hreflang <url>` | `resources/skills/seo-hreflang.md` |
| `seo competitors <url>` | `resources/skills/seo-competitor-pages.md` |
| `seo programmatic <url>` | `resources/skills/seo-programmatic.md` |
| `seo article <url>` | `resources/skills/seo-article.md` |
| Any other `seo <sub-skill> <url>` | `resources/skills/seo-<sub-skill>.md` |

If unsure which file to read, check the full commands table in `SKILL.md`.

## Skill routing (gstack — developer tools only)

When the user's request matches a gstack developer skill, invoke it using the Skill
tool as your FIRST action.

Key routing rules:
- Product ideas, "is this worth building", brainstorming → invoke office-hours
- Bugs, errors, "why is this broken", 500 errors → invoke investigate
- Ship, deploy, push, create PR → invoke ship
- QA, test the site, find bugs → invoke qa
- Code review, check my diff → invoke review
- Update docs after shipping → invoke document-release
- Weekly retro → invoke retro
- Design system, brand → invoke design-consultation
- Visual audit, design polish → invoke design-review
- Architecture review → invoke plan-eng-review
- Save progress, checkpoint, resume → invoke checkpoint
- Code quality, health check → invoke health

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
|------|----------|
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.

## Writing Voice — diverFi

**Voice:** cá nhân, thẳng, logic, câu ngắn, thừa nhận thất bại, có gai nhẹ
**Tagline VI:** "DeFi không hype. Không shill." | **EN:** "DeFi explained honestly."
**Measure:** Người đọc có WOW không, và nếu đọc ở trang khác họ có nhận ra đây là diverFi không?

### Hard stops
1. **Không mở bài bằng định nghĩa** — họ cần góc nhìn, không cần từ điển
2. **Không "bạn cần phải…", "chìa khóa là…"** — dạy đời không có stake là rỗng
3. **Không khen mà không có rủi ro** — nếu không dám nói cái xấu, cái tốt vô nghĩa
4. **Claim level rõ ràng:** "tôi" (trải nghiệm thật) / "theo quan sát" / "tôi chưa chắc nhưng"
5. **Weight test:** mỗi đoạn phải có stake — ai bị ảnh hưởng? Không trả lời được → viết lại

### Never
- Khuyên mua/bán/đầu tư bất kỳ tài sản
- Claim x10, x100 không có cơ sở; shill một chiều không có risk disclosure
- Bold liên tục (max 1 bold/400 từ, tối đa 7 bold/bài 3000 từ)
- Header/sub-header quá nhiều (tín hiệu chưa hiểu đủ để gộp ý)
- Giả vờ biết nhiều hơn thực sự biết; viết ngoài tài chính/blockchain

### Pattern selection

| Tiêu đề bài | Pattern | Hook |
|---|---|---|
| "[Topic] là gì?" / "Tại sao X quan trọng" | B — Opportunity-first | Vấn đề ẩn reader chưa nhận ra |
| "Tôi đã thử/mất tiền với X" / "Lỗi phổ biến" | A — Trust-first | Sai lầm cụ thể của tác giả |
| "Cách làm X" / "Hướng dẫn X" | C — Problem-solution | Frustration reader đang có |

**Pattern B:** personal loss KHÔNG phải hook. Dùng làm credibility signal trong phần rủi ro.

### Writing mechanics
- Độ dài: <1000 từ tự nhiên | 2000–3500 từ SEO article
- Hứa hẹn cụ thể trong 200–300 từ đầu
- Tiêu đề: keyword + số (nếu phù hợp) + hứa hẹn cụ thể
- Kết bài: "Tóm lại là…" + lập trường rõ ràng (không "tuỳ trường hợp")
- Câu ngắn trong đoạn personal voice

### Context freshness
- `writing-dna.md` last updated: 2026-04-15. Nếu >7 ngày từ hôm nay → warn user trước khi viết.
- `marketing-context.md` (diverFi): **DEFERRED** — không đọc, không prompt. Resume 2026-06-20.
