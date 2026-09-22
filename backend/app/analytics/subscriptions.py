import hashlib
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import numpy as np
import models
import utils

@dataclass
class SubscriptionCandidate:
    candidate_id: str
    merchant: str
    amount: float
    frequency: str  # "monthly", "weekly", "quarterly", "annual", "bi-weekly"
    interval_days: int
    occurrences: int
    confidence: float  # 0.0 to 1.0
    annualized_cost: float
    last_seen_at: datetime
    category: str

class SubscriptionIntelligenceEngine:
    """
    Deterministic Recurring & Subscription Detection Engine.
    Analyzes merchant similarity, amount proximity, interval variance, and frequency.
    """

    @classmethod
    def detect_subscriptions(
        cls,
        transactions: List[models.Transaction],
        user_id: int = 0,
        decisions: Optional[Dict[str, str]] = None
    ) -> List[SubscriptionCandidate]:
        if len(transactions) < 3:
            return []

        decisions_map = decisions or {}

        # Group transactions by normalized merchant key
        merchant_groups = defaultdict(list)
        for t in transactions:
            if not t.amount or t.amount <= 0 or not t.date:
                continue
            m_key = utils.normalize_merchant_key(t.description or "")
            if m_key and m_key != "unknown":
                merchant_groups[m_key].append(t)

        candidates: List[SubscriptionCandidate] = []

        for m_key, tx_list in merchant_groups.items():
            if len(tx_list) < 2:
                continue

            # Sort ascending by date
            sorted_txns = sorted(tx_list, key=lambda x: x.date)
            intervals = []
            for i in range(1, len(sorted_txns)):
                diff = (sorted_txns[i].date - sorted_txns[i - 1].date).days
                if diff > 0:
                    intervals.append(diff)

            if not intervals:
                continue

            median_interval = float(np.median(intervals))
            amounts = [float(t.amount) for t in sorted_txns]
            avg_amount = float(np.mean(amounts))
            amt_std = float(np.std(amounts))

            # Determine frequency class
            freq = "irregular"
            base_days = 30
            if 5 <= median_interval <= 9:
                freq = "weekly"
                base_days = 7
            elif 12 <= median_interval <= 16:
                freq = "bi-weekly"
                base_days = 14
            elif 25 <= median_interval <= 35:
                freq = "monthly"
                base_days = 30
            elif 80 <= median_interval <= 100:
                freq = "quarterly"
                base_days = 90
            elif 340 <= median_interval <= 390:
                freq = "annual"
                base_days = 365

            if freq == "irregular" and len(sorted_txns) < 3:
                continue

            # Compute interval variance penalty
            interval_var = float(np.std(intervals)) if len(intervals) > 1 else 0.0
            var_penalty = min(0.4, (interval_var / max(1.0, median_interval)) * 0.5)

            # Amount consistency penalty (amounts within 15% get high confidence)
            amt_var_penalty = min(0.3, (amt_std / avg_amount) * 0.5) if avg_amount > 0 else 0.5

            # Base confidence
            base_conf = 0.5 + min(0.35, len(sorted_txns) * 0.08)
            final_conf = max(0.2, min(1.0, base_conf - var_penalty - amt_var_penalty))

            # Annualized cost calculation
            annualized = 0.0
            if freq == "weekly":
                annualized = avg_amount * 52.0
            elif freq == "bi-weekly":
                annualized = avg_amount * 26.0
            elif freq == "monthly" or freq == "irregular":
                annualized = avg_amount * 12.0
            elif freq == "quarterly":
                annualized = avg_amount * 4.0
            elif freq == "annual":
                annualized = avg_amount

            # Candidate ID
            cid = utils.make_candidate_id(user_id, m_key)
            last_txn = sorted_txns[-1]

            candidates.append(SubscriptionCandidate(
                candidate_id=cid,
                merchant=last_txn.description or m_key.title(),
                amount=round(avg_amount, 2),
                frequency=freq,
                interval_days=int(round(median_interval)),
                occurrences=len(sorted_txns),
                confidence=round(final_conf, 2),
                annualized_cost=round(annualized, 2),
                last_seen_at=last_txn.date,
                category=(last_txn.category or "utilities").lower()
            ))

        # Sort by annualized cost descending
        candidates.sort(key=lambda x: x.annualized_cost, reverse=True)
        return candidates
