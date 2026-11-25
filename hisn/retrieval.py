"""Offline runbook search: small BM25 over hisn/data/runbooks/*.md."""
from __future__ import annotations

import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

RUNBOOK_DIR = Path(__file__).parent / "data" / "runbooks"
_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = {"a", "an", "the", "of", "on", "in", "to", "and", "or", "is", "for", "with", "by", "at", "as", "from"}


def _stem(w: str) -> str:
    for suf in ("ing", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)]
    return w


def _tokens(text: str) -> list[str]:
    return [_stem(w) for w in _TOKEN.findall(text.lower()) if w not in _STOP]


def _parse(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    meta, body = {}, raw
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", raw, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip().lower()] = v.strip().strip("'\"")
        body = m.group(2)
    rid = meta.get("id") or path.stem
    title = meta.get("title") or rid
    snippet = " ".join(body.split())[:200]
    # title counts three times so it outweighs body text
    toks = _tokens(title) * 3 + _tokens(body)
    return {"id": rid, "title": title, "snippet": snippet, "tf": Counter(toks), "len": len(toks)}


@lru_cache(maxsize=1)
def _index() -> dict:
    docs = [_parse(p) for p in sorted(RUNBOOK_DIR.glob("*.md"))]
    n = len(docs)
    df: Counter = Counter()
    for d in docs:
        df.update(d["tf"].keys())
    avg = (sum(d["len"] for d in docs) / n) if n else 1.0
    idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
    return {"docs": docs, "idf": idf, "avg": avg or 1.0}


def search_runbooks(query: str, k: int = 3) -> list[dict]:
    if not isinstance(query, str) or not query.strip():
        return []
    try:
        k = int(k)
    except (TypeError, ValueError):
        k = 3
    k = max(1, min(10, k))
    idx = _index()
    q = _tokens(query)
    k1, b = 1.5, 0.75
    out = []
    for d in idx["docs"]:
        s = 0.0
        for t in set(q):
            f = d["tf"].get(t, 0)
            if f:
                s += idx["idf"].get(t, 0.0) * f * (k1 + 1) / (f + k1 * (1 - b + b * d["len"] / idx["avg"]))
        out.append({"id": d["id"], "title": d["title"], "snippet": d["snippet"], "score": round(s, 6)})
    out.sort(key=lambda r: (-r["score"], r["id"]))
    return out[:k]
