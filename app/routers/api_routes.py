from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.database import get_db
from app.models.entities import Risk, Decision, Analysis, AuditEntry
from app.schemas.risk_schemas import (
    RiskCreate,
    RiskUpdate,
    RiskResponse,
    DecisionCreate,
    DecisionResponse,
    AnalysisResponse,
    AuditResponse,
)
from app.services.ai_engine import RuleEngine, CompletenessChecker, SimilarityService
from app.services.gemini_service import GeminiAdvisor
from app.config import settings

router = APIRouter(prefix="/api", tags=["Risk Management & Governance"])


# 1. Risks CRUD
@router.get("/risks", response_model=List[RiskResponse])
def get_risks(
    status: Optional[str] = None,
    area: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Risk)
    if status:
        query = query.filter(Risk.status == status.upper())
    if area:
        query = query.filter(Risk.area == area)
    return query.order_by(Risk.id.desc()).all()


@router.post("/risks", response_model=RiskResponse, status_code=201)
def create_risk(risk_in: RiskCreate, db: Session = Depends(get_db)):
    risk = Risk(
        title=risk_in.title,
        description=risk_in.description,
        area=risk_in.area,
        severity=risk_in.severity.upper(),
        owner=risk_in.owner,
        status="PENDING",
    )
    db.add(risk)
    db.commit()
    db.refresh(risk)

    # Log audit entry
    audit = AuditEntry(
        risk_id=risk.id,
        action="RISK_CREATED",
        actor=risk.owner,
        details=f"Initial registration in {risk.area} with severity {risk.severity}"
    )
    db.add(audit)
    db.commit()

    return risk


@router.get("/risks/{risk_id}", response_model=RiskResponse)
def get_risk(risk_id: int, db: Session = Depends(get_db)):
    risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk record not found")
    return risk


@router.put("/risks/{risk_id}", response_model=RiskResponse)
def update_risk(risk_id: int, update_in: RiskUpdate, db: Session = Depends(get_db)):
    risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk record not found")

    update_data = update_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if val is not None:
            setattr(risk, field, val.upper() if field in ["severity", "status"] else val)

    db.commit()
    db.refresh(risk)

    audit = AuditEntry(
        risk_id=risk.id,
        action="RISK_UPDATED",
        actor="Human Reviewer",
        details=f"Fields modified: {', '.join(update_data.keys())}"
    )
    db.add(audit)
    db.commit()

    return risk


@router.delete("/risks/{risk_id}", status_code=204)
def delete_risk(risk_id: int, db: Session = Depends(get_db)):
    risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk record not found")

    db.delete(risk)
    db.commit()

    audit = AuditEntry(
        risk_id=risk_id,
        action="RISK_DELETED",
        actor="System Admin",
        details=f"Risk #{risk_id} removed by administrator."
    )
    db.add(audit)
    db.commit()
    return None


# 2. AI Decision Package & Analysis
@router.post("/risks/{risk_id}/analyze", response_model=AnalysisResponse)
def analyze_risk(risk_id: int, db: Session = Depends(get_db)):
    risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk record not found")

    all_risks = db.query(Risk).all()
    all_decisions = db.query(Decision).all()

    # 1. Deterministic rules
    suggested_severity, rules_fired = RuleEngine.evaluate(risk)

    # 2. Completeness check
    score, missing = CompletenessChecker.check(risk)

    # 3. TF-IDF Similarity
    similar = SimilarityService.find_similar(risk, all_risks, all_decisions)

    # 4. Optional Gemini advisor
    gemini_res = GeminiAdvisor.analyze_second_opinion(risk.title, risk.description or "", risk.area)
    method = "GEMINI_ASSISTED" if gemini_res else "RULE_BASED"
    if gemini_res:
        rules_fired.append(f"Gemini Advisor Comment: {gemini_res['advisor_comment']}")

    analysis = Analysis(
        risk_id=risk.id,
        method=method,
        suggested_severity=suggested_severity,
        completeness_score=score,
        rules_fired=json.dumps(rules_fired),
        missing_fields=json.dumps(missing),
        similar_decisions=json.dumps(similar),
        ai_disclaimer="AI outputs are decision-support suggestions only. Final determination rests with the accountable human officer.",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return AnalysisResponse(
        risk_id=analysis.risk_id,
        method=analysis.method,
        suggested_severity=analysis.suggested_severity,
        completeness_score=analysis.completeness_score,
        rules_fired=rules_fired,
        missing_fields=missing,
        similar_decisions=similar,
        ai_disclaimer=analysis.ai_disclaimer,
        created_at=analysis.created_at,
    )


# 3. Human Decisions
@router.post("/decisions", response_model=DecisionResponse, status_code=201)
def submit_decision(decision_in: DecisionCreate, db: Session = Depends(get_db)):
    risk = db.query(Risk).filter(Risk.id == decision_in.risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Target risk not found")

    decision = Decision(
        risk_id=decision_in.risk_id,
        reviewer=decision_in.reviewer,
        decision=decision_in.decision.upper(),
        justification=decision_in.justification,
        evidence_reviewed=decision_in.evidence_reviewed,
        confidence_level=decision_in.confidence_level or "HIGH",
    )
    db.add(decision)

    # Update risk status matching decision
    status_map = {
        "APPROVED": "APPROVED",
        "REJECTED": "REJECTED",
        "NEEDS_INFO": "NEEDS_INFO",
        "DEFERRED": "PENDING",
    }
    risk.status = status_map.get(decision.decision, "PENDING")

    # Record immutable audit entry
    audit = AuditEntry(
        risk_id=risk.id,
        action="DECISION_RECORDED",
        actor=decision.reviewer,
        details=f"Human review sign-off: {decision.decision}. Justification: {decision.justification[:60]}..."
    )
    db.add(audit)
    db.commit()
    db.refresh(decision)

    return decision


@router.get("/decisions/risk/{risk_id}", response_model=List[DecisionResponse])
def get_decisions_for_risk(risk_id: int, db: Session = Depends(get_db)):
    return db.query(Decision).filter(Decision.risk_id == risk_id).order_by(Decision.id.desc()).all()


# 4. Audit Trail
@router.get("/audit", response_model=List[AuditResponse])
def get_audit_trail(risk_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(AuditEntry)
    if risk_id:
        query = query.filter(AuditEntry.risk_id == risk_id)
    return query.order_by(AuditEntry.id.desc()).all()


# 5. Health Check
@router.get("/health")
def health_check():
    return {
        "status": "UP",
        "service": "swisscom-risk-alignment-ai",
        "mode": "HUMAN_IN_THE_LOOP",
        "gemini_active": bool(settings.gemini_api_key),
    }
