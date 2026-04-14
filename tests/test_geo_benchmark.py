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
