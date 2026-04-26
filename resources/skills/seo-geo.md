---
name: seo-geo
description: >
  Optimize content for AI Overviews (formerly SGE), ChatGPT web search,
  Perplexity, and other AI-powered search experiences. Generative Engine
  Optimization (GEO) analysis including brand mention signals, AI crawler
  accessibility, llms.txt compliance, passage-level citability scoring, and
  platform-specific optimization. Use when user says "AI Overviews", "SGE",
  "GEO", "AI search", "LLM optimization", "Perplexity", "AI citations",
  "ChatGPT search", or "AI visibility".
---

# AI Search / GEO Optimization (February 2026)

## Key Statistics

| Metric | Value |
|--------|-------|
| AI Overviews reach | 1.5B users/month, 200+ countries |
| AI Overviews query coverage | 50%+ of all queries |
| AI-referred sessions growth | 527% Jan–May 2025 (SparkToro) |
| ChatGPT weekly active users | 900M (OpenAI) |
| Perplexity monthly queries | 500M+ |

**Brand mentions correlate 3× more strongly with AI visibility than backlinks.**
(Ahrefs Dec 2025, 75K brands) — YouTube (0.737) > Reddit > Wikipedia > LinkedIn > Domain Rating (0.266)

**Only 11% of domains** cited by both ChatGPT and Google AIO for the same query — platform-specific optimization required.

---

## GEO Analysis Criteria

### 1. Citability Score (25%)
Optimal passage length: **134–167 words**. Strong signals: quotable sentences with specific facts, self-contained answer blocks, direct answer in first 40–60 words, claims with sources, "X is..." definition patterns, unique data. Weak: vague statements, opinion without evidence, buried conclusions.

### 2. Structural Readability (20%)
92% of AIO citations from top-10 pages, but 47% from below position 5. Strong: clean H1→H2→H3, question-based headings, short paragraphs (2–4 sentences), tables, lists, FAQ sections. Weak: walls of text, inconsistent hierarchy.

### 3. Multi-Modal Content (15%)
Content with multi-modal elements sees 156% higher selection rates. Check: images, video, infographics, interactive elements, structured data supporting media.

### 4. Authority & Brand Signals (20%)
Strong: author byline + credentials, publication/update dates, primary source citations, Wikipedia/Wikidata entity presence, Reddit/YouTube/LinkedIn mentions. Weak: anonymous authorship, no dates, no sources.

### 5. Technical Accessibility (20%)
**AI crawlers do NOT execute JavaScript** — SSR is critical. Check: SSR vs client-only content, AI crawler access in robots.txt, llms.txt presence, RSL 1.0 licensing.

---

## AI Crawler Detection

Check `robots.txt`:

| Crawler | Owner |
|---------|-------|
| GPTBot, OAI-SearchBot, ChatGPT-User | OpenAI |
| ClaudeBot, anthropic-ai | Anthropic |
| PerplexityBot | Perplexity |
| CCBot | Common Crawl (often blocked) |
| Bytespider | ByteDance |
| cohere-ai | Cohere |

Allow GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot. Block CCBot/training crawlers if desired.

---

## llms.txt Standard

`/llms.txt` — structured content guidance for AI crawlers. Format: `# Title`, `> description`, sections with `- [Page](url): Description`. Check: presence, structured guidance, key page highlights, contact/authority info.

---

## RSL 1.0

Machine-readable AI licensing (Dec 2025). Backed by Reddit, Yahoo, Medium, Quora, Cloudflare, Akamai, Creative Commons. Check RSL implementation and licensing terms.

---

## Platform-Specific Optimization

| Platform | Key Citation Sources | Focus |
|----------|---------------------|-------|
| Google AI Overviews | Top-10 pages (92%) | Traditional SEO + passage optimization |
| ChatGPT | Wikipedia (47.9%), Reddit (11.3%) | Entity presence, authoritative sources |
| Perplexity | Reddit (46.7%), Wikipedia | Community validation |
| Bing Copilot | Bing index | Bing SEO, IndexNow |

---

## Measured GEO Score

```bash
python3 <SKILL_DIR>/scripts/geo_benchmark.py <url> --n 20
```

Keys: `PERPLEXITY_API_KEY` and/or `OPENAI_API_KEY`. Embed `## AI Visibility Score` section into `GEO-ANALYSIS.md`.

---

## Output

Generate `GEO-ANALYSIS.md` with:
1. GEO Readiness Score: XX/100
2. Platform breakdown (Google AIO, ChatGPT, Perplexity scores)
3. AI Crawler Access Status
4. llms.txt Status + recommendations
5. Brand Mention Analysis (Wikipedia, Reddit, YouTube, LinkedIn)
6. Passage-Level Citability (optimal 134–167 word blocks identified)
7. Server-Side Rendering Check
8. Top 5 Highest-Impact Changes
9. Schema Recommendations
10. Content Reformatting Suggestions (specific passages to rewrite)

---

## Passage Indexing Optimization

Rules: self-contained sections per H2, 100–200 words per block, question-phrased H2/H3 with direct answer first sentence, start sections with full subject (not "It"/"This"). Add `speakable` CSS selectors for top answer passages.

---

## Priority Actions

**Quick wins:** "What is [topic]?" definition in first 60 words · 134–167 word answer blocks · question-based headings · statistics with sources · publication dates · Person schema · allow AI crawlers

**Medium effort:** `/llms.txt` · author bio + Wikipedia/LinkedIn links · SSR for key content · Reddit/YouTube entity presence · comparison tables · FAQ sections

**High impact:** original research/surveys · Wikipedia brand presence · YouTube channel · comprehensive entity linking · unique tools/calculators
