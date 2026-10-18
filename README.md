# Swisscom RiskAlign AI — Decision Intelligence & Governance

[![CI/CD Pipeline](https://github.com/selca/swisscom-risk-alignment-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/selca/swisscom-risk-alignment-ai/actions)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-1.38-FF4B4B?logo=streamlit)
![License](https://img.shields.io/badge/License-Proprietary_Swisscom_Portfolio-blue)

An explainable, human-in-the-loop AI risk assessment service designed for Swisscom compliance governance. Evaluates risk completeness, applies transparent rule engines, searches historical decision precedents, and formats structured decision packages while leaving all binding final decisions exclusively in human hands.

---

## 💡 Key Architectural Safeguards

1. **Deterministic Rule Engine First**: Evaluates keywords and departmental baselines deterministically without requiring external API keys.
2. **Transparent Decision Packages**: Outputs the exact rule IDs (`R01`-`R05`) and completeness factors contributing to each recommendation.
3. **TF-IDF Decision Similarity**: Compares incoming risks with historical decisions to maintain institutional consistency.
4. **Mandatory Human Justification**: Requires human reviewers to enter a defensible rationale before updating risk status.
5. **Immutable Audit Ledger**: Records all changes, actors, and decisions in persistent database storage.

---

## 🚀 Quick Start (Lightweight, No Docker Required)

### 1. Start the FastAPI REST Backend (Port 8000)
```powershell
cd C:\Users\selca\Projects\swisscom-risk-alignment-ai
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
# API Docs (Swagger UI): http://127.0.0.1:8000/docs
```

### 2. Launch the Streamlit Governance UI (Port 8501)
```powershell
cd C:\Users\selca\Projects\swisscom-risk-alignment-ai
streamlit run streamlit_app/app.py
# Dashboard: http://localhost:8501
```

---

## 🧪 Automated Testing

Run the automated pytest test suite covering API contracts, rule triggers, completeness checks, and audit logging:

```powershell
pytest -v
```
