from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Sport = Literal["football", "f1", "chess", "unknown"]
DesignName = Literal["single_agent", "sequential_chain", "triage_handoff", "committee_referee"]


class Citation(BaseModel):
    source_id: str
    title: str | None = None
    url: str | None = None
    retrieved_at: str | None = None


class AgentAnswer(BaseModel):
    question: str
    design: str
    answer: str
    sports: list[str] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    skills_used: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    citation_details: list[Citation] = Field(default_factory=list)
    abstained: bool = False
    uncertainty_notes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    structured_facts: dict[str, Any] = Field(default_factory=dict)
    trace: list[str] = Field(default_factory=list)
    cost_proxy: float = 0.0


class EvalCase(BaseModel):
    case_id: str
    question: str
    expected_sports: list[str]
    expected_keywords: list[str] = Field(default_factory=list)
    forbidden_keywords: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    required_citations: list[str] = Field(default_factory=list)
    should_abstain: bool = False


class EvalResult(BaseModel):
    case_id: str
    question: str
    design: str
    passed: bool
    route_accuracy: float
    tool_recall: float
    skill_recall: float
    citation_recall: float
    keyword_recall: float
    forbidden_absence: float
    abstention_accuracy: float
    unsupported_claim: bool
    tool_calls: int
    cost_proxy: float
    answer: AgentAnswer
    failures: list[str] = Field(default_factory=list)
