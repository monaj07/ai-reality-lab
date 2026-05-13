from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class Citation(BaseModel):
    id: str
    source_id: str
    title: str
    url: str
    detail: str = ""


class ForecastClaim(BaseModel):
    text: str
    citation_ids: list[str] = Field(default_factory=list)


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
