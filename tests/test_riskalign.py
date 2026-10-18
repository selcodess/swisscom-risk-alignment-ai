def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "UP"
    assert data["mode"] == "HUMAN_IN_THE_LOOP"


def test_create_and_get_risk(client):
    new_risk = {
        "title": "Customer database backup missing encryption at rest",
        "description": "Secondary analytics warehouse backup exports do not enforce server-side AES256 key management.",
        "area": "Information Security",
        "severity": "HIGH",
        "owner": "Sam Taylor",
    }
    create_res = client.post("/api/risks", json=new_risk)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["id"] is not None
    assert created_data["status"] == "PENDING"
    risk_id = created_data["id"]

    # Verify retrieval
    get_res = client.get(f"/api/risks/{risk_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == new_risk["title"]


def test_ai_decision_package_analysis(client):
    # Create risk with data breach trigger keyword
    risk_payload = {
        "title": "Suspected customer data breach on legacy proxy gateway",
        "description": "Anomaly detection identified unauthorized traffic egress to unknown external IP.",
        "area": "Information Security",
        "severity": "LOW",
        "owner": "Alex Morgan",
    }
    r = client.post("/api/risks", json=risk_payload)
    risk_id = r.json()["id"]

    # Run AI assessment
    analysis_res = client.post(f"/api/risks/{risk_id}/analyze")
    assert analysis_res.status_code == 200
    ai_data = analysis_res.json()

    # Rule engine must escalate to CRITICAL due to 'data breach' keyword
    assert ai_data["suggested_severity"] == "CRITICAL"
    assert any("R01" in rule for rule in ai_data["rules_fired"])
    assert ai_data["completeness_score"] >= 80.0
    assert "human officer" in ai_data["ai_disclaimer"].lower()


def test_human_decision_workflow_and_audit(client):
    # Create risk
    r = client.post("/api/risks", json={
        "title": "Legacy SSL certificate expiration in payment pipeline",
        "description": "TLS 1.1 root trust certificate expiring in 14 days without automatic renewal hook.",
        "area": "Operations",
        "severity": "HIGH",
        "owner": "Maya Chen",
    })
    risk_id = r.json()["id"]

    # Submit decision with mandatory justification
    decision_payload = {
        "risk_id": risk_id,
        "reviewer": "Swisscom Lead Officer",
        "decision": "APPROVED",
        "justification": "Approved emergency change window #892 for certificate replacement tonight.",
        "confidence_level": "HIGH",
    }
    dec_res = client.post("/api/decisions", json=decision_payload)
    assert dec_res.status_code == 201
    assert dec_res.json()["decision"] == "APPROVED"

    # Confirm risk status was updated
    risk_check = client.get(f"/api/risks/{risk_id}")
    assert risk_check.json()["status"] == "APPROVED"

    # Confirm audit trail captured this immutable entry
    audit_res = client.get(f"/api/audit?risk_id={risk_id}")
    assert audit_res.status_code == 200
    entries = audit_res.json()
    assert any(e["action"] == "DECISION_RECORDED" for e in entries)
