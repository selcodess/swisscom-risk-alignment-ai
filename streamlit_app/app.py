import streamlit as st
import requests
import json
import pandas as pd

API_BASE = "http://localhost:8000/api"

st.set_page_config(
    page_title="Swisscom RiskAlign AI",
    page_icon="◆",
    layout="wide"
)

st.title("◆ Swisscom RiskAlign AI — Governance Console")
st.markdown("Human-in-the-Loop decision intelligence platform for Swisscom enterprise risk reviews.")

# Sidebar navigation
menu = st.sidebar.radio("Navigation", ["Risk Register & Triage", "New Risk Submission", "Audit Trail & Compliance"])

try:
    health = requests.get(f"{API_BASE}/health", timeout=2).json()
    st.sidebar.success(f"● Backend Live ({health.get('mode')})")
except Exception:
    st.sidebar.warning("○ Backend Offline (Start with uvicorn app.main:app)")

if menu == "Risk Register & Triage":
    st.subheader("Monitored Risks")
    
    try:
        res = requests.get(f"{API_BASE}/risks")
        if res.status_code == 200:
            risks = res.json()
            df = pd.DataFrame(risks)
            if not df.empty:
                st.dataframe(
                    df[["id", "title", "area", "severity", "status", "owner"]],
                    use_container_width=True
                )
                
                selected_id = st.selectbox("Select Risk for AI Decision Package & Human Review", df["id"].tolist())
                selected_risk = next(r for r in risks if r["id"] == selected_id)
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.write("### Risk Context")
                    st.write(f"**Title:** {selected_risk['title']}")
                    st.write(f"**Area:** {selected_risk['area']}")
                    st.write(f"**Current Severity:** {selected_risk['severity']}")
                    st.write(f"**Current Status:** {selected_risk['status']}")
                    st.write(f"**Owner:** {selected_risk['owner']}")
                    st.info(f"**Description:** {selected_risk.get('description') or 'No description logged.'}")
                    
                    if st.button("Generate AI Decision Package", type="primary"):
                        ai_res = requests.post(f"{API_BASE}/risks/{selected_id}/analyze")
                        if ai_res.status_code == 200:
                            st.session_state[f"ai_{selected_id}"] = ai_res.json()
                
                with col2:
                    st.write("### AI Advisory Package")
                    ai_data = st.session_state.get(f"ai_{selected_id}")
                    if ai_data:
                        st.metric("Completeness Score", f"{ai_data['completeness_score']}%")
                        st.write(f"**Suggested Severity:** `{ai_data['suggested_severity']}` (via `{ai_data['method']}`)")
                        
                        st.write("**Rules Evaluated:**")
                        for r in ai_data["rules_fired"]:
                            st.write(f"- {r}")
                            
                        st.warning(f"⚠️ {ai_data['ai_disclaimer']}")
                    else:
                        st.write("Click *Generate AI Decision Package* to inspect explainable guidelines.")

                st.write("---")
                st.write("### ✍️ Record Human Decision")
                with st.form("decision_form"):
                    dec_type = st.selectbox("Decision", ["APPROVED", "REJECTED", "NEEDS_INFO", "DEFERRED"])
                    reviewer = st.text_input("Reviewer Name / Title", value="Senior Risk Reviewer")
                    justification = st.text_area("Mandatory Written Justification (min 20 chars)", placeholder="Explain reasoning based on evidence reviewed...")
                    submitted = st.form_submit_button("Sign & Submit Human Decision")
                    
                    if submitted:
                        if len(justification.strip()) < 20:
                            st.error("Justification must contain at least 20 characters for compliance.")
                        else:
                            post_data = {
                                "risk_id": selected_id,
                                "reviewer": reviewer,
                                "decision": dec_type,
                                "justification": justification
                            }
                            dec_post = requests.post(f"{API_BASE}/decisions", json=post_data)
                            if dec_post.status_code == 201:
                                st.success(f"Decision '{dec_type}' formally recorded in immutable audit ledger!")
                                st.rerun()
            else:
                st.info("No risks currently in database.")
    except Exception as e:
        st.error(f"Unable to query backend: {e}")

elif menu == "New Risk Submission":
    st.subheader("Submit New Risk Record")
    with st.form("new_risk"):
        title = st.text_input("Risk Title", placeholder="e.g. Unauthenticated webhook endpoint detected")
        area = st.selectbox("Business Domain", ["Information Security", "Operations", "Compliance", "Vendor Management"])
        severity = st.selectbox("Initial Severity", ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        owner = st.text_input("Accountable Risk Owner", placeholder="Full Name")
        desc = st.text_area("Impact Description & Scope", placeholder="Describe affected systems, potential data exposure or business loss...")
        create_btn = st.form_submit_button("Log Risk")
        
        if create_btn:
            if not title or not owner:
                st.warning("Title and Owner are mandatory.")
            else:
                payload = {"title": title, "area": area, "severity": severity, "owner": owner, "description": desc}
                try:
                    res = requests.post(f"{API_BASE}/risks", json=payload)
                    if res.status_code == 201:
                        st.success("Risk created and logged to audit trail!")
                except Exception as e:
                    st.error(f"Error creating risk: {e}")

elif menu == "Audit Trail & Compliance":
    st.subheader("Immutable Audit Ledger")
    try:
        audit_res = requests.get(f"{API_BASE}/audit")
        if audit_res.status_code == 200:
            entries = audit_res.json()
            if entries:
                st.dataframe(pd.DataFrame(entries)[["id", "risk_id", "actor", "action", "details", "timestamp"]], use_container_width=True)
            else:
                st.info("No audit events recorded yet.")
    except Exception as e:
        st.error(f"Error loading audit trail: {e}")
