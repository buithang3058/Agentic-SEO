#!/usr/bin/env python3
"""
GEO Benchmark — measure AI citation rate (GEO Score) for a URL.

GEO Score = (questions cited by >= 1 AI engine) / total questions * 100

Engines: Perplexity sonar (required) + OpenAI gpt-4o-search-preview (optional)
Citations are RAG-based: AI engines retrieve live web results and cite sources.
This is NOT a measure of training data coverage.

Usage:
    python geo_benchmark.py https://example.com
    python geo_benchmark.py https://example.com --n 20
    python geo_benchmark.py https://example.com --questions questions.txt
    python geo_benchmark.py https://example.com --generate-with-llm
    python geo_benchmark.py https://example.com --json
    python geo_benchmark.py https://example.com --output geo-report.json

Prerequisites:
    PERPLEXITY_API_KEY  — Perplexity sonar engine (get at https://www.perplexity.ai/settings/api)
    OPENAI_API_KEY      — OpenAI gpt-4o-search-preview engine (get at https://platform.openai.com/api-keys)
    At least one key is required. Both enables dual-engine mode.

Install dependencies:
    pip install requests beautifulsoup4
"""

import argparse
import glob
import json
import math
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("Error: requests required. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: beautifulsoup4 required. Run: pip install beautifulsoup4", file=sys.stderr)
    sys.exit(1)


# Headings that produce useless questions
HEADING_FILLER_BLOCKLIST = {
    "introduction", "faq", "overview", "conclusion", "summary",
    "contact", "about", "references", "resources", "table of contents",
    "toc", "contents", "navigation", "menu",
}

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
OPENAI_API_URL = "https://api.openai.com/v1/responses"


# ---------------------------------------------------------------------------
# Citation parsers
# ---------------------------------------------------------------------------

def parse_perplexity_citation(response: dict, domain: str) -> bool:
    """
    Check if domain appears in Perplexity's citations array.

    Perplexity sonar returns citations as a top-level list of URL strings:
        response['citations'] = ["https://example.com/...", ...]

    NOT inline in response text. Substring match, case-insensitive.
    """
    citations = response.get("citations", [])
    domain_lower = domain.lower()
    return any(domain_lower in url.lower() for url in citations)


def parse_openai_citation(response: dict, domain: str) -> bool:
    """
    Check if domain appears in OpenAI Responses API annotations.

    OpenAI web search (gpt-4o-search-preview) returns citations in:
        response['output'][i]['content'][j]['annotations'][k]['url']

    NOT inline in text. Substring match, case-insensitive.
    """
    domain_lower = domain.lower()
    for output_item in response.get("output", []):
        for content_item in output_item.get("content", []):
            for annotation in content_item.get("annotations", []):
                url = annotation.get("url", "")
                if domain_lower in url.lower():
                    return True
    return False


# ---------------------------------------------------------------------------
# Score formula
# ---------------------------------------------------------------------------

def compute_score(results: list) -> dict:
    """
    Compute GEO Score from a list of result dicts with 'cited' bool.

    Returns:
        {
            "score": float,           # 0-100
            "n": int,                 # number of questions
            "margin_of_error": float, # 95% CI half-width (percentage points)
        }
    """
    n = len(results)
    if n == 0:
        raise ValueError("No results to score")

    cited_count = sum(1 for r in results if r.get("cited", False))
    p = cited_count / n
    score = round(p * 100, 2)

    # 95% confidence interval — normal approximation: MOE = 1.96 * sqrt(p*(1-p)/n) * 100
    # At p=0 or p=1, MOE=0 (exact). For small N this is approximate.
    if n > 1:
        moe = 1.96 * math.sqrt(p * (1 - p) / n) * 100
    else:
        moe = 0.0

    return {
        "score": score,
        "n": n,
        "margin_of_error": round(moe, 2),
    }


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def query_engine_with_retry(api_fn, query: str, delay: float = 1.0):
    """
    Call api_fn(query). Retry once on any exception. Return None if both fail.

    Args:
        api_fn: callable that takes a query string and returns a response dict
        query:  the question to pass to the engine
        delay:  seconds to wait before retry

    Returns:
        Response dict on success, None if both attempts fail.
    """
    for attempt in range(2):
        try:
            return api_fn(query)
        except Exception as e:
            if attempt == 0:
                time.sleep(delay)
            else:
                print(f"Warning: API call failed after retry: {e}", file=sys.stderr)
                return None
    return None


def check_data_sufficiency(total_questions: int, skipped: int) -> dict:
    """
    Check if enough questions answered to produce a reliable score.

    Returns reliable=False with message if > 50% of questions were skipped.
    """
    if total_questions == 0:
        return {"reliable": False, "message": "Insufficient data, score unreliable: no questions provided"}

    skip_rate = skipped / total_questions
    if skip_rate > 0.5:
        return {
            "reliable": False,
            "message": f"Insufficient data, score unreliable: {skipped}/{total_questions} questions skipped",
        }
    return {"reliable": True, "message": ""}


# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------

def extract_domain(url: str) -> str:
    """Extract domain (and optional path) for citation matching."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower().lstrip("www.")
    # For GitHub repos, include path so github.com/owner/repo is specific
    if "github.com" in domain and parsed.path.strip("/"):
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 2:
            return f"github.com/{parts[0]}/{parts[1]}"
    return domain


def fetch_headings(url: str, timeout: int = 15) -> list:
    """Fetch page and extract H1/H2/H3 headings."""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; SEOAgentic/1.0; +https://github.com/buithang/seo-agentic)"},
            timeout=timeout,
        )
        resp.raise_for_status()
    except Exception as e:
        print(f"Warning: could not fetch {url}: {e}", file=sys.stderr)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    headings = []
    for tag in soup.find_all(["h1", "h2", "h3"]):
        text = tag.get_text(separator=" ").strip()
        if text:
            headings.append((tag.name, text))
    return headings


def headings_to_questions(headings: list) -> list:
    """
    Convert headings to natural-language questions.

    Rules:
      H1/H2 → "How to [text]?"
      H3     → "What is [text]?"
      Filler headings (Introduction, FAQ, etc.) are skipped.

    This is approximate. For higher-quality questions, use --questions or
    --generate-with-llm.
    """
    questions = []
    for tag, text in headings:
        normalized = text.lower().strip("?. ")
        if normalized in HEADING_FILLER_BLOCKLIST:
            continue
        if tag in ("h1", "h2"):
            questions.append(f"How to {text.rstrip('?.')}?")
        else:
            questions.append(f"What is {text.rstrip('?.')}?")
    return questions


def fetch_page_text(url: str, max_chars: int = 3000, timeout: int = 15) -> str:
    """
    Fetch a page and return visible text (scripts/styles stripped), truncated to max_chars.
    Returns empty string on failure — caller decides whether to proceed without content.
    """
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; SEOAgentic/1.0; +https://github.com/buithang/seo-agentic)"},
            timeout=timeout,
        )
        resp.raise_for_status()
    except Exception:
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "head"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    # Collapse whitespace
    text = " ".join(text.split())
    return text[:max_chars]


def generate_questions_with_llm(url: str, openai_key: str, n: int) -> list:
    """
    Generate benchmark questions using OpenAI Chat Completions (not web search).
    Only called when --generate-with-llm is passed AND openai_key is available.
    Uses a separate model call, NOT the benchmarking engine, to avoid bias.
    Fetches page content first so the LLM generates topic-specific questions.
    """
    page_text = fetch_page_text(url)
    if page_text:
        user_content = (
            f"Website URL: {url}\n\n"
            f"Page content (first 3000 chars):\n{page_text}\n\n"
            f"Generate {n} search queries."
        )
    else:
        user_content = f"Website URL: {url}\n\nGenerate {n} search queries."

    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You generate search engine queries a user might type to find "
                            "information related to a website. Output ONLY a JSON array of "
                            f"strings, no explanation. Generate exactly {n} queries."
                        ),
                    },
                    {
                        "role": "user",
                        "content": user_content,
                    },
                ],
                "temperature": 0.7,
            },
            timeout=30,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()
        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0]
        return json.loads(content)
    except Exception as e:
        print(f"Warning: LLM question generation failed: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------------------------
# Engine API callers
# ---------------------------------------------------------------------------

def call_perplexity(query: str, api_key: str) -> dict:
    resp = requests.post(
        PERPLEXITY_API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "sonar",
            "messages": [{"role": "user", "content": query}],
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def call_openai_search(query: str, api_key: str) -> dict:
    resp = requests.post(
        OPENAI_API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "gpt-4o-search-preview",
            "input": query,
            "tools": [{"type": "web_search_preview"}],
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Core benchmark runner
# ---------------------------------------------------------------------------

def run_benchmark(
    questions: list,
    domain: str,
    perplexity_key: str,
    openai_key: Optional[str],
    max_workers: int = 5,
) -> dict:
    """
    Query all engines for each question in parallel.
    Returns raw results list with per-question citation status.
    """
    engines = []
    if perplexity_key:
        engines.append(("perplexity", lambda q: call_perplexity(q, perplexity_key)))
    if openai_key:
        engines.append(("openai", lambda q: call_openai_search(q, openai_key)))

    parsers = {
        "perplexity": parse_perplexity_citation,
        "openai": parse_openai_citation,
    }

    def query_question(question: str) -> dict:
        engines_citing = []
        failed_engines = 0

        for engine_name, api_fn in engines:
            response = query_engine_with_retry(lambda q, fn=api_fn: fn(q), question)
            if response is None:
                failed_engines += 1
                continue
            if parsers[engine_name](response, domain):
                engines_citing.append(engine_name)

        # Skipped = ALL engines failed for this question
        skipped = failed_engines == len(engines)
        cited = len(engines_citing) > 0

        return {
            "query": question,
            "cited": cited,
            "engines_citing": engines_citing,
            "skipped": skipped,
        }

    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_q = {executor.submit(query_question, q): q for q in questions}
        for future in as_completed(future_to_q):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                q = future_to_q[future]
                print(f"Warning: question failed entirely: {q!r}: {e}", file=sys.stderr)
                results.append({"query": q, "cited": False, "engines_citing": [], "skipped": True})

    skipped_count = sum(1 for r in results if r.get("skipped"))

    # Sort to preserve question order for reproducible output
    question_order = {q: i for i, q in enumerate(questions)}
    results.sort(key=lambda r: question_order.get(r["query"], 999))

    return {
        "results": results,
        "skipped_count": skipped_count,
        "engine_pair": "+".join(name for name, _ in engines),
    }


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_text_report(domain: str, score_data: dict, benchmark: dict, sufficiency: dict) -> str:
    lines = ["", "## AI Visibility Score", ""]

    if not sufficiency["reliable"]:
        lines.append(f"WARNING: {sufficiency['message']}")
        lines.append("")

    lines.append(
        f"GEO Score: {score_data['score']:.0f}/100 "
        f"(±{score_data['margin_of_error']:.0f}% margin of error, N={score_data['n']})"
    )
    lines.append(f"Engines: {benchmark['engine_pair']}")
    lines.append("Note: Measures RAG-based citation rate, not training data coverage.")
    lines.append("")

    cited = [r for r in benchmark["results"] if r.get("cited")]
    not_cited = [r for r in benchmark["results"] if not r.get("cited") and not r.get("skipped")]
    skipped = [r for r in benchmark["results"] if r.get("skipped")]

    # Per-engine breakdown (only shown in dual-engine mode)
    active_engines = benchmark["engine_pair"].split("+")
    if len(active_engines) >= 2:
        n = score_data["n"]
        results = benchmark["results"]
        a = sum(1 for r in results if "perplexity" in r.get("engines_citing", []))
        b = sum(1 for r in results if "openai" in r.get("engines_citing", []))
        c = sum(1 for r in results if "perplexity" in r.get("engines_citing", []) and "openai" in r.get("engines_citing", []))
        d = a + b - c  # union = GEO Score numerator
        lines.append("Per-engine breakdown:")
        lines.append(f"  Perplexity (sonar):      {a/n*100:.0f}% ({a}/{n})")
        lines.append(f"  OpenAI (gpt-4o-search):  {b/n*100:.0f}% ({b}/{n})")
        lines.append(f"  Both engines cited:      {c/n*100:.0f}% ({c}/{n})")
        lines.append(f"  Either engine (GEO):     {d/n*100:.0f}% ({d}/{n})")
        lines.append("")

    if cited:
        lines.append(f"Cited ({len(cited)}/{score_data['n']}):")
        for r in cited:
            engines = ", ".join(r["engines_citing"])
            lines.append(f'  + "{r["query"]}" — {engines}')
        lines.append("")

    if not_cited:
        lines.append(f"Not cited ({len(not_cited)}/{score_data['n']}):")
        for r in not_cited:
            lines.append(f'  - "{r["query"]}"')
        lines.append("")

    if skipped:
        lines.append(f"Skipped (API errors) ({len(skipped)}):")
        for r in skipped:
            lines.append(f'  ? "{r["query"]}"')
        lines.append("")

    lines.append("Recommendations:")
    if score_data["score"] < 20:
        lines.append("  - Add an llms.txt file to help AI engines understand site structure")
        lines.append("  - Add FAQ sections targeting exact-match questions about your domain")
        lines.append("  - Ensure site is not blocking AI crawlers (GPTBot, PerplexityBot, ClaudeBot)")
    elif score_data["score"] < 50:
        lines.append("  - Expand content on topics where citation rate is low")
        lines.append("  - Add structured data (Article, HowTo, FAQ) to increase retrieval confidence")
    else:
        lines.append("  - Strong citation rate — maintain content freshness and internal linking")

    # llms.txt content gap hints — shown when any questions were not cited
    not_cited_questions = [r["query"] for r in benchmark["results"] if not r.get("cited") and not r.get("skipped")]
    if not_cited_questions:
        lines.append("")
        lines.append("## llms.txt Content Gap Hints")
        lines.append("")
        lines.append("Based on uncited queries, consider adding these topic pointers to /llms.txt:")
        lines.append("")
        for q in not_cited_questions[:5]:
            topic = q.rstrip("?")
            lines.append(f'  "{q}" -> add a pointer to your {topic} page in /llms.txt')
        if len(not_cited_questions) > 5:
            lines.append(f"  (showing 5 of {len(not_cited_questions)} — run with --n 30 for broader coverage)")
        lines.append("")
        lines.append("See https://llmstxt.org for llms.txt format.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Competitor comparison table
# ---------------------------------------------------------------------------

def _format_comparison_table(primary_domain: str, primary_score: dict, competitor_rows: list) -> str:
    """
    Render a GEO Score comparison table.

    primary_score: dict with score, n, margin_of_error
    competitor_rows: list of {domain, score, n, margin_of_error}
    """
    all_rows = [
        {"domain": f"{primary_domain} (you)", "score": primary_score["score"],
         "n": primary_score["n"], "moe": primary_score["margin_of_error"]},
        *[{"domain": r["domain"], "score": r["score"], "n": r["n"], "moe": r["margin_of_error"]}
          for r in competitor_rows],
    ]

    # Column widths
    max_domain = max(len(r["domain"]) for r in all_rows)
    col_domain = max(max_domain, 6)  # min width for "Domain"

    lines = ["", "## GEO Score Comparison", ""]
    header = f"  {'Domain':<{col_domain}}  {'Score':>7}  {'MOE':>5}  {'N':>4}"
    lines.append(header)
    lines.append("  " + "-" * (col_domain + 22))

    all_rows_sorted = sorted(all_rows, key=lambda r: r["score"], reverse=True)
    for row in all_rows_sorted:
        lines.append(
            f"  {row['domain']:<{col_domain}}  {row['score']:>5.0f}/100  ±{row['moe']:>3.0f}%  {row['n']:>4}"
        )

    # Gap vs top competitor
    comp_scores = [r["score"] for r in competitor_rows]
    if comp_scores:
        best_comp = max(competitor_rows, key=lambda r: r["score"])
        gap = primary_score["score"] - best_comp["score"]
        lines.append("")
        if gap > 0:
            lines.append(f"  Gap vs top competitor: +{gap:.0f} points ahead of {best_comp['domain']}")
        elif gap < 0:
            lines.append(f"  Gap vs top competitor: {gap:.0f} points behind {best_comp['domain']}")
        else:
            lines.append(f"  Tied with top competitor: {best_comp['domain']}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Measure AI citation rate (GEO Score) for a URL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("url", help="URL to benchmark")
    parser.add_argument("--questions", "-q", metavar="FILE",
                        help="File with one question per line (UTF-8, blank lines ignored)")
    parser.add_argument("--n", type=int, default=20,
                        help="Number of questions to use (default: 20, minimum recommended: 20)")
    parser.add_argument("--generate-with-llm", action="store_true",
                        help="Generate questions using OpenAI instead of heading parse")
    parser.add_argument("--json", action="store_true", dest="output_json",
                        help="Output JSON to stdout")
    parser.add_argument("--output", "-o", metavar="FILE",
                        help="Save JSON output to file")
    parser.add_argument("--workers", type=int, default=5,
                        help="Parallel API workers (default: 5)")
    parser.add_argument("--save", action="store_true",
                        help="Save results to ~/.seo-geo-history/ and show delta from previous run (primary domain only, not competitors)")
    parser.add_argument("--competitors", metavar="DOMAINS",
                        help="Comma-separated competitor domains to compare (e.g., competitor1.com,competitor2.com)")

    args = parser.parse_args()

    # API keys
    perplexity_key = os.environ.get("PERPLEXITY_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")

    if not perplexity_key and not openai_key:
        print(
            "Error: No API key found.\n"
            "Set PERPLEXITY_API_KEY and/or OPENAI_API_KEY.\n"
            "  PERPLEXITY_API_KEY: https://www.perplexity.ai/settings/api\n"
            "  OPENAI_API_KEY: https://platform.openai.com/api-keys",
            file=sys.stderr,
        )
        sys.exit(1)

    if not perplexity_key:
        print("Note: PERPLEXITY_API_KEY not set — running OpenAI-only mode", file=sys.stderr)
    if not openai_key:
        print("Note: OPENAI_API_KEY not set — running Perplexity-only mode", file=sys.stderr)

    # N warning
    if args.n < 20:
        print(f"Warning: N={args.n} is below recommended minimum of 20 (±22% CI). Score will have wider uncertainty.", file=sys.stderr)

    # URL scheme normalization — must happen before fetch_headings and extract_domain
    if not args.url.startswith(("http://", "https://")):
        args.url = "https://" + args.url

    # Question sourcing
    questions = []

    if args.questions:
        try:
            with open(args.questions, encoding="utf-8") as f:
                questions = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"Error: questions file not found: {args.questions}", file=sys.stderr)
            sys.exit(1)
        print(f"Loaded {len(questions)} questions from {args.questions}", file=sys.stderr)

    elif args.generate_with_llm:
        if not openai_key:
            print("Warning: --generate-with-llm requires OPENAI_API_KEY. Falling back to heading parse.", file=sys.stderr)
        else:
            print(f"Generating {args.n} questions via LLM...", file=sys.stderr)
            questions = generate_questions_with_llm(args.url, openai_key, args.n)
            if not questions:
                print("LLM generation failed. Falling back to heading parse.", file=sys.stderr)

    if not questions:
        print(f"Extracting headings from {args.url}...", file=sys.stderr)
        headings = fetch_headings(args.url)
        questions = headings_to_questions(headings)
        if not questions:
            print(
                "Error: could not extract any questions from headings.\n"
                "Provide questions manually with --questions questions.txt",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"Generated {len(questions)} questions from headings", file=sys.stderr)

    # Cap at --n
    if len(questions) > args.n:
        questions = questions[: args.n]
    elif len(questions) < args.n:
        print(f"Warning: only {len(questions)} questions available (requested {args.n})", file=sys.stderr)

    domain = extract_domain(args.url)
    print(f"Benchmarking domain: {domain}", file=sys.stderr)
    engine_count = bool(perplexity_key) + bool(openai_key)
    print(f"Running {len(questions)} questions against {engine_count} engine(s)...", file=sys.stderr)

    # Run benchmark
    benchmark = run_benchmark(
        questions=questions,
        domain=domain,
        perplexity_key=perplexity_key,
        openai_key=openai_key or None,
        max_workers=args.workers,
    )

    # Score
    answered = [r for r in benchmark["results"] if not r.get("skipped")]
    if not answered:
        print("Error: all questions were skipped due to API errors.", file=sys.stderr)
        sys.exit(1)

    score_data = compute_score(answered)
    sufficiency = check_data_sufficiency(len(questions), benchmark["skipped_count"])

    # Per-engine stats for JSON output
    n = score_data["n"]
    results = benchmark["results"]
    per_engine = {}
    for engine_name in benchmark["engine_pair"].split("+"):
        per_engine[engine_name] = {
            "cited": sum(1 for r in results if engine_name in r.get("engines_citing", [])),
            "total": n,
        }

    # Build output
    output = {
        "url": args.url,
        "domain": domain,
        "score": score_data["score"],
        "n": score_data["n"],
        "margin_of_error": score_data["margin_of_error"],
        "engine_pair": benchmark["engine_pair"],
        "per_engine": per_engine,
        "reliable": sufficiency["reliable"],
        "results": benchmark["results"],
    }

    if not sufficiency["reliable"]:
        output["warning"] = sufficiency["message"]

    # Competitor benchmarks (same questions, different domain)
    competitor_rows = []  # [{domain, score, margin_of_error, n}]
    if args.competitors:
        raw_competitors = [c.strip() for c in args.competitors.split(",") if c.strip()]
        for raw in raw_competitors:
            comp_url = raw if raw.startswith(("http://", "https://")) else "https://" + raw
            comp_domain = extract_domain(comp_url)
            if not comp_domain:
                print(f"Warning: skipping malformed competitor domain: {raw!r}", file=sys.stderr)
                continue
            print(f"Benchmarking competitor: {comp_domain}", file=sys.stderr)
            comp_benchmark = run_benchmark(
                questions=questions,
                domain=comp_domain,
                perplexity_key=perplexity_key,
                openai_key=openai_key or None,
                max_workers=args.workers,
            )
            comp_answered = [r for r in comp_benchmark["results"] if not r.get("skipped")]
            if comp_answered:
                comp_score = compute_score(comp_answered)
            else:
                comp_score = {"score": 0.0, "n": 0, "margin_of_error": 0.0}
            competitor_rows.append({
                "domain": comp_domain,
                "score": comp_score["score"],
                "n": comp_score["n"],
                "margin_of_error": comp_score["margin_of_error"],
            })
        output["domains"] = [
            {"domain": domain, "score": score_data["score"], "n": score_data["n"],
             "margin_of_error": score_data["margin_of_error"], "primary": True},
            *[{**row, "primary": False} for row in competitor_rows],
        ]

    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"Saved to {args.output}", file=sys.stderr)

    # Historical save + delta
    delta_lines = []
    if args.save:
        history_dir = os.path.expanduser("~/.seo-geo-history/")
        domain_slug = domain.replace("/", "-")
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
        save_path = os.path.join(history_dir, f"{domain_slug}-{timestamp}.json")
        save_payload = dict(output)
        save_payload["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        try:
            os.makedirs(history_dir, exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(save_payload, f, indent=2, ensure_ascii=False)
            print(f"Saved to {save_path}", file=sys.stderr)
            # Find previous run (newest file excluding just-written)
            pattern = os.path.join(history_dir, f"{domain_slug}-*.json")
            history_files = sorted(glob.glob(pattern))
            previous_files = [p for p in history_files if p != save_path]
            if previous_files:
                with open(previous_files[-1], encoding="utf-8") as f:
                    previous = json.load(f)
                prev_score = previous.get("score", 0)
                curr_score = score_data["score"]
                delta = curr_score - prev_score
                prev_date = previous.get("timestamp", previous_files[-1])[:10]
                delta_sign = "+" if delta >= 0 else ""
                delta_lines.append("")
                delta_lines.append(f"Previous run: {prev_date} -> Score: {prev_score:.0f}/100")
                delta_lines.append(f"This run: {timestamp[:10]} -> Score: {curr_score:.0f}/100 ({delta_sign}{delta:.0f} points)")
                if abs(delta) < score_data["margin_of_error"]:
                    delta_lines.append(f"Note: delta ({delta_sign}{delta:.0f}) is within margin of error (±{score_data['margin_of_error']:.0f}) — not statistically significant")
                prev_engine_pair = previous.get("engine_pair", "")
                curr_engine_pair = benchmark["engine_pair"]
                if prev_engine_pair and prev_engine_pair != curr_engine_pair:
                    delta_lines.append(f"Note: engine_pair changed ({prev_engine_pair} -> {curr_engine_pair}) — delta may reflect engine change, not citation improvement")
        except Exception as e:
            print(f"Warning: could not save history: {e}", file=sys.stderr)

    if args.output_json or args.output:
        if not args.output:
            print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        report = format_text_report(domain, score_data, benchmark, sufficiency)
        if competitor_rows:
            report += _format_comparison_table(domain, score_data, competitor_rows)
        if delta_lines:
            report += "\n" + "\n".join(delta_lines)
        print(report)


if __name__ == "__main__":
    main()
