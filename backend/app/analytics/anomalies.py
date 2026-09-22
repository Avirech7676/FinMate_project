import math
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np
import models

@dataclass
class AnomalyResult:
    transaction_id: int
    anomaly_score: float  # 0.0 to 1.0
    severity: str        # "low", "medium", "high"
    level: str           # "rule", "statistical", "ml"
    reason: str
    evidence: Dict[str, Any]

class LayeredAnomalyDetector:
    """
    3-Tier Anomaly Detection Engine:
    - Level 1: Deterministic Rule-Based Thresholds
    - Level 2: Statistical Outliers (Z-score, IQR)
    - Level 3: Machine Learning (Isolation Forest)
    """

    @classmethod
    def detect_anomalies(
        cls,
        transactions: List[models.Transaction],
        monthly_income: float = 0.0
    ) -> List[AnomalyResult]:
        if len(transactions) < 5:
            return []

        anomalies: List[AnomalyResult] = []
        anom_tx_ids = set()

        # Group amounts by category
        by_cat = defaultdict(list)
        for t in transactions:
            amt = float(t.amount or 0.0)
            if amt > 0:
                by_cat[(t.category or "other").lower()].append((t, amt))

        # --- LEVEL 1: RULE-BASED THRESHOLDS ---
        for cat, items in by_cat.items():
            if len(items) < 3:
                continue
            cat_median = float(np.median([x[1] for x in items]))
            for t, amt in items:
                # Rule 1: Single purchase > 3x category median and >= $150
                if cat_median > 0 and amt >= 3.0 * cat_median and amt >= 150.0:
                    if t.transaction_id not in anom_tx_ids:
                        anom_tx_ids.add(t.transaction_id)
                        anomalies.append(AnomalyResult(
                            transaction_id=t.transaction_id,
                            anomaly_score=round(min(1.0, (amt / (3.0 * cat_median)) * 0.7), 2),
                            severity="high" if amt > 500.0 else "medium",
                            level="rule",
                            reason=f"Spending of ${amt:.2f} is more than 3x your typical {cat} median (${cat_median:.2f}).",
                            evidence={
                                "amount": amt,
                                "category": cat,
                                "category_median": round(cat_median, 2),
                                "multiplier": round(amt / cat_median, 2),
                                "description": t.description
                            }
                        ))

        # --- LEVEL 2: STATISTICAL DETECTION (Z-Score & IQR) ---
        for cat, items in by_cat.items():
            if len(items) < 5:
                continue
            amounts = np.array([x[1] for x in items])
            mean = float(np.mean(amounts))
            std = float(np.std(amounts))
            q25, q75 = float(np.percentile(amounts, 25)), float(np.percentile(amounts, 75))
            iqr = q75 - q25
            iqr_upper = q75 + 1.5 * iqr

            for t, amt in items:
                if t.transaction_id in anom_tx_ids:
                    continue
                z_score = ((amt - mean) / std) if std > 0 else 0.0
                is_z_outlier = z_score >= 2.5
                is_iqr_outlier = (amt > iqr_upper) and (amt >= 2.0 * mean) and (amt >= 100.0)

                if is_z_outlier or is_iqr_outlier:
                    anom_tx_ids.add(t.transaction_id)
                    score = min(1.0, max(0.5, (z_score / 4.0))) if is_z_outlier else 0.65
                    severity = "high" if z_score >= 3.0 or amt > 500.0 else "medium"
                    anomalies.append(AnomalyResult(
                        transaction_id=t.transaction_id,
                        anomaly_score=round(score, 2),
                        severity=severity,
                        level="statistical",
                        reason=f"Statistically abnormal {cat} transaction (Z-score: {z_score:.2f}, IQR threshold: ${iqr_upper:.2f}).",
                        evidence={
                            "amount": amt,
                            "category": cat,
                            "mean": round(mean, 2),
                            "std": round(std, 2),
                            "z_score": round(z_score, 2),
                            "iqr_upper_bound": round(iqr_upper, 2),
                            "description": t.description
                        }
                    ))

        # --- LEVEL 3: MACHINE LEARNING (Isolation Forest) ---
        if len(transactions) >= 15:
            try:
                from sklearn.ensemble import IsolationForest
                # Feature engineering: [amount, day_of_week, day_of_month]
                features = []
                valid_txns = []
                for t in transactions:
                    if t.transaction_id in anom_tx_ids:
                        continue
                    amt = float(t.amount or 0.0)
                    dt = t.date or t.created_at
                    dow = dt.weekday() if dt else 0
                    dom = dt.day if dt else 15
                    features.append([amt, dow, dom])
                    valid_txns.append(t)

                if len(features) >= 10:
                    X = np.array(features)
                    iso = IsolationForest(contamination=0.03, random_state=42)
                    preds = iso.fit_predict(X)
                    raw_scores = iso.decision_function(X)

                    for idx, pred in enumerate(preds):
                        raw_s = float(raw_scores[idx])
                        if pred == -1 and raw_s < -0.04:  # Confident Multidimensional Anomaly
                            t = valid_txns[idx]
                            raw_s = float(raw_scores[idx])
                            normalized_score = round(min(1.0, max(0.4, 1.0 - (raw_s + 0.5))), 2)
                            anom_tx_ids.add(t.transaction_id)
                            anomalies.append(AnomalyResult(
                                transaction_id=t.transaction_id,
                                anomaly_score=normalized_score,
                                severity="medium",
                                level="ml",
                                reason="Machine learning model (Isolation Forest) flagged atypical multidimensional spending pattern.",
                                evidence={
                                    "amount": float(t.amount),
                                    "category": t.category,
                                    "description": t.description,
                                    "isolation_forest_decision_score": round(raw_s, 4)
                                }
                            ))
            except Exception:
                pass  # Graceful fallback if scikit-learn is unavailable or fails

        # Sort by anomaly score descending
        anomalies.sort(key=lambda x: x.anomaly_score, reverse=True)
        return anomalies
