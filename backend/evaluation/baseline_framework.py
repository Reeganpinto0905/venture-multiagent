"""
Evaluation Interface & Configuration for Experimental Baseline Comparison.
Supports 4 architectural paradigms:
A. Single LLM (Zero-shot / Direct prompt without retrieval)
B. Conventional RAG (Unstructured chunk retrieval + Single LLM)
C. Multi-Agent RAG (Multi-agent supervisor without structured OKF schema)
D. VentureIQ OKF + Evidence Verification (OKF v0.2 + Critic-Evaluator-Refiner verification)
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class ArchitectureParadigm(str, Enum):
    SINGLE_LLM = "Single_LLM"
    CONVENTIONAL_RAG = "Conventional_RAG"
    MULTI_AGENT_RAG = "Multi_Agent_RAG"
    VENTUREIQ_OKF_VERIFIED = "VentureIQ_OKF_Evidence_Verification"


@dataclass
class BaselineConfig:
    paradigm: ArchitectureParadigm
    system_name: str
    description: str
    has_retrieval: bool
    retrieval_mode: str  # none | vector_chunks | okf_structured
    has_multi_agent: bool
    has_verification_loop: bool
    is_active_for_evaluation: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "paradigm": self.paradigm.value,
            "system_name": self.system_name,
            "description": self.description,
            "has_retrieval": self.has_retrieval,
            "retrieval_mode": self.retrieval_mode,
            "has_multi_agent": self.has_multi_agent,
            "has_verification_loop": self.has_verification_loop,
            "is_active_for_evaluation": self.is_active_for_evaluation
        }


# Standard Benchmark Architectures
STANDARD_ARCHITECTURES = {
    ArchitectureParadigm.SINGLE_LLM: BaselineConfig(
        paradigm=ArchitectureParadigm.SINGLE_LLM,
        system_name="Baseline A: Single LLM Direct",
        description="Standard single-prompt LLM inference with no external retrieval or agent orchestration.",
        has_retrieval=False,
        retrieval_mode="none",
        has_multi_agent=False,
        has_verification_loop=False,
        is_active_for_evaluation=False
    ),
    ArchitectureParadigm.CONVENTIONAL_RAG: BaselineConfig(
        paradigm=ArchitectureParadigm.CONVENTIONAL_RAG,
        system_name="Baseline B: Conventional Unstructured RAG",
        description="Traditional vector retrieval over unstructured text chunks into a single LLM prompt.",
        has_retrieval=True,
        retrieval_mode="vector_chunks",
        has_multi_agent=False,
        has_verification_loop=False,
        is_active_for_evaluation=False
    ),
    ArchitectureParadigm.MULTI_AGENT_RAG: BaselineConfig(
        paradigm=ArchitectureParadigm.MULTI_AGENT_RAG,
        system_name="Baseline C: Multi-Agent Unstructured RAG",
        description="Specialized multi-agent swarm without structured OKF schema or formal verification loop.",
        has_retrieval=True,
        retrieval_mode="vector_chunks",
        has_multi_agent=True,
        has_verification_loop=False,
        is_active_for_evaluation=False
    ),
    ArchitectureParadigm.VENTUREIQ_OKF_VERIFIED: BaselineConfig(
        paradigm=ArchitectureParadigm.VENTUREIQ_OKF_VERIFIED,
        system_name="VentureIQ: OKF Structured + Verification Loop",
        description="Dual-tier OKF knowledge bundle, deterministic routing, and Critic-Evaluator-Refiner verification.",
        has_retrieval=True,
        retrieval_mode="okf_structured",
        has_multi_agent=True,
        has_verification_loop=True,
        is_active_for_evaluation=True
    )
}


def get_baseline_comparison_template() -> Dict[str, Any]:
    """
    Returns reproducible schema for baseline comparisons without executing expensive runs prematurely.
    """
    return {
        "framework_version": "v1.0.0",
        "description": "Standardized benchmarking protocol for startup due diligence architectures.",
        "architectures": {
            k.value: cfg.to_dict() for k, cfg in STANDARD_ARCHITECTURES.items()
        },
        "evaluation_metrics_protocol": [
            "retrieval_hit_rate",
            "groundedness_score",
            "unsupported_claim_rate",
            "pipeline_latency_sec",
            "precision",
            "recall",
            "f1_score",
            "auc_pr"
        ]
    }
