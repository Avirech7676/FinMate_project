from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Iterable

import google.generativeai as genai

import schemas


@dataclass(frozen=True)
class ScoredOffer:
    offer: schemas.OfferOut
    score: float


_PROVIDER_TRUST: dict[str, float] = {
    "amazon": 0.90,
    "flipkart": 0.85,
    "bigbasket": 0.82,
    "blinkit": 0.80,
    "zepto": 0.80,
}


def _score_offers(offers: Iterable[schemas.OfferOut], priority: schemas.DebatePriority) -> list[ScoredOffer]:
    offers = list(offers)
    prices = [o.price for o in offers if o.price is not None and o.price > 0]
    min_price = min(prices) if prices else None

    scored: list[ScoredOffer] = []
    for o in offers:
        trust = _PROVIDER_TRUST.get(o.provider, 0.7)
        price_score = 0.0
        if min_price and o.price and o.price > 0:
            # Cheaper -> closer to 1.0
            price_score = max(0.0, min(1.0, min_price / o.price))

        eta_score = 0.0
        if o.delivery_eta_minutes is not None:
            # Lower ETA better; normalize roughly within 0..180 minutes
            eta_score = max(0.0, min(1.0, 1.0 - (o.delivery_eta_minutes / 180.0)))

        # Priority weighting
        if priority == "cheapest":
            score = 0.70 * price_score + 0.20 * trust + 0.10 * eta_score
        elif priority == "fastest":
            score = 0.60 * eta_score + 0.25 * trust + 0.15 * price_score
        else:
            score = 0.55 * price_score + 0.25 * trust + 0.20 * eta_score

        # Penalize missing price a bit so we prefer verifiable offers
        if o.price is None:
            score *= 0.75

        scored.append(ScoredOffer(offer=o, score=round(score, 4)))

    scored.sort(key=lambda x: x.score, reverse=True)
    return scored


def _templated_debate(
    *,
    query: str,
    priority: schemas.DebatePriority,
    chosen: Optional[schemas.OfferOut],
    top_offers: list[ScoredOffer],
) -> schemas.DebateOut:
    chosen_line = (
        f"Pick: {chosen.provider.title()} — {chosen.title} at {chosen.currency} {chosen.price}."
        if (chosen and chosen.price is not None)
        else (f"Pick: {chosen.provider.title()} — {chosen.title}." if chosen else "Pick: none (not enough priced offers).")
    )

    frugal = (
        f"Focus on keeping cost low for '{query}'. {chosen_line} "
        f"If you buy today, set a hard cap and avoid add-ons."
    )
    value = (
        "Prefer an offer with a clear price and a reliable provider. "
        "If the cheapest listing looks ambiguous, choose the next-best priced option from a trusted provider."
    )
    convenience = (
        "If you need it immediately, prioritize fast delivery and availability. "
        "If delivery time is unknown, confirm on checkout before deciding."
    )
    referee = (
        f"Recommendation ({priority}): {chosen_line} "
        "Verify at checkout and consider delaying 24 hours if this is a want, not a need."
    )

    return schemas.DebateOut(
        query=query,
        priority=priority,
        offers=[s.offer for s in top_offers],
        chosen_offer=chosen,
        confidence=0.65 if chosen else 0.35,
        roles=[
            schemas.DebateRoleOut(role="FrugalCoach", text=frugal),
            schemas.DebateRoleOut(role="ValueAnalyst", text=value),
            schemas.DebateRoleOut(role="ConvenienceAdvocate", text=convenience),
            schemas.DebateRoleOut(role="Referee", text=referee),
        ],
        final_recommendation=referee,
    )


def _ai_debate(
    *,
    gemini_api_key: str,
    query: str,
    priority: schemas.DebatePriority,
    chosen: Optional[schemas.OfferOut],
    offers: list[schemas.OfferOut],
    user_context: str,
) -> Optional[list[schemas.DebateRoleOut]]:
    if not gemini_api_key:
        return None

    # genai is configured in main.py globally; still guard if called independently.
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
    except Exception:
        return None

    offers_compact = []
    for o in offers[:10]:
        offers_compact.append(
            {
                "provider": o.provider,
                "title": o.title,
                "price": o.price,
                "currency": o.currency,
                "eta_min": o.delivery_eta_minutes,
                "url": o.url,
            }
        )

    prompt = f"""
You are a 4-role panel debating whether/where to buy a product.\n
Return ONLY valid JSON with keys: roles (array of 4 objects: role, text).\n
Roles must be exactly: FrugalCoach, ValueAnalyst, ConvenienceAdvocate, Referee.\n
Keep each role text <= 80 words. Be specific.\n
User query: {query}\n
Priority: {priority}\n
Chosen offer (deterministic): {chosen.model_dump() if chosen else None}\n
Offers: {offers_compact}\n
User context: {user_context}\n
"""
    try:
        resp = model.generate_content(prompt)
        raw = (resp.text or "").replace("```json", "").replace("```", "").strip()
        import json

        data = json.loads(raw)
        roles = data.get("roles") or []
        out: list[schemas.DebateRoleOut] = []
        for r in roles:
            role = r.get("role")
            text = r.get("text")
            if role in {"FrugalCoach", "ValueAnalyst", "ConvenienceAdvocate", "Referee"} and isinstance(text, str):
                out.append(schemas.DebateRoleOut(role=role, text=text.strip()))
        if len(out) == 4:
            return out
    except Exception:
        return None

    return None


def run_debate(
    *,
    gemini_api_key: str,
    query: str,
    priority: schemas.DebatePriority,
    offers: list[schemas.OfferOut],
    user_context: str = "",
) -> schemas.DebateOut:
    scored = _score_offers(offers, priority)
    chosen = scored[0].offer if scored else None

    base = _templated_debate(query=query, priority=priority, chosen=chosen, top_offers=scored[:25])
    ai_roles = _ai_debate(
        gemini_api_key=gemini_api_key,
        query=query,
        priority=priority,
        chosen=chosen,
        offers=[s.offer for s in scored[:25]],
        user_context=user_context,
    )
    if ai_roles:
        base.roles = ai_roles
        referee = next((r.text for r in ai_roles if r.role == "Referee"), None)
        if referee:
            base.final_recommendation = referee
        base.confidence = 0.75 if chosen else 0.35
    return base


def pick_recommended_offer(offers: list[schemas.OfferOut], priority: schemas.DebatePriority) -> Optional[schemas.OfferOut]:
    scored = _score_offers(offers, priority)
    return scored[0].offer if scored else None

