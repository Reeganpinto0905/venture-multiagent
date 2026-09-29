"""
Automated Research Feature Tests for VentureIQ using standard unittest:
1. Public startup benchmark schema & pilot dataset
2. Historical backtesting with date cutoffs (no look-ahead bias)
3. PRO vs CONTRA analysis across 7 institutional dimensions
4. Critic -> Evaluator -> Refiner verification loop
5. Evidence utilization metrics calculation
6. Historical outcome metrics (Precision, Recall, F1, AUC-PR, Confusion Matrix)
"""

import os
import sys
import unittest

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from evaluation.benchmark_schema import load_benchmark_dataset, BenchmarkStartup
from evaluation.backtester import filter_startup_by_cutoff, verify_no_lookahead_bias, is_date_prior_or_equal
from agents.pro_contra import analyze_pro_contra, DUE_DILIGENCE_DIMENSIONS
from agents.verification_loop import run_verification_loop, VerificationCritic, VerificationEvaluator, VerificationRefiner
from evaluation.evidence_utilization import calculate_evidence_utilization
from evaluation.outcome_metrics import evaluate_outcome_prediction, compute_auc_pr


class TestVentureIQResearchFeatures(unittest.TestCase):

    def test_step1_benchmark_dataset_schema(self):
        dataset_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "evaluation", "benchmark_dataset.json"))
        startups = load_benchmark_dataset(dataset_path)

        self.assertGreaterEqual(len(startups), 5, f"Expected pilot dataset of at least 5 startups, found {len(startups)}")

        for s in startups:
            self.assertTrue(s.startup_id, "startup_id must be non-empty")
            self.assertTrue(s.name, "name must be non-empty")
            self.assertTrue(s.industry, "industry must be non-empty")
            self.assertTrue(s.historical_cutoff, "historical_cutoff date must be present")
            self.assertGreater(len(s.sources), 0, f"Startup {s.name} must have public sources")
            self.assertGreater(len(s.facts), 0, f"Startup {s.name} must have verifiable facts")
            for fact in s.facts:
                self.assertTrue(fact.evidence_id, "Every fact must have an evidence_id")
                self.assertIn(fact.category, DUE_DILIGENCE_DIMENSIONS, f"Fact category {fact.category} must be in standard dimensions")
            if s.later_outcome:
                self.assertIn(s.later_outcome.status, ["SUCCESS", "FAILURE", "ACQUIRED", "UNKNOWN"])

    def test_step2_historical_backtesting_no_lookahead_bias(self):
        dataset_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "evaluation", "benchmark_dataset.json"))
        startups = load_benchmark_dataset(dataset_path)

        quibi = next(s for s in startups if s.startup_id == "quibi")
        # Cutoff date is 2020-04-01.
        # Source published on 2020-10-22 must be strictly excluded.
        filtered_quibi = filter_startup_by_cutoff(quibi, "2020-04-01")

        # Verification:
        self.assertLess(len(filtered_quibi.sources), len(quibi.sources), "Post-cutoff source was not filtered out")
        for s in filtered_quibi.sources:
            self.assertTrue(
                is_date_prior_or_equal(s.publication_date, "2020-04-01"),
                f"Leaked future source {s.document} dated {s.publication_date}"
            )

        # Audit check:
        audit = verify_no_lookahead_bias(filtered_quibi, "2020-04-01")
        self.assertTrue(audit["passed"])
        self.assertEqual(audit["leaked_sources_count"], 0)
        self.assertEqual(audit["leaked_facts_count"], 0)

        # Ensure outcome is stripped to prevent target label leakage
        self.assertIsNone(filtered_quibi.later_outcome)

    def test_step3_pro_contra_7_dimensions(self):
        dataset_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "evaluation", "benchmark_dataset.json"))
        startups = load_benchmark_dataset(dataset_path)
        sprig = next(s for s in startups if s.startup_id == "sprig")

        res = analyze_pro_contra(sprig.name, entities=[], facts=sprig.facts)
        dims = res["dimensions"]

        # All 7 dimensions must exist
        for d in DUE_DILIGENCE_DIMENSIONS:
            self.assertIn(d, dims, f"Dimension {d} missing from PRO/CONTRA analysis")

        # Sprig had negative gross margins ($6 loss per meal) -> Financials must have contradicting evidence
        fin = dims["Financials"]
        self.assertGreater(len(fin["contradicting_evidence"]), 0)
        self.assertTrue(any("loss" in e["claim"].lower() or "risks" in e["evidence_id"] for e in fin["contradicting_evidence"]))

        # Every evidence point must reference an evidence_id
        for d_name, d_val in dims.items():
            for pt in d_val["supporting_evidence"] + d_val["contradicting_evidence"]:
                self.assertIn("evidence_id", pt)
                self.assertIn(pt["status"], ["VERIFIED", "INFERENCE", "UNKNOWN"])

    def test_step4_verification_loop_unsupported_reduction(self):
        draft = "Quibi raised $1.75B with guaranteed 100% certainty market dominance like Uber for television."
        valid_eids = ["companies/quibi"]

        loop_res = run_verification_loop(draft, valid_eids, max_iterations=2)

        self.assertLessEqual(loop_res["iterations_run"], 2)
        # Unsupported / overconfident claims should be reduced or neutralized
        self.assertGreaterEqual(loop_res["before_unsupported_count"], loop_res["after_unsupported_count"])
        self.assertNotIn("guaranteed", loop_res["verified_text"].lower())
        self.assertNotIn("like uber for", loop_res["verified_text"].lower())

    def test_step5_evidence_utilization(self):
        avail = [
            {"id": "comp_1", "category": "companies"},
            {"id": "comp_2", "category": "companies"},
            {"id": "risk_1", "category": "risks"},
            {"id": "bm_1", "category": "business_models"}
        ]
        retrieved = [
            {"id": "comp_1", "category": "companies"},
            {"id": "risk_1", "category": "risks"}
        ]
        used = [
            {"id": "comp_1", "category": "companies"}
        ]
        cited = ["comp_1"]

        metrics = calculate_evidence_utilization(avail, retrieved, used, cited)
        macro = metrics["macro_metrics"]

        self.assertEqual(macro["total_available"], 4)
        self.assertEqual(macro["total_retrieved"], 2)
        self.assertEqual(macro["total_used"], 1)
        self.assertEqual(macro["total_cited"], 1)

        # retrieval_rate = 2/4 * 100 = 50.0%
        self.assertEqual(macro["retrieval_rate"]["value_percent"], 50.0)
        # utilization_rate = 1/4 * 100 = 25.0%
        self.assertEqual(macro["utilization_rate"]["value_percent"], 25.0)
        # citation_rate = 1/1 * 100 = 100.0%
        self.assertEqual(macro["citation_rate"]["value_percent"], 100.0)

    def test_step6_outcome_metrics_and_threshold(self):
        # 1. Under minimum threshold -> Fail-safe to "Not experimentally verified"
        under_threshold_cases = [
            {"startup_id": "s1", "predicted_verdict": "FAILURE", "risk_score": 80, "actual_outcome": "FAILURE"},
            {"startup_id": "s2", "predicted_verdict": "SUCCESS", "risk_score": 20, "actual_outcome": "SUCCESS"}
        ]
        insufficient_res = evaluate_outcome_prediction(under_threshold_cases)
        self.assertEqual(insufficient_res["status"], "Not experimentally verified")
        self.assertEqual(insufficient_res["metrics"]["precision"], "Not experimentally verified")

        # 2. Labeled cases >= 4
        labeled_cases = [
            {"startup_id": "quibi", "predicted_verdict": "FAILURE", "risk_score": 85, "actual_outcome": "FAILURE"},
            {"startup_id": "sprig", "predicted_verdict": "FAILURE", "risk_score": 90, "actual_outcome": "FAILURE"},
            {"startup_id": "beepi", "predicted_verdict": "FAILURE", "risk_score": 80, "actual_outcome": "FAILURE"},
            {"startup_id": "airbnb", "predicted_verdict": "SUCCESS", "risk_score": 20, "actual_outcome": "SUCCESS"},
            {"startup_id": "stripe", "predicted_verdict": "SUCCESS", "risk_score": 25, "actual_outcome": "SUCCESS"}
        ]
        outcome_eval = evaluate_outcome_prediction(labeled_cases, positive_label="FAILURE")
        self.assertEqual(outcome_eval["status"], "EXPERIMENTALLY_VERIFIED")
        self.assertEqual(outcome_eval["confusion_matrix"]["tp"], 3)
        self.assertEqual(outcome_eval["confusion_matrix"]["fp"], 0)
        self.assertEqual(outcome_eval["confusion_matrix"]["tn"], 2)
        self.assertEqual(outcome_eval["confusion_matrix"]["fn"], 0)
        self.assertEqual(outcome_eval["metrics"]["precision"]["value_percent"], 100.0)
        self.assertEqual(outcome_eval["metrics"]["recall"]["value_percent"], 100.0)
        self.assertEqual(outcome_eval["metrics"]["f1"]["value_percent"], 100.0)
        self.assertGreater(outcome_eval["metrics"]["auc_pr"]["value"], 0.0)


if __name__ == "__main__":
    unittest.main()
