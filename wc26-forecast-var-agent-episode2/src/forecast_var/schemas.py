from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

ClaimType = Literal[
    "field_fact",
    "source_policy",
    "model_input",
    "model_output",
    "scenario_assumption",
    "uncertainty",
    "guardrail",
    "market_baseline",
    "source_coverage",
    "evidence_retrieval",
    "simulation_output",
    "rolling_state",
    "general",
]


class Citation(BaseModel):
    id: str
    source_id: str
    title: str
    url: str
    detail: str = ""


class ForecastClaim(BaseModel):
    text: str
    claim_type: ClaimType = "general"
    citation_ids: list[str] = Field(default_factory=list)


class ClaimVerification(BaseModel):
    claim: str
    claim_type: str
    citation_ids: list[str]
    source_ids: list[str]
    support_labels: list[str]
    support_class: str
    supported: bool
    reason: str


class AgentAnswer(BaseModel):
    answer: str
    claims: list[ForecastClaim] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    skills_used: list[str] = Field(default_factory=list)
    probabilities: dict[str, float] = Field(default_factory=dict)
    abstained: bool = False
    confidence: str = "medium"
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
