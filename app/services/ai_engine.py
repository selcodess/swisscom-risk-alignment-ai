from typing import List, Dict, Tuple
from app.models.entities import Risk, Decision


class RuleEngine:
    """
    Deterministic, fully explainable risk severity and compliance rule engine.
    Ensures Swisscom risk guidelines are consistently evaluated without black-box assumptions.
    """

    CRITICAL_KEYWORDS = [
        "data exposure",
        "data breach",
        "gdpr",
        "ciso",
        "unauthorized access",
        "customer pii",
        "zero-day",
        "ransomware",
    ]

    HIGH_KEYWORDS = [
        "downtime",
        "outage",
        "single supplier",
        "partner api",
        "failover",
        "audit trail",
        "unplanned",
    ]

    @classmethod
    def evaluate(cls, risk: Risk) -> Tuple[str, List[str]]:
        rules_fired: List[str] = []
        severity = "LOW"
        title_desc = f"{risk.title} {risk.description or ''}".lower()

        # Rule 1: High-impact security keywords
        for kw in cls.CRITICAL_KEYWORDS:
            if kw in title_desc:
                rules_fired.append(f"R01: Critical security phrase '{kw}' identified in risk context.")
                severity = "CRITICAL"
                break

        # Rule 2: Department-specific baseline escalation
        if risk.area == "Information Security" and severity != "CRITICAL":
            rules_fired.append("R02: Information Security domain baseline elevates minimum severity to HIGH.")
            severity = "HIGH"

        # Rule 3: Operational resiliency checks
        if severity not in ["CRITICAL", "HIGH"]:
            for kw in cls.HIGH_KEYWORDS:
                if kw in title_desc:
                    rules_fired.append(f"R03: Resiliency impact phrase '{kw}' detected.")
                    severity = "HIGH"
                    break

        # Rule 4: Vendor management risks
        if risk.area == "Vendor Management" and severity == "LOW":
            rules_fired.append("R04: Third-party dependency requires minimum MEDIUM classification.")
            severity = "MEDIUM"

        if not rules_fired:
            rules_fired.append("R05: Standard operational baseline evaluation applied.")
            severity = risk.severity or "MEDIUM"

        return severity, rules_fired


class CompletenessChecker:
    """
    Evaluates whether a risk record contains sufficient information for an executive decision.
    """

    @classmethod
    def check(cls, risk: Risk) -> Tuple[float, List[str]]:
        score = 100.0
        missing: List[str] = []

        if not risk.title or len(risk.title.strip()) < 10:
            score -= 25.0
            missing.append("Title is too brief (< 10 chars)")

        if not risk.description or len(risk.description.strip()) < 25:
            score -= 30.0
            missing.append("Missing detailed business context / impact description")

        if not risk.owner or len(risk.owner.strip()) < 3:
            score -= 20.0
            missing.append("Accountable Risk Owner not properly designated")

        if not risk.area:
            score -= 15.0
            missing.append("Business area not categorized")

        return max(0.0, score), missing


class SimilarityService:
    """
    TF-IDF Vectorizer-based similarity search over historical risk decisions.
    Runs locally on CPU with minimal RAM overhead.
    """

    @classmethod
    def find_similar(cls, target_risk: Risk, all_risks: List[Risk], all_decisions: List[Decision]) -> List[Dict]:
        if not all_risks or len(all_risks) <= 1:
            return []

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            corpus = [f"{r.title} {r.description or ''}" for r in all_risks if r.id != target_risk.id]
            target_text = [f"{target_risk.title} {target_risk.description or ''}"]

            if not corpus:
                return []

            vectorizer = TfidfVectorizer(stop_words="english")
            tfidf_matrix = vectorizer.fit_transform(corpus)
            target_vec = vectorizer.transform(target_text)

            similarities = cosine_similarity(target_vec, tfidf_matrix).flatten()

            results = []
            other_risks = [r for r in all_risks if r.id != target_risk.id]

            # Pair with past decisions
            decision_map = {d.risk_id: d for d in all_decisions}

            for idx, score in enumerate(similarities):
                if score > 0.15:  # Relevance threshold
                    r = other_risks[idx]
                    dec = decision_map.get(r.id)
                    results.append({
                        "risk_id": r.id,
                        "title": r.title,
                        "similarity_score": round(float(score) * 100, 1),
                        "past_decision": dec.decision if dec else "No formal decision recorded",
                        "past_justification": dec.justification if dec else None,
                    })

            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return results[:3]
        except Exception:
            return []
