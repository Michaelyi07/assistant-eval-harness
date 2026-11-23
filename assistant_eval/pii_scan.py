"""PII gate: regex scan for CN mobile numbers (incl. separator variants) and emails.

The gate runs over every string field of every corpus item; any hit is a hard
failure (AC1). Synthetic names are covered by the same gate because the corpus
must not contain any mobile/email-shaped strings at all.
"""

from __future__ import annotations

import re
from typing import Any, Iterable

# CN mobile: 1[3-9] + 9 digits (11 total), with optional separators (- space .)
# between the 3-4-4 digit groups.
CN_MOBILE = re.compile(
    r"(?<!\d)1[3-9]\d[\s\-\.]?(\d{4})[\s\-\.]?(\d{4})(?!\d)"
)
# RFC-lite email: local@domain.tld (no spaces, common TLD length 2-24).
EMAIL = re.compile(
    r"(?<![\w\.\-])[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,24}(?![\w\-])"
)

PATTERNS = {"cn_mobile": CN_MOBILE, "email": EMAIL}


def _iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield k
            yield from _iter_strings(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from _iter_strings(v)


def scan_item(item: dict) -> list[dict]:
    """Scan one corpus item; return list of hits {field_path_kind, pattern, match}."""
    hits: list[dict] = []
    for s in _iter_strings(item):
        for name, pat in PATTERNS.items():
            for m in pat.finditer(s):
                hits.append({"pattern": name, "match": m.group(0)})
    return hits


def scan_corpus(items: list[dict]) -> list[dict]:
    """Scan a whole corpus; return hits with item ids."""
    out: list[dict] = []
    for item in items:
        for hit in scan_item(item):
            out.append({"item_id": item.get("id"), **hit})
    return out
