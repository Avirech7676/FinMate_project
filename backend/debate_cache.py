from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class _Entry:
    expires_at: float
    value: Any


class TTLCache:
    def __init__(self, *, ttl_s: int = 900, max_items: int = 256):
        self._ttl_s = ttl_s
        self._max_items = max_items
        self._store: dict[str, _Entry] = {}

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        ent = self._store.get(key)
        if not ent:
            return None
        if ent.expires_at <= now:
            self._store.pop(key, None)
            return None
        return ent.value

    def set(self, key: str, value: Any) -> None:
        now = time.time()
        if len(self._store) >= self._max_items:
            # Drop expired first, else drop an arbitrary oldest-ish entry.
            for k in list(self._store.keys()):
                if self._store[k].expires_at <= now:
                    self._store.pop(k, None)
            if len(self._store) >= self._max_items:
                self._store.pop(next(iter(self._store.keys())), None)
        self._store[key] = _Entry(expires_at=now + self._ttl_s, value=value)

