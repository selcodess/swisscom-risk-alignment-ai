from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models.entities import Risk, Decision, AuditEntry
from app.routers.api_routes import router

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Swisscom Enterprise Risk & AI Alignment Service with Human-in-the-Loop Governance",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def seed_initial_data():
    db = SessionLocal()
    try:
        if db.query(Risk).count() == 0:
            sample_risks = [
                Risk(
                    title="Customer data exposure via partner API",
                    description="External telemetry sync endpoint sends unmasked customer identifiers without strict mutual TLS validation.",
                    area="Information Security",
                    severity="CRITICAL",
                    status="PENDING",
                    owner="Alex Morgan",
                ),
                Risk(
                    title="Unplanned downtime during service migration",
                    description="Cloud gateway cluster migration lacks verified automated rollback procedures for database synchronization.",
                    area="Operations",
                    severity="HIGH",
                    status="NEEDS_INFO",
                    owner="Maya Chen",
                ),
                Risk(
                    title="Delayed vendor security assessment",
                    description="Third-party billing component provider has not renewed ISO 27001 audit report within SLA window.",
                    area="Vendor Management",
                    severity="MEDIUM",
                    status="PENDING",
                    owner="Sam Taylor",
                ),
                Risk(
                    title="Insufficient audit trail for manual approvals",
                    description="Emergency firewall rules applied during weekend incident lack secondary supervisor digital sign-off.",
                    area="Compliance",
                    severity="HIGH",
                    status="APPROVED",
                    owner="Jordan Lee",
                ),
                Risk(
                    title="Data processing dependency on one supplier",
                    description="Sole-sourced European SMS routing gateway creates concentration vulnerability during carrier failover.",
                    area="Vendor Management",
                    severity="MEDIUM",
                    status="PENDING",
                    owner="Alex Morgan",
                ),
                Risk(
                    title="Outdated internal operational runbooks",
                    description="Secondary DNS failover documentation references decommissioned monitoring consoles.",
                    area="Operations",
                    severity="LOW",
                    status="APPROVED",
                    owner="Maya Chen",
                ),
            ]
            db.add_all(sample_risks)
            db.commit()

            # Seed a sample human decision for precedent similarity matching
            dec = Decision(
                risk_id=4,
                reviewer="Jordan Lee (Security Compliance)",
                decision="APPROVED",
                justification="Emergency procedures were reviewed post-incident. Compensating controls confirmed adequate log capture.",
                evidence_reviewed="Syslog export #2026-10-12 and incident retrospective notes",
                confidence_level="HIGH",
            )
            audit = AuditEntry(
                risk_id=4,
                action="DECISION_RECORDED",
                actor="Jordan Lee",
                details="Approved with retroactive compensating logging verification.",
            )
            db.add(dec)
            db.add(audit)
            db.commit()
    finally:
        db.close()
