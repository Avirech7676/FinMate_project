from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Optional, Iterable

from schemas import OfferOut, OfferProvider


@dataclass(frozen=True)
class ProviderResult:
    provider: OfferProvider
    offers: list[OfferOut]
    error: Optional[str] = None


class OfferProviderAdapter(Protocol):
    name: OfferProvider

    async def search(
        self,
        *,
        query: str,
        max_results: int,
        location: Optional[str] = None,
        timeout_s: float = 4.0,
    ) -> ProviderResult: ...


def _dedupe_offers(offers: Iterable[OfferOut]) -> list[OfferOut]:
    seen: set[tuple[str, str]] = set()
    out: list[OfferOut] = []
    for o in offers:
        key = (o.provider, (o.title or "").strip().lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(o)
    return out

