from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import models
import utils

class SpendingAnalytics:
    """Deterministic calculations for spending patterns, category shares, and trends."""

    @staticmethod
    def compute_spending_summary(transactions: List[models.Transaction]) -> Dict[str, Any]:
        if not transactions:
            return {
                "total_spent": 0.0,
                "transaction_count": 0,
                "average_transaction": 0.0,
                "highest_transaction": None,
                "category_breakdown": {},
                "top_merchants": []
            }

        total = 0.0
        by_category = defaultdict(float)
        by_merchant = defaultdict(float)
        highest_txn: Optional[models.Transaction] = None

        for t in transactions:
            amt = float(t.amount or 0.0)
            total += amt
            cat = (t.category or "other").strip().lower()
            by_category[cat] += amt
            m_key = utils.normalize_merchant_key(t.description or "")
            by_merchant[m_key] += amt

            if highest_txn is None or amt > highest_txn.amount:
                highest_txn = t

        count = len(transactions)
        avg = round(total / count, 2) if count > 0 else 0.0

        top_merchants = [
            {"merchant": k.title() if k and k != "unknown" else "Other", "amount": round(v, 2)}
            for k, v in sorted(by_merchant.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        return {
            "total_spent": round(total, 2),
            "transaction_count": count,
            "average_transaction": avg,
            "highest_transaction": {
                "transaction_id": highest_txn.transaction_id,
                "amount": round(highest_txn.amount, 2),
                "category": highest_txn.category,
                "description": highest_txn.description,
                "date": highest_txn.date.isoformat() if highest_txn.date else None
            } if highest_txn else None,
            "category_breakdown": {k: round(v, 2) for k, v in by_category.items()},
            "top_merchants": top_merchants
        }

    @staticmethod
    def compute_monthly_comparison(
        current_txns: List[models.Transaction],
        prior_txns: List[models.Transaction]
    ) -> Dict[str, Any]:
        curr_total = sum(float(t.amount or 0) for t in current_txns)
        prior_total = sum(float(t.amount or 0) for t in prior_txns)

        diff = curr_total - prior_total
        pct_change = 0.0
        if prior_total > 0:
            pct_change = round((diff / prior_total) * 100, 2)

        curr_by_cat = defaultdict(float)
        for t in current_txns:
            curr_by_cat[(t.category or "other").lower()] += float(t.amount or 0)

        prior_by_cat = defaultdict(float)
        for t in prior_txns:
            prior_by_cat[(t.category or "other").lower()] += float(t.amount or 0)

        all_cats = set(curr_by_cat.keys()) | set(prior_by_cat.keys())
        cat_deltas = []
        for cat in all_cats:
            c_val = curr_by_cat[cat]
            p_val = prior_by_cat[cat]
            delta = c_val - p_val
            pct = round((delta / p_val) * 100, 1) if p_val > 0 else 100.0 if c_val > 0 else 0.0
            cat_deltas.append({
                "category": cat,
                "current_amount": round(c_val, 2),
                "prior_amount": round(p_val, 2),
                "difference": round(delta, 2),
                "percentage_change": pct
            })

        cat_deltas.sort(key=lambda x: abs(x["difference"]), reverse=True)

        return {
            "current_month_total": round(curr_total, 2),
            "prior_month_total": round(prior_total, 2),
            "net_difference": round(diff, 2),
            "percentage_change": pct_change,
            "category_comparisons": cat_deltas
        }
