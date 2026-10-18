from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from app.database import Base


class Risk(Base):
    __tablename__ = "risks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    area = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False, default="MEDIUM")
    status = Column(String(50), nullable=False, default="PENDING")
    owner = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    risk_id = Column(Integer, ForeignKey("risks.id"), nullable=False)
    reviewer = Column(String(100), nullable=False)
    decision = Column(String(50), nullable=False)  # APPROVED, REJECTED, NEEDS_INFO, DEFERRED
    justification = Column(Text, nullable=False)
    evidence_reviewed = Column(Text, nullable=True)
    confidence_level = Column(String(50), default="HIGH")
    decided_at = Column(DateTime(timezone=True), server_default=func.now())


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    risk_id = Column(Integer, ForeignKey("risks.id"), nullable=False)
    method = Column(String(50), nullable=False)  # RULE_BASED, GEMINI_ASSISTED
    suggested_severity = Column(String(50), nullable=False)
    completeness_score = Column(Float, nullable=False)
    rules_fired = Column(Text, nullable=True)  # JSON string
    missing_fields = Column(Text, nullable=True)  # JSON string
    similar_decisions = Column(Text, nullable=True)  # JSON string
    ai_disclaimer = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditEntry(Base):
    __tablename__ = "audit_entries"

    id = Column(Integer, primary_key=True, index=True)
    risk_id = Column(Integer, nullable=False)
    action = Column(String(100), nullable=False)
    actor = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
