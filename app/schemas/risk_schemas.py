from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class RiskBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: Optional[str] = None
    area: str = Field(..., max_length=100)
    severity: str = Field(default="MEDIUM")
    owner: str = Field(..., min_length=2, max_length=100)


class RiskCreate(RiskBase):
    pass


class RiskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    area: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    owner: Optional[str] = None


class RiskResponse(RiskBase):
    id: int
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DecisionCreate(BaseModel):
    risk_id: int
    reviewer: str = Field(..., min_length=2)
    decision: str = Field(..., description="APPROVED, REJECTED, NEEDS_INFO, DEFERRED")
    justification: str = Field(..., min_length=20, max_length=2000, description="Mandatory human expert rationale")
    evidence_reviewed: Optional[str] = "Standard compliance evaluation"
    confidence_level: Optional[str] = "HIGH"


class DecisionResponse(BaseModel):
    id: int
    risk_id: int
    reviewer: str
    decision: str
    justification: str
    evidence_reviewed: Optional[str] = None
    confidence_level: Optional[str] = None
    decided_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnalysisResponse(BaseModel):
    risk_id: int
    method: str
    suggested_severity: str
    completeness_score: float
    rules_fired: List[str]
    missing_fields: List[str]
    similar_decisions: List[dict]
    ai_disclaimer: str
    created_at: Optional[datetime] = None


class AuditResponse(BaseModel):
    id: int
    risk_id: int
    action: str
    actor: str
    details: Optional[str] = None
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True
