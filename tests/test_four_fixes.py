"""
Targeted tests verifying the 4 fixes:
1. OKF cold-start -> Tavily fallback with timestamp and source URL.
2. Tavily failure fallback (cache -> OKF -> UNKNOWN) with exponential backoff.
3. Refiner claim classification: VERIFIED_FACT, INFERENCE, EXTERNAL_BENCHMARK, UNKNOWN.
4. Gemini token optimization: prompt caching, skipping unnecessary agent calls on absent evidence, supervisor reuse.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from knowledge.retriever import retrieve_context
from tools.search_tool import search_web
from agents.verification_loop import classify_claim, run_verification_loop, VerificationRefiner, CLAIM_TYPES
from agents.llm_utils import invoke_gemini, _STATS, get_gemini_stats
from agents.market import market_agent
from agents.supervisor import supervisor_chat


class TestFourFixes(unittest.TestCase):

    def test_fix1_okf_cold_start_to_tavily_fallback(self):
        """Verify that when OKF evidence is insufficient, it triggers Tavily and labels as Live Web Evidence."""
        with patch("tools.search_tool.TavilyClient") as mock_tavily_class:
            mock_client = MagicMock()
            mock_client.search.return_value = {
                "results": [{
                    "title": "Quantum Satellite Cryptography Market 2026",
                    "content": "Global quantum satellite encryption market growing at 34% CAGR.",
                    "url": "https://example.com/quantum-satellite-2026"
                }]
            }
            mock_tavily_class.return_value = mock_client

            # Query completely absent from the 67 startup OKF entities
            query = "quantum satellite entangled orbital encryption security"
            res = retrieve_context(query, top_k=2)

            self.assertIn("Live Web Evidence (OKF Cold-Start Fallback)", res)
            self.assertIn("Source URL: https://example.com/quantum-satellite-2026", res)
            self.assertIn("Fetched:", res)

    def test_fix2_tavily_failure_to_okf_or_unknown_fallback(self):
        """Verify that when Tavily fails, it falls back to low-confidence OKF or returns UNKNOWN (no hallucinations)."""
        with patch("tools.search_tool.TavilyClient") as mock_tavily_class:
            mock_client = MagicMock()
            mock_client.search.side_effect = ConnectionError("Tavily unreachable")
            mock_tavily_class.return_value = mock_client

            # For an imaginary query with zero matches in OKF and failed Tavily
            impossible_query = "xyzqwerty987654321randomquerynotindatabase"
            res = retrieve_context(impossible_query, top_k=2)

            self.assertEqual(res, "UNKNOWN / Insufficient Evidence")

    def test_fix3_refiner_claim_classification(self):
        """Verify 4-tier classification: VERIFIED_FACT, INFERENCE, EXTERNAL_BENCHMARK, UNKNOWN."""
        # 1. VERIFIED_FACT
        fact_claim = "Quibi raised $1.75B in pre-launch capital [OKF Evidence #1 | Quibi]."
        self.assertEqual(classify_claim(fact_claim, ["companies/quibi"]), CLAIM_TYPES["VERIFIED_FACT"])

        # 2. INFERENCE
        inference_claim = "Three early pilot deployments may indicate strong initial enterprise customer traction."
        self.assertEqual(classify_claim(inference_claim), CLAIM_TYPES["INFERENCE"])

        # 3. EXTERNAL_BENCHMARK
        benchmark_claim = "The typical industry average SaaS churn benchmark is under 5% annually."
        self.assertEqual(classify_claim(benchmark_claim), CLAIM_TYPES["EXTERNAL_BENCHMARK"])

        # 4. UNKNOWN
        unknown_claim = "Exact revenue, retention, and gross margins cannot be verified in submitted materials."
        self.assertEqual(classify_claim(unknown_claim), CLAIM_TYPES["UNKNOWN"])

        # 5. Full loop verification
        draft_text = (
            "Quibi raised $1.75B [Evidence: companies/quibi]. "
            "High early engagement may indicate customer interest. "
            "Typical industry average CAC payback is 12 months. "
            "Specific customer retention metrics cannot be verified."
        )
        loop_res = run_verification_loop(draft_text, ["companies/quibi"])
        classifications = [c["classification"] for c in loop_res["classified_claims"]]
        self.assertIn("VERIFIED_FACT", classifications)
        self.assertIn("INFERENCE", classifications)
        self.assertIn("EXTERNAL_BENCHMARK", classifications)
        self.assertIn("UNKNOWN", classifications)

    def test_fix4_gemini_token_optimization_caching_and_skipping(self):
        """Verify prompt caching and skipping unnecessary Gemini calls."""
        # 1. Test SQLite Prompt Caching
        with patch("agents.llm_utils._call_gemini_rest") as mock_rest:
            mock_rest.return_value = ('{"analysis": "Cached analysis"}', {"promptTokenCount": 50, "candidatesTokenCount": 20})
            
            initial_calls = _STATS["gemini_calls"]
            p = "Unique Test Prompt for Token Caching Verification"

            # First invocation: cache miss, executes call
            res1 = invoke_gemini(p, phase="test_cache", use_cache=True)
            self.assertEqual(res1, '{"analysis": "Cached analysis"}')

            # Second invocation: cache hit, does not call _call_gemini_rest again
            mock_rest.reset_mock()
            res2 = invoke_gemini(p, phase="test_cache", use_cache=True)
            self.assertEqual(res2, '{"analysis": "Cached analysis"}')
            mock_rest.assert_not_called()

        # 2. Test Skipping Agent LLM Call when evidence is absent
        absent_state = {
            "user_query": "",
            "market_context": "UNKNOWN / Insufficient Evidence",
            "retrieved_context": "UNKNOWN / Insufficient Evidence"
        }
        with patch("agents.market.search_web", return_value="UNKNOWN / Insufficient Evidence: No search query provided."):
            with patch("agents.market.invoke_gemini") as mock_agent_llm:
                market_res = market_agent(absent_state)
                # LLM should be skipped entirely
                mock_agent_llm.assert_not_called()
                self.assertIn("UNKNOWN / Insufficient Evidence", market_res["market_analysis"])

        # 3. Test Supervisor Skipping LLM Call when core profile is complete
        ready_state = {
            "conversation": [],
            "startup_profile": {
                "problem": "Manual AP reconciliation delays",
                "target_customer": "Mid-market B2B finance teams",
                "business_model": "Seat-based SaaS $299/mo"
            },
            "questions_asked": 2
        }
        with patch("agents.supervisor.invoke_gemini") as mock_sup_llm:
            sup_res = supervisor_chat(ready_state, "Can you validate now?")
            mock_sup_llm.assert_not_called()
            self.assertTrue(sup_res["ready_for_analysis"])


if __name__ == "__main__":
    unittest.main()
