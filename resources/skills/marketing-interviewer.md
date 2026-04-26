---
name: marketing-interviewer
description: >
  Marketing context extractor. Conducts a 30-question interview across 6 categories
  to extract brand positioning, audience, channels, messaging, competition, and content
  pillars. Output: marketing-context.md for the active project.
  Use when user says "marketing interview", "interview marketing", or "marketing context".
---

# Marketing Interviewer

Extracts marketing knowledge via structured dialogue. 30 questions, 6 categories.
Output: `~/.seo-projects/<slug>/marketing-context.md`. One question at a time.

---

## Startup

1. Check `~/.seo-projects/active` — if empty, halt: "No active project. Run: project switch <name>"
2. Read slug from `~/.seo-projects/active`
3. Read existing `~/.seo-projects/<slug>/marketing-context.md` if present. Skip pre-filled fields. If exists, rename to `.bak`
4. Read `~/.seo-projects/<slug>/context.md` — extract name, url, competitors
5. Introduce: "Marketing Interview — <name>. 30 questions, 6 areas. One at a time. Type 'save and exit' to stop early."

---

## Interview Rules

1. One question at a time — wait for answer before next
2. Push back on vague answers — re-ask with concrete prompt ("Give me a job title, age, specific Monday morning worry")
3. Skip pre-filled fields — note `[SKIPPED]` in tracking
4. On "save and exit" — save answers so far, fill remaining with `...`, write file

Show running count: **[Q1/30]**, **[Q2/30]**, etc.

---

## Interview Questions

### Category 1: Brand Positioning (Q1–Q6)

**Q1:** "In one sentence, what does <name> do and who is it for?"
**Q2:** "Not the feature — the outcome. If they use <name> for 6 months, what changes?"
**Q3:** "Most people don't change. What pain or desire makes someone actually act?"
**Q4:** "What do you do that the most obvious competitor doesn't — or can't?"
**Q5:** "If someone describes you to a friend in 10 words, what should they say?"
**Q6:** "What positioning would you actively reject? What brand would you never want to be compared to?"

### Category 2: Audience Segments (Q7–Q11)

**Q7:** "Describe the person who gets the most value. Job title, situation, what they were doing before."
**Q8:** "Who comes to you, tries it, and leaves? What's the profile of someone this isn't built for?"
**Q9:** "What do they think is true about their problem before they find you?"
**Q10:** "What risk are they trying to avoid? What would make them hesitate?"
**Q11:** "Six months after using <name>, what does their life look like? Be specific."

### Category 3: Channel Strategy (Q12–Q16)

**Q12:** "Which specific platforms, communities, forums, newsletters, YouTube channels?"
**Q13:** "What's working right now to find you? Search? Word of mouth? Social?"
**Q14:** "Which channel are you not using that you think you should be?"
**Q15:** "What format actually gets engagement? Long reads, short posts, video, threads, email?"
**Q16:** "One message for a billboard — no URL, no features. What do you say?"

### Category 4: Messaging Angles (Q17–Q21)

**Q17:** "When you write with this framing, people engage. What is it?"
**Q18:** "You've tried this angle and it doesn't land. What is it?"
**Q19:** "The thing that makes people's eyes glaze over or requires 5 minutes to explain."
**Q20:** "The first thing you'd say to someone at a coffee meeting — not a pitch."
**Q21:** "The most common reason someone doesn't buy or sign up. What is it?"

### Category 5: Competition (Q22–Q26)

**Q22:** "Name your top 2–3 competitors. URLs if possible."
**Q23:** "Be honest — what do competitors have that you don't?"
**Q24:** "The real reason customers choose you — not the marketing reason."
**Q25:** "Where is conventional wisdom in your space wrong?"
**Q26:** "The honest truth that competitors all dance around."

### Category 6: Content Pillars (Q27–Q30)

**Q27:** "Three topics you could write about forever — deep knowledge, strong opinions."
**Q28:** "Topics to avoid — off-brand, outside expertise, positioning confusion."
**Q29:** "The obvious content gap — question your audience asks most, you haven't answered."
**Q30:** "The piece of content so good it removes the last objection before buying."

---

## Adversarial Self-Review

After all questions: scan for answers with no specific name, number, or example. Select up to 3 weakest. For each: show their answer, label it too vague, push for a specific follow-up. User can revise or say "keep it."

---

## Output

Write `~/.seo-projects/<slug>/marketing-context.md` with frontmatter (`project:`, `updated:`).

Sections: **Brand & Product** (what it is, target audience, value prop, positioning + competitors) · **Core Messages** (main message, angles that work/avoid) · **Content Strategy** (pillar topics, content funnel awareness/consideration/conversion, CTA mapping) · **Channels & Distribution** (SEO, social, newsletter) · **Writing Instructions** (tone from Q9/Q10, brand voice from Q5, key differentiators from Q19/Q21)

Pre-filled fields: keep existing content. Unanswered: write `...`.

After writing: "Marketing context saved. Next: `content calendar` or `content write <topic>`"

---

## Trigger phrases

- `marketing interview` / `interview marketing` / `marketing context`
