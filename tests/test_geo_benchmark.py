"""
Tests for scripts/geo_benchmark.py

Run with: pip install pytest && pytest tests/test_geo_benchmark.py -v

These tests cover the four highest-risk areas identified in the eng review:
1. Citation parsers (Perplexity + OpenAI) — format is version-sensitive
2. Score formula correctness
3. Error handling (retry + skip logic)
4. >50% skip threshold detection

Fixture JSON files in tests/fixtures/ represent real API response shapes.
Update fixtures when API response formats change upstream.
"""

import json
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock

import pytest

# Add scripts/ to path so we can import geo_benchmark
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Helpers — load fixture JSON
# ---------------------------------------------------------------------------

def load_fixture(name: str) -> dict:
    with open(FIXTURES / name) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 1. Perplexity citation parser
# ---------------------------------------------------------------------------

class TestPerplexityCitationParser:
    """
    Perplexity sonar returns citations in response['citations'] — a top-level
    array of URL strings. NOT inline in response text.
    """

    def test_domain_in_citations_array(self):
        from geo_benchmark import parse_perplexity_citation
        response = load_fixture("perplexity_cited.json")
        assert parse_perplexity_citation(response, "example.com") is True

    def test_domain_not_in_citations_array(self):
        from geo_benchmark import parse_perplexity_citation
        response = load_fixture("perplexity_not_cited.json")
        assert parse_perplexity_citation(response, "example.com") is False

    def test_domain_in_text_but_not_in_citations_is_not_cited(self):
        """
        Citation requires presence in citations[] array, not in response text.
        This guards against text-search false positives.
        """
        from geo_benchmark import parse_perplexity_citation
        response = load_fixture("perplexity_not_cited.json")
        # Inject domain into response text without adding to citations
        response["choices"][0]["message"]["content"] += " See also example.com for details."
        assert parse_perplexity_citation(response, "example.com") is False

    def test_case_insensitive_match(self):
        from geo_benchmark import parse_perplexity_citation
        response = load_fixture("perplexity_cited.json")
        assert parse_perplexity_citation(response, "EXAMPLE.COM") is True

    def test_missing_citations_key_returns_false(self):
        """Guard against API response format change where citations key is absent."""
        from geo_benchmark import parse_perplexity_citation
        response = {"choices": [{"message": {"content": "hello"}}]}
        assert parse_perplexity_citation(response, "example.com") is False

    def test_github_repo_url_match(self):
        from geo_benchmark import parse_perplexity_citation
        response = load_fixture("perplexity_cited.json")
        response["citations"].append("https://github.com/buithang/seo-agentic")
        assert parse_perplexity_citation(response, "github.com/buithang/seo-agentic") is True


# ---------------------------------------------------------------------------
# 2. OpenAI citation parser
# ---------------------------------------------------------------------------

class TestOpenAICitationParser:
    """
    OpenAI web search (gpt-4o-search-preview) returns citations in:
    response['output'][i]['content'][j]['annotations']
    Each annotation has a 'url' field. NOT inline in text.
    """

    def test_domain_in_annotations(self):
        from geo_benchmark import parse_openai_citation
        response = load_fixture("openai_cited.json")
        assert parse_openai_citation(response, "example.com") is True

    def test_domain_not_in_annotations(self):
        from geo_benchmark import parse_openai_citation
        response = load_fixture("openai_not_cited.json")
        assert parse_openai_citation(response, "example.com") is False

    def test_domain_in_text_but_not_in_annotations_is_not_cited(self):
        """Same guard as Perplexity: text presence doesn't count."""
        from geo_benchmark import parse_openai_citation
        response = load_fixture("openai_not_cited.json")
        response["output"][0]["content"][0]["text"] += " Check example.com for more."
        assert parse_openai_citation(response, "example.com") is False

    def test_case_insensitive_match(self):
        from geo_benchmark import parse_openai_citation
        response = load_fixture("openai_cited.json")
        assert parse_openai_citation(response, "EXAMPLE.COM") is True

    def test_missing_output_key_returns_false(self):
        from geo_benchmark import parse_openai_citation
        response = {"id": "resp_xyz", "model": "gpt-4o-search-preview"}
        assert parse_openai_citation(response, "example.com") is False

    def test_empty_annotations_returns_false(self):
        from geo_benchmark import parse_openai_citation
        response = load_fixture("openai_not_cited.json")
        response["output"][0]["content"][0]["annotations"] = []
        assert parse_openai_citation(response, "example.com") is False


# ---------------------------------------------------------------------------
# 3. Score formula
# ---------------------------------------------------------------------------

class TestScoreFormula:
    """
    GEO Score = (questions cited by >= 1 engine) / total * 100
    margin_of_error = 1.96 * sqrt(p*(1-p)/n) * 100  [95% CI, binary outcome]
    """

    def test_basic_score_two_of_three(self):
        from geo_benchmark import compute_score
        results = [
            {"cited": True},
            {"cited": False},
            {"cited": True},
        ]
        score = compute_score(results)
        assert abs(score["score"] - 66.67) < 0.01

    def test_all_cited(self):
        from geo_benchmark import compute_score
        results = [{"cited": True}] * 10
        score = compute_score(results)
        assert score["score"] == 100.0

    def test_none_cited(self):
        from geo_benchmark import compute_score
        results = [{"cited": False}] * 10
        score = compute_score(results)
        assert score["score"] == 0.0

    def test_n_is_correct(self):
        from geo_benchmark import compute_score
        results = [{"cited": True}] * 5 + [{"cited": False}] * 15
        score = compute_score(results)
        assert score["n"] == 20

    def test_margin_of_error_at_n20_p05(self):
        """At N=20, p=0.5: MOE = 1.96 * sqrt(0.5*0.5/20) * 100 ≈ 21.91"""
        from geo_benchmark import compute_score
        results = [{"cited": True}] * 10 + [{"cited": False}] * 10
        score = compute_score(results)
        assert abs(score["margin_of_error"] - 21.91) < 0.1

    def test_empty_results_raises(self):
        from geo_benchmark import compute_score
        with pytest.raises((ValueError, ZeroDivisionError)):
            compute_score([])


# ---------------------------------------------------------------------------
# 4. Error handling — retry + skip logic
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """
    On API error: retry once. Skip question if still failing.
    Score is computed on non-skipped questions only.
    """

    def test_retry_fires_once_on_timeout(self):
        """A single question failure triggers exactly one retry."""
        from geo_benchmark import query_engine_with_retry
        call_count = {"n": 0}

        def flaky_api(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] < 2:
                raise TimeoutError("timeout")
            return load_fixture("perplexity_cited.json")

        result = query_engine_with_retry(flaky_api, "test query")
        assert call_count["n"] == 2
        assert result is not None

    def test_question_skipped_after_two_failures(self):
        """If retry also fails, question is skipped (returns None)."""
        from geo_benchmark import query_engine_with_retry

        def always_fails(*args, **kwargs):
            raise TimeoutError("timeout")

        result = query_engine_with_retry(always_fails, "test query")
        assert result is None

    def test_score_computed_on_non_skipped_questions(self):
        """Skipped questions don't count toward N or score numerator."""
        from geo_benchmark import compute_score
        # 2 cited out of 3 non-skipped (1 question was skipped, not included)
        results = [
            {"cited": True},
            {"cited": True},
            {"cited": False},
        ]
        score = compute_score(results)
        assert score["n"] == 3
        assert abs(score["score"] - 66.67) < 0.01


# ---------------------------------------------------------------------------
# 5. >50% skip threshold
# ---------------------------------------------------------------------------

class TestSkipThreshold:
    """
    If more than 50% of questions are skipped, output must signal unreliable data.
    """

    def test_insufficient_data_flag_at_majority_skips(self):
        from geo_benchmark import check_data_sufficiency
        total_questions = 20
        skipped = 11
        result = check_data_sufficiency(total_questions, skipped)
        assert result["reliable"] is False
        assert "Insufficient data" in result["message"]

    def test_sufficient_data_at_minority_skips(self):
        from geo_benchmark import check_data_sufficiency
        result = check_data_sufficiency(20, 9)
        assert result["reliable"] is True

    def test_exactly_fifty_percent_is_sufficient(self):
        """50% skipped is the boundary — not over 50%, so still reliable."""
        from geo_benchmark import check_data_sufficiency
        result = check_data_sufficiency(20, 10)
        assert result["reliable"] is True

    def test_zero_skips_is_sufficient(self):
        from geo_benchmark import check_data_sufficiency
        result = check_data_sufficiency(20, 0)
        assert result["reliable"] is True


# ---------------------------------------------------------------------------
# 6. Skipped-tracking fix — all engines fail → skipped=True
# ---------------------------------------------------------------------------

class TestSkippedTracking:
    """
    query_question() must return skipped=True when ALL engines fail,
    and skipped=False when at least one engine succeeds (even if it didn't cite).
    """

    def test_all_engines_fail_returns_skipped_true(self):
        """When every engine returns None, the question must be marked skipped."""
        from geo_benchmark import run_benchmark
        with patch("geo_benchmark.query_engine_with_retry", return_value=None):
            result = run_benchmark(
                questions=["test question"],
                domain="example.com",
                perplexity_key="fake_key",
                openai_key=None,
            )
        assert result["results"][0]["skipped"] is True
        assert result["skipped_count"] == 1

    def test_one_engine_fails_other_succeeds_not_skipped(self):
        """If one engine fails but the other returns a response, question is not skipped."""
        from geo_benchmark import run_benchmark
        perplexity_response = load_fixture("perplexity_not_cited.json")

        call_count = {"n": 0}

        def mock_retry(api_fn, query, delay=1.0):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return perplexity_response
            return None

        with patch("geo_benchmark.query_engine_with_retry", side_effect=mock_retry):
            result = run_benchmark(
                questions=["test question"],
                domain="example.com",
                perplexity_key="fake_key",
                openai_key="fake_openai_key",
            )
        assert result["results"][0]["skipped"] is False
        assert result["skipped_count"] == 0

    def test_skipped_count_computed_from_results(self):
        """skipped_count must reflect actual skipped results, not just exception path."""
        from geo_benchmark import run_benchmark
        with patch("geo_benchmark.query_engine_with_retry", return_value=None):
            result = run_benchmark(
                questions=["q1", "q2", "q3"],
                domain="example.com",
                perplexity_key="fake_key",
                openai_key=None,
            )
        assert result["skipped_count"] == 3


# ---------------------------------------------------------------------------
# 7. Single-engine mode
# ---------------------------------------------------------------------------

class TestSingleEngineMode:
    """
    Either PERPLEXITY_API_KEY or OPENAI_API_KEY alone must be sufficient.
    Both missing must exit(1).
    """

    def test_perplexity_only_runs(self):
        """run_benchmark with only perplexity_key works, produces results."""
        from geo_benchmark import run_benchmark
        response = load_fixture("perplexity_cited.json")
        with patch("geo_benchmark.query_engine_with_retry", return_value=response):
            result = run_benchmark(
                questions=["what is seo?"],
                domain="example.com",
                perplexity_key="fake_key",
                openai_key=None,
            )
        assert len(result["results"]) == 1
        assert result["engine_pair"] == "perplexity"

    def test_openai_only_runs(self):
        """run_benchmark with only openai_key works, produces results."""
        from geo_benchmark import run_benchmark
        response = load_fixture("openai_cited.json")
        with patch("geo_benchmark.query_engine_with_retry", return_value=response):
            result = run_benchmark(
                questions=["what is seo?"],
                domain="example.com",
                perplexity_key=None,
                openai_key="fake_openai_key",
            )
        assert len(result["results"]) == 1
        assert result["engine_pair"] == "openai"

    def test_no_keys_exits(self, monkeypatch, capsys):
        """If neither key is set, main() must exit with code 1."""
        import geo_benchmark
        monkeypatch.setenv("PERPLEXITY_API_KEY", "")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setattr("sys.argv", ["geo_benchmark.py", "https://example.com"])
        with pytest.raises(SystemExit) as exc_info:
            geo_benchmark.main()
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# 8. URL scheme normalization
# ---------------------------------------------------------------------------

class TestURLSchemeNormalization:
    """
    extract_domain() requires a scheme to work correctly.
    main() must prepend https:// when scheme is absent.
    """

    def test_extract_domain_with_scheme(self):
        from geo_benchmark import extract_domain
        assert extract_domain("https://example.com/page") == "example.com"

    def test_extract_domain_without_scheme_breaks(self):
        """Without scheme, urlparse returns empty netloc — the fix is in main(), not here."""
        from geo_benchmark import extract_domain
        # This is the broken behavior that the URL scheme fix prevents
        result = extract_domain("example.com")
        assert result != "example.com"  # netloc is empty without scheme

    def test_scheme_prepended_in_main(self, monkeypatch, capsys):
        """main() prepends https:// when URL has no scheme."""
        import geo_benchmark
        captured_url = {}

        def mock_extract_domain(url):
            captured_url["url"] = url
            return "example.com"

        monkeypatch.setenv("PERPLEXITY_API_KEY", "fake")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setattr("sys.argv", ["geo_benchmark.py", "example.com", "--n", "1"])
        monkeypatch.setattr("geo_benchmark.extract_domain", mock_extract_domain)
        monkeypatch.setattr("geo_benchmark.fetch_headings", lambda url, timeout=15: [("h2", "Test heading")])
        monkeypatch.setattr("geo_benchmark.run_benchmark", lambda **kw: {
            "results": [{"query": "How to Test heading?", "cited": True, "engines_citing": ["perplexity"], "skipped": False}],
            "skipped_count": 0,
            "engine_pair": "perplexity",
        })

        geo_benchmark.main()

        assert captured_url.get("url", "").startswith("https://")

    def test_http_scheme_preserved(self, monkeypatch, capsys):
        """http:// URLs must not have https:// prepended."""
        import geo_benchmark
        captured_url = {}

        def mock_extract_domain(url):
            captured_url["url"] = url
            return "example.com"

        monkeypatch.setenv("PERPLEXITY_API_KEY", "fake")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setattr("sys.argv", ["geo_benchmark.py", "http://example.com", "--n", "1"])
        monkeypatch.setattr("geo_benchmark.extract_domain", mock_extract_domain)
        monkeypatch.setattr("geo_benchmark.fetch_headings", lambda url, timeout=15: [("h2", "Test")])
        monkeypatch.setattr("geo_benchmark.run_benchmark", lambda **kw: {
            "results": [{"query": "How to Test?", "cited": True, "engines_citing": ["perplexity"], "skipped": False}],
            "skipped_count": 0,
            "engine_pair": "perplexity",
        })

        geo_benchmark.main()

        assert captured_url.get("url", "").startswith("http://")
        assert not captured_url.get("url", "").startswith("https://")


# ---------------------------------------------------------------------------
# 9. Per-engine breakdown
# ---------------------------------------------------------------------------

class TestPerEngineBreakdown:
    """
    Per-engine breakdown: A=perplexity cited, B=openai cited, C=both, D=A+B-C (GEO)
    Must match GEO Score. Only shown in dual-engine mode.
    """

    def test_breakdown_math_d_equals_geo_numerator(self):
        """D = A + B - C must equal the GEO Score numerator."""
        from geo_benchmark import format_text_report, compute_score
        results = [
            {"query": "q1", "cited": True,  "engines_citing": ["perplexity", "openai"], "skipped": False},
            {"query": "q2", "cited": True,  "engines_citing": ["perplexity"],           "skipped": False},
            {"query": "q3", "cited": True,  "engines_citing": ["openai"],               "skipped": False},
            {"query": "q4", "cited": False, "engines_citing": [],                       "skipped": False},
        ]
        benchmark = {"results": results, "skipped_count": 0, "engine_pair": "perplexity+openai"}
        score_data = compute_score(results)
        sufficiency = {"reliable": True, "message": ""}
        report = format_text_report("example.com", score_data, benchmark, sufficiency)

        # A=2, B=2, C=1, D=3 — GEO Score = 3/4 = 75%
        assert "Either engine (GEO):     75%" in report
        assert f"GEO Score: 75/100" in report

    def test_breakdown_shown_in_dual_engine_mode(self):
        from geo_benchmark import format_text_report, compute_score
        results = [{"query": "q1", "cited": True, "engines_citing": ["perplexity", "openai"], "skipped": False}]
        benchmark = {"results": results, "skipped_count": 0, "engine_pair": "perplexity+openai"}
        score_data = compute_score(results)
        sufficiency = {"reliable": True, "message": ""}
        report = format_text_report("example.com", score_data, benchmark, sufficiency)
        assert "Per-engine breakdown:" in report

    def test_breakdown_not_shown_in_single_engine_mode(self):
        from geo_benchmark import format_text_report, compute_score
        results = [{"query": "q1", "cited": True, "engines_citing": ["perplexity"], "skipped": False}]
        benchmark = {"results": results, "skipped_count": 0, "engine_pair": "perplexity"}
        score_data = compute_score(results)
        sufficiency = {"reliable": True, "message": ""}
        report = format_text_report("example.com", score_data, benchmark, sufficiency)
        assert "Per-engine breakdown:" not in report

    def test_per_engine_json_field(self):
        """JSON output includes per_engine with cited/total per engine."""
        from geo_benchmark import run_benchmark, compute_score
        perplexity_cited = load_fixture("perplexity_cited.json")
        openai_not_cited = load_fixture("openai_not_cited.json")

        responses = iter([perplexity_cited, openai_not_cited])

        with patch("geo_benchmark.query_engine_with_retry", side_effect=lambda fn, q, **kw: next(responses)):
            result = run_benchmark(
                questions=["test?"],
                domain="example.com",
                perplexity_key="fake",
                openai_key="fake_openai",
            )

        assert result["engine_pair"] == "perplexity+openai"
        # Verify engines_citing reflects which engine actually cited
        r = result["results"][0]
        assert "perplexity" in r["engines_citing"]
        assert "openai" not in r["engines_citing"]


# ---------------------------------------------------------------------------
# 10. llms.txt content gap hints
# ---------------------------------------------------------------------------

class TestLlmsTxtHints:
    """
    Hints appear when any questions were not cited.
    Capped at 5. Not shown when all questions were cited.
    """

    def test_hints_appear_when_not_cited(self):
        from geo_benchmark import format_text_report, compute_score
        results = [
            {"query": "How to improve SEO?", "cited": False, "engines_citing": [], "skipped": False},
        ]
        benchmark = {"results": results, "skipped_count": 0, "engine_pair": "perplexity"}
        score_data = compute_score(results)
        sufficiency = {"reliable": True, "message": ""}
        report = format_text_report("example.com", score_data, benchmark, sufficiency)
        assert "llms.txt Content Gap Hints" in report
        assert '"How to improve SEO?"' in report

    def test_hints_not_shown_when_all_cited(self):
        from geo_benchmark import format_text_report, compute_score
        results = [
            {"query": "How to improve SEO?", "cited": True, "engines_citing": ["perplexity"], "skipped": False},
        ]
        benchmark = {"results": results, "skipped_count": 0, "engine_pair": "perplexity"}
        score_data = compute_score(results)
        sufficiency = {"reliable": True, "message": ""}
        report = format_text_report("example.com", score_data, benchmark, sufficiency)
        assert "llms.txt Content Gap Hints" not in report

    def test_hints_capped_at_five(self):
        from geo_benchmark import format_text_report, compute_score
        results = [
            {"query": f"Question {i}?", "cited": False, "engines_citing": [], "skipped": False}
            for i in range(10)
        ]
        benchmark = {"results": results, "skipped_count": 0, "engine_pair": "perplexity"}
        score_data = compute_score(results)
        sufficiency = {"reliable": True, "message": ""}
        report = format_text_report("example.com", score_data, benchmark, sufficiency)
        # Extract just the llms.txt hints section
        hints_section = report.split("## llms.txt Content Gap Hints")[-1]
        # Hints cap at 5: "Question 4?" is the 5th (0-indexed), "Question 5?" must not be a hint
        assert '"Question 4?"' in hints_section
        assert '"Question 5?"' not in hints_section

    def test_skipped_questions_not_in_hints(self):
        from geo_benchmark import format_text_report, compute_score
        results = [
            {"query": "Good question?", "cited": False, "engines_citing": [], "skipped": False},
            {"query": "Skipped question?", "cited": False, "engines_citing": [], "skipped": True},
        ]
        benchmark = {"results": results, "skipped_count": 1, "engine_pair": "perplexity"}
        score_data = compute_score([r for r in results if not r.get("skipped")])
        sufficiency = {"reliable": True, "message": ""}
        report = format_text_report("example.com", score_data, benchmark, sufficiency)
        hints_section = report.split("## llms.txt Content Gap Hints")[-1]
        assert '"Good question?"' in hints_section
        assert '"Skipped question?"' not in hints_section


# ---------------------------------------------------------------------------
# 11. --save flag: writes JSON, domain slug normalizes /, delta computation
# ---------------------------------------------------------------------------

class TestSaveFlag:
    """
    --save writes JSON to history dir.
    Domain slug normalizes '/' (for github.com/owner/repo).
    Second run shows delta.
    """

    def test_save_writes_valid_json(self, tmp_path, monkeypatch):
        """--save writes a JSON file with the correct schema."""
        import geo_benchmark
        monkeypatch.setenv("PERPLEXITY_API_KEY", "fake")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setattr("sys.argv", [
            "geo_benchmark.py", "https://example.com", "--n", "1", "--save",
        ])
        monkeypatch.setattr("geo_benchmark.fetch_headings", lambda url, timeout=15: [("h2", "Test")])
        monkeypatch.setattr("geo_benchmark.run_benchmark", lambda **kw: {
            "results": [{"query": "How to Test?", "cited": True, "engines_citing": ["perplexity"], "skipped": False}],
            "skipped_count": 0,
            "engine_pair": "perplexity",
        })
        history_dir = str(tmp_path / "seo-geo-history")
        monkeypatch.setattr("geo_benchmark.os.path.expanduser", lambda p: p.replace("~/.seo-geo-history/", history_dir + "/"))

        geo_benchmark.main()

        files = list(tmp_path.glob("seo-geo-history/*.json"))
        assert len(files) == 1
        with open(files[0]) as f:
            data = json.load(f)
        assert data["domain"] == "example.com"
        assert "score" in data
        assert "timestamp" in data
        assert "per_engine" in data

    def test_domain_slug_normalizes_slash(self, tmp_path, monkeypatch):
        """github.com/owner/repo domain has / replaced with - in filename."""
        import geo_benchmark
        monkeypatch.setenv("PERPLEXITY_API_KEY", "fake")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setattr("sys.argv", [
            "geo_benchmark.py", "https://github.com/owner/repo", "--n", "1", "--save",
        ])
        monkeypatch.setattr("geo_benchmark.fetch_headings", lambda url, timeout=15: [("h2", "Test")])
        monkeypatch.setattr("geo_benchmark.run_benchmark", lambda **kw: {
            "results": [{"query": "How to Test?", "cited": False, "engines_citing": [], "skipped": False}],
            "skipped_count": 0,
            "engine_pair": "perplexity",
        })
        history_dir = str(tmp_path / "seo-geo-history")
        monkeypatch.setattr("geo_benchmark.os.path.expanduser", lambda p: p.replace("~/.seo-geo-history/", history_dir + "/"))

        geo_benchmark.main()

        files = list(tmp_path.glob("seo-geo-history/*.json"))
        assert len(files) == 1
        assert "/" not in files[0].name


# ---------------------------------------------------------------------------
# 12. Delta with MOE note
# ---------------------------------------------------------------------------

class TestDeltaMOE:
    """
    Delta shown on second run.
    'not statistically significant' note when abs(delta) < MOE.
    No note when delta exceeds MOE.
    """

    def _make_history_file(self, history_dir, domain_slug, score, timestamp="2026-04-07-000000", engine_pair=None):
        os.makedirs(history_dir, exist_ok=True)
        path = os.path.join(history_dir, f"{domain_slug}-{timestamp}.json")
        data = {"domain": domain_slug, "score": score, "timestamp": "2026-04-07T00:00:00Z", "n": 20, "margin_of_error": 21.91}
        if engine_pair is not None:
            data["engine_pair"] = engine_pair
        with open(path, "w") as f:
            json.dump(data, f)
        return path

    def test_delta_shown_on_second_run(self, tmp_path, monkeypatch):
        """Second run shows previous score and delta."""
        import geo_benchmark
        history_dir = str(tmp_path / "hist")
        self._make_history_file(history_dir, "example.com", score=40.0)

        monkeypatch.setenv("PERPLEXITY_API_KEY", "fake")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setattr("sys.argv", [
            "geo_benchmark.py", "https://example.com", "--n", "20", "--save",
        ])
        monkeypatch.setattr("geo_benchmark.fetch_headings", lambda url, timeout=15: [("h2", f"H{i}") for i in range(20)])
        # 9 cited out of 20 = 45%
        cited_flags = [True] * 9 + [False] * 11
        monkeypatch.setattr("geo_benchmark.run_benchmark", lambda **kw: {
            "results": [
                {"query": f"How to H{i}?", "cited": cited_flags[i], "engines_citing": ["perplexity"] if cited_flags[i] else [], "skipped": False}
                for i in range(20)
            ],
            "skipped_count": 0,
            "engine_pair": "perplexity",
        })
        monkeypatch.setattr("geo_benchmark.os.path.expanduser", lambda p: p.replace("~/.seo-geo-history/", history_dir + "/"))

        captured = []
        original_print = print
        def mock_print(*args, **kwargs):
            if kwargs.get("file") is sys.stderr:
                original_print(*args, **kwargs)
            else:
                captured.append(" ".join(str(a) for a in args))
        monkeypatch.setattr("builtins.print", mock_print)

        geo_benchmark.main()

        full_output = "\n".join(captured)
        assert "Previous run:" in full_output
        assert "Score: 40/100" in full_output

    def test_moe_note_when_delta_within_moe(self, tmp_path, monkeypatch):
        """When delta < MOE, show 'not statistically significant' note."""
        import geo_benchmark
        history_dir = str(tmp_path / "hist")
        # Previous score 40, current will be 45 — delta=5, MOE≈21 — within MOE
        self._make_history_file(history_dir, "example.com", score=40.0)

        monkeypatch.setenv("PERPLEXITY_API_KEY", "fake")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setattr("sys.argv", [
            "geo_benchmark.py", "https://example.com", "--n", "20", "--save",
        ])
        monkeypatch.setattr("geo_benchmark.fetch_headings", lambda url, timeout=15: [("h2", f"H{i}") for i in range(20)])
        cited_flags = [True] * 9 + [False] * 11  # 45%
        monkeypatch.setattr("geo_benchmark.run_benchmark", lambda **kw: {
            "results": [
                {"query": f"How to H{i}?", "cited": cited_flags[i], "engines_citing": ["perplexity"] if cited_flags[i] else [], "skipped": False}
                for i in range(20)
            ],
            "skipped_count": 0,
            "engine_pair": "perplexity",
        })
        monkeypatch.setattr("geo_benchmark.os.path.expanduser", lambda p: p.replace("~/.seo-geo-history/", history_dir + "/"))

        captured = []
        original_print = print
        def mock_print(*args, **kwargs):
            if kwargs.get("file") is sys.stderr:
                original_print(*args, **kwargs)
            else:
                captured.append(" ".join(str(a) for a in args))
        monkeypatch.setattr("builtins.print", mock_print)

        geo_benchmark.main()
        full_output = "\n".join(captured)
        assert "not statistically significant" in full_output

    def test_no_moe_note_when_delta_exceeds_moe(self, tmp_path, monkeypatch):
        """When delta > MOE, do NOT show the insignificance note."""
        import geo_benchmark
        history_dir = str(tmp_path / "hist")
        # Previous score 0, current will be 100 — delta=100, far exceeds MOE
        self._make_history_file(history_dir, "example.com", score=0.0)

        monkeypatch.setenv("PERPLEXITY_API_KEY", "fake")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setattr("sys.argv", [
            "geo_benchmark.py", "https://example.com", "--n", "20", "--save",
        ])
        monkeypatch.setattr("geo_benchmark.fetch_headings", lambda url, timeout=15: [("h2", f"H{i}") for i in range(20)])
        monkeypatch.setattr("geo_benchmark.run_benchmark", lambda **kw: {
            "results": [
                {"query": f"How to H{i}?", "cited": True, "engines_citing": ["perplexity"], "skipped": False}
                for i in range(20)
            ],
            "skipped_count": 0,
            "engine_pair": "perplexity",
        })
        monkeypatch.setattr("geo_benchmark.os.path.expanduser", lambda p: p.replace("~/.seo-geo-history/", history_dir + "/"))

        captured = []
        original_print = print
        def mock_print(*args, **kwargs):
            if kwargs.get("file") is sys.stderr:
                original_print(*args, **kwargs)
            else:
                captured.append(" ".join(str(a) for a in args))
        monkeypatch.setattr("builtins.print", mock_print)

        geo_benchmark.main()
        full_output = "\n".join(captured)
        assert "Previous run:" in full_output
        assert "not statistically significant" not in full_output

    def test_engine_pair_mismatch_shows_warning(self, tmp_path, monkeypatch):
        """When engine_pair changes between runs, a note must be shown so delta is not misread."""
        import geo_benchmark
        history_dir = str(tmp_path / "hist")
        # Previous run was Perplexity-only
        self._make_history_file(history_dir, "example.com", score=40.0, engine_pair="perplexity")

        monkeypatch.setenv("PERPLEXITY_API_KEY", "fake")
        monkeypatch.setenv("OPENAI_API_KEY", "fake_openai")  # now dual-engine
        monkeypatch.setattr("sys.argv", [
            "geo_benchmark.py", "https://example.com", "--n", "20", "--save",
        ])
        monkeypatch.setattr("geo_benchmark.fetch_headings", lambda url, timeout=15: [("h2", f"H{i}") for i in range(20)])
        monkeypatch.setattr("geo_benchmark.run_benchmark", lambda **kw: {
            "results": [
                {"query": f"How to H{i}?", "cited": True, "engines_citing": ["perplexity", "openai"], "skipped": False}
                for i in range(20)
            ],
            "skipped_count": 0,
            "engine_pair": "perplexity+openai",
        })
        monkeypatch.setattr("geo_benchmark.os.path.expanduser", lambda p: p.replace("~/.seo-geo-history/", history_dir + "/"))

        captured = []
        original_print = print
        def mock_print(*args, **kwargs):
            if kwargs.get("file") is sys.stderr:
                original_print(*args, **kwargs)
            else:
                captured.append(" ".join(str(a) for a in args))
        monkeypatch.setattr("builtins.print", mock_print)

        geo_benchmark.main()
        full_output = "\n".join(captured)
        assert "engine_pair changed" in full_output
        assert "perplexity" in full_output
        assert "perplexity+openai" in full_output


# ---------------------------------------------------------------------------
# 13. headings_to_questions — primary question generation path
# ---------------------------------------------------------------------------

class TestHeadingsToQuestions:
    """
    headings_to_questions() is the primary question generation path.
    H1/H2 → "How to...?", H3 → "What is...?"
    Filler headings (HEADING_FILLER_BLOCKLIST) are skipped.
    Trailing ?. is stripped before formatting.
    """

    def test_h1_becomes_how_to(self):
        from geo_benchmark import headings_to_questions
        result = headings_to_questions([("h1", "Improve SEO")])
        assert result == ["How to Improve SEO?"]

    def test_h2_becomes_how_to(self):
        from geo_benchmark import headings_to_questions
        result = headings_to_questions([("h2", "Build Links")])
        assert result == ["How to Build Links?"]

    def test_h3_becomes_what_is(self):
        from geo_benchmark import headings_to_questions
        result = headings_to_questions([("h3", "Core Web Vitals")])
        assert result == ["What is Core Web Vitals?"]

    def test_filler_heading_skipped(self):
        """Headings in HEADING_FILLER_BLOCKLIST must be excluded."""
        from geo_benchmark import headings_to_questions
        for filler in ["Introduction", "FAQ", "Overview", "Conclusion", "Summary"]:
            assert headings_to_questions([("h2", filler)]) == [], f"Expected {filler!r} to be filtered"

    def test_trailing_punctuation_stripped(self):
        """Trailing ? and . in heading text must be stripped before formatting."""
        from geo_benchmark import headings_to_questions
        result = headings_to_questions([("h2", "Improve SEO.")])
        assert result == ["How to Improve SEO?"]
        result = headings_to_questions([("h2", "Improve SEO?")])
        assert result == ["How to Improve SEO?"]

    def test_mixed_headings(self):
        """Mix of H1, H2, H3, and filler in one call."""
        from geo_benchmark import headings_to_questions
        headings = [
            ("h1", "Improve SEO"),
            ("h2", "Introduction"),   # filler — skipped
            ("h3", "E-E-A-T"),
            ("h2", "Build Links"),
        ]
        result = headings_to_questions(headings)
        assert result == [
            "How to Improve SEO?",
            "What is E-E-A-T?",
            "How to Build Links?",
        ]


# ---------------------------------------------------------------------------
# 14. generate_questions_with_llm — LLM-based question generation path
# ---------------------------------------------------------------------------

class TestGenerateQuestionsWithLLM:
    """
    generate_questions_with_llm() calls GPT-4o-mini, strips markdown fences,
    parses JSON. Any failure returns [] (fallback to heading parse).
    """

    def test_happy_path_returns_questions(self, monkeypatch):
        """Clean JSON array returned by LLM is parsed correctly."""
        import geo_benchmark
        from unittest.mock import Mock
        mock_get = Mock()
        mock_get.raise_for_status = Mock()
        mock_get.text = "<html><body><h1>SEO Guide</h1></body></html>"
        mock_post = Mock()
        mock_post.raise_for_status = Mock()
        mock_post.json.return_value = {
            "choices": [{"message": {"content": '["What is SEO?", "How to build links?"]'}}]
        }
        monkeypatch.setattr("geo_benchmark.requests.get", lambda *a, **kw: mock_get)
        monkeypatch.setattr("geo_benchmark.requests.post", lambda *a, **kw: mock_post)
        result = geo_benchmark.generate_questions_with_llm("https://example.com", "fake_key", 2)
        assert result == ["What is SEO?", "How to build links?"]

    def test_page_content_passed_to_llm(self, monkeypatch):
        """Page content is fetched and included in the LLM prompt."""
        import geo_benchmark
        from unittest.mock import Mock
        captured = {}
        mock_get = Mock()
        mock_get.raise_for_status = Mock()
        mock_get.text = "<html><body><h1>Stripe Payments API</h1><p>Accept payments globally.</p></body></html>"
        mock_post = Mock()
        mock_post.raise_for_status = Mock()
        mock_post.json.return_value = {
            "choices": [{"message": {"content": '["How does Stripe Payments API work?"]'}}]
        }
        def capture_post(*args, **kwargs):
            captured["body"] = kwargs.get("json", {})
            return mock_post
        monkeypatch.setattr("geo_benchmark.requests.get", lambda *a, **kw: mock_get)
        monkeypatch.setattr("geo_benchmark.requests.post", capture_post)
        geo_benchmark.generate_questions_with_llm("https://stripe.com", "fake_key", 1)
        user_msg = captured["body"]["messages"][1]["content"]
        assert "Stripe Payments API" in user_msg
        assert "Page content" in user_msg

    def test_fetch_failure_falls_back_to_url_only(self, monkeypatch):
        """If page fetch fails, LLM still runs with URL-only prompt (no crash)."""
        import geo_benchmark
        from unittest.mock import Mock
        captured = {}
        def raise_on_get(*args, **kwargs):
            raise ConnectionError("timeout")
        mock_post = Mock()
        mock_post.raise_for_status = Mock()
        mock_post.json.return_value = {
            "choices": [{"message": {"content": '["What is SEO?"]'}}]
        }
        def capture_post(*args, **kwargs):
            captured["body"] = kwargs.get("json", {})
            return mock_post
        monkeypatch.setattr("geo_benchmark.requests.get", raise_on_get)
        monkeypatch.setattr("geo_benchmark.requests.post", capture_post)
        result = geo_benchmark.generate_questions_with_llm("https://example.com", "fake_key", 1)
        assert result == ["What is SEO?"]
        user_msg = captured["body"]["messages"][1]["content"]
        assert "Page content" not in user_msg

    def test_markdown_fence_stripped(self, monkeypatch):
        """LLM response wrapped in ```json ... ``` fences is unwrapped correctly."""
        import geo_benchmark
        from unittest.mock import Mock
        mock_get = Mock()
        mock_get.raise_for_status = Mock()
        mock_get.text = "<html><body><p>content</p></body></html>"
        mock_post = Mock()
        mock_post.raise_for_status = Mock()
        mock_post.json.return_value = {
            "choices": [{"message": {"content": '```json\n["What is SEO?"]\n```'}}]
        }
        monkeypatch.setattr("geo_benchmark.requests.get", lambda *a, **kw: mock_get)
        monkeypatch.setattr("geo_benchmark.requests.post", lambda *a, **kw: mock_post)
        result = geo_benchmark.generate_questions_with_llm("https://example.com", "fake_key", 1)
        assert result == ["What is SEO?"]

    def test_exception_returns_empty_list(self, monkeypatch):
        """Any exception (timeout, bad JSON, auth error) returns [] for graceful fallback."""
        import geo_benchmark
        from unittest.mock import Mock
        mock_get = Mock()
        mock_get.raise_for_status = Mock()
        mock_get.text = "<html><body></body></html>"
        def raise_timeout(*args, **kwargs):
            raise TimeoutError("connection timeout")
        monkeypatch.setattr("geo_benchmark.requests.get", lambda *a, **kw: mock_get)
        monkeypatch.setattr("geo_benchmark.requests.post", raise_timeout)
        result = geo_benchmark.generate_questions_with_llm("https://example.com", "fake_key", 5)
        assert result == []


class TestFetchPageText:
    """Tests for fetch_page_text helper."""

    def test_returns_visible_text(self, monkeypatch):
        """Extracts text from body, strips scripts and styles."""
        import geo_benchmark
        from unittest.mock import Mock
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        mock_resp.text = (
            "<html><head><style>body{margin:0}</style></head>"
            "<body><script>alert(1)</script><h1>SEO Guide</h1><p>Learn SEO.</p></body></html>"
        )
        monkeypatch.setattr("geo_benchmark.requests.get", lambda *a, **kw: mock_resp)
        text = geo_benchmark.fetch_page_text("https://example.com")
        assert "SEO Guide" in text
        assert "Learn SEO" in text
        assert "alert" not in text
        assert "margin" not in text

    def test_truncates_to_max_chars(self, monkeypatch):
        """Output is capped at max_chars."""
        import geo_benchmark
        from unittest.mock import Mock
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        mock_resp.text = f"<html><body><p>{'x' * 5000}</p></body></html>"
        monkeypatch.setattr("geo_benchmark.requests.get", lambda *a, **kw: mock_resp)
        text = geo_benchmark.fetch_page_text("https://example.com", max_chars=100)
        assert len(text) <= 100

    def test_returns_empty_on_fetch_failure(self, monkeypatch):
        """Returns empty string if page fetch fails (no exception raised)."""
        import geo_benchmark
        def raise_err(*args, **kwargs):
            raise ConnectionError("timeout")
        monkeypatch.setattr("geo_benchmark.requests.get", raise_err)
        text = geo_benchmark.fetch_page_text("https://example.com")
        assert text == ""


class TestExtractDomainEdgeCases:
    """Guard against empty domain causing false-positive citation matches."""

    def test_malformed_url_returns_empty_string(self):
        """http:// with no host produces empty domain — callers must guard."""
        from geo_benchmark import extract_domain
        assert extract_domain("http://") == ""

    def test_empty_domain_matches_every_url(self):
        """Demonstrates why empty domain is dangerous: '' in any URL = True."""
        # This is a property test, not a feature — documents the footgun.
        assert "" in "https://example.com/page"
        assert "" in "https://totally-unrelated.com"


# ---------------------------------------------------------------------------
# 15. format_text_report — reliability warning + recommendation tiers
# ---------------------------------------------------------------------------

class TestFormatTextReportEdgeCases:
    """
    format_text_report() shows a WARNING prefix when reliable=False.
    Recommendation tiers: <20 → llms.txt + FAQ, <50 → expand + schema, >=50 → maintain.
    """

    def test_unreliable_score_shows_warning(self):
        """When reliable=False, the report must include a WARNING line."""
        from geo_benchmark import format_text_report, compute_score
        results = [{"cited": False}]
        score_data = compute_score(results)
        benchmark = {"results": [{"query": "q1", "cited": False, "engines_citing": [], "skipped": False}],
                     "skipped_count": 0, "engine_pair": "perplexity"}
        sufficiency = {"reliable": False, "message": "Insufficient data, score unreliable: 11/20 questions skipped"}
        report = format_text_report("example.com", score_data, benchmark, sufficiency)
        assert "WARNING:" in report
        assert "Insufficient data" in report

    def test_score_below_20_recommends_llmstxt_and_faq(self):
        """Score < 20 → recommend llms.txt + FAQ + crawler access."""
        from geo_benchmark import format_text_report, compute_score
        results = [{"cited": False}] * 10
        score_data = compute_score(results)
        benchmark = {"results": [{"query": f"q{i}", "cited": False, "engines_citing": [], "skipped": False} for i in range(10)],
                     "skipped_count": 0, "engine_pair": "perplexity"}
        sufficiency = {"reliable": True, "message": ""}
        report = format_text_report("example.com", score_data, benchmark, sufficiency)
        assert "llms.txt" in report
        assert "FAQ" in report

    def test_score_50_or_above_recommends_maintenance(self):
        """Score >= 50 → recommend maintaining content freshness."""
        from geo_benchmark import format_text_report, compute_score
        results = [{"cited": True}] * 10
        score_data = compute_score(results)
        benchmark = {"results": [{"query": f"q{i}", "cited": True, "engines_citing": ["perplexity"], "skipped": False} for i in range(10)],
                     "skipped_count": 0, "engine_pair": "perplexity"}
        sufficiency = {"reliable": True, "message": ""}
        report = format_text_report("example.com", score_data, benchmark, sufficiency)
        assert "Strong citation rate" in report


class TestComparisonTable:
    """Tests for _format_comparison_table."""

    def test_shows_all_domains(self):
        """Primary domain and all competitors appear in table."""
        from geo_benchmark import _format_comparison_table
        rows = [
            {"domain": "competitor.com", "score": 60.0, "n": 20, "margin_of_error": 21.0},
        ]
        table = _format_comparison_table("example.com", {"score": 45.0, "n": 20, "margin_of_error": 22.0}, rows)
        assert "example.com (you)" in table
        assert "competitor.com" in table

    def test_gap_behind_shows_negative(self):
        """When primary is behind top competitor, gap line shows negative."""
        from geo_benchmark import _format_comparison_table
        rows = [{"domain": "top.com", "score": 70.0, "n": 20, "margin_of_error": 20.0}]
        table = _format_comparison_table("example.com", {"score": 40.0, "n": 20, "margin_of_error": 22.0}, rows)
        assert "behind top.com" in table
        assert "-30" in table

    def test_gap_ahead_shows_positive(self):
        """When primary is ahead, gap line shows positive."""
        from geo_benchmark import _format_comparison_table
        rows = [{"domain": "slow.com", "score": 20.0, "n": 20, "margin_of_error": 18.0}]
        table = _format_comparison_table("example.com", {"score": 55.0, "n": 20, "margin_of_error": 22.0}, rows)
        assert "ahead of slow.com" in table
        assert "+35" in table

    def test_sorted_by_score_descending(self):
        """Table rows appear sorted highest score first."""
        from geo_benchmark import _format_comparison_table
        rows = [
            {"domain": "low.com", "score": 20.0, "n": 20, "margin_of_error": 18.0},
            {"domain": "high.com", "score": 80.0, "n": 20, "margin_of_error": 18.0},
        ]
        table = _format_comparison_table("example.com", {"score": 50.0, "n": 20, "margin_of_error": 22.0}, rows)
        assert table.index("high.com") < table.index("low.com")
