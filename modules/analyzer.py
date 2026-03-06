from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ContradictionFinding:
    statement_a: str
    statement_b: str
    reason: str


_SENT_SPLIT = re.compile(r"(?<=[。！？.!?])\s+|\n+")


def _sentences(text: str) -> list[str]:
    items = [s.strip() for s in _SENT_SPLIT.split(text) if s and s.strip()]
    # avoid very short fragments
    return [s for s in items if len(s) >= 6]


def analyze_contradictions(text: str) -> dict:
    """
    Minimal contradiction analysis (rule-based).

    This is a placeholder analyzer: it looks for obvious negation pairs
    around the same key phrase across nearby sentences.
    """
    sents = _sentences(text)
    findings: list[ContradictionFinding] = []

    # Very lightweight heuristic: if two sentences share a long common substring
    # and one contains negation keywords while the other doesn't.
    neg = ("不", "无", "未", "没有", "并非", "否认", "not ", "no ", "never ")

    def has_neg(s: str) -> bool:
        low = s.lower()
        return any(k in s for k in neg) or any(k in low for k in (" not ", " no ", " never "))

    for i in range(len(sents)):
        a = sents[i]
        for j in range(i + 1, min(i + 8, len(sents))):
            b = sents[j]
            # quick overlap check
            common = _longest_common_key(a, b)
            if len(common) < 10:
                continue
            if has_neg(a) ^ has_neg(b):
                findings.append(
                    ContradictionFinding(
                        statement_a=a,
                        statement_b=b,
                        reason=f"Possible negation conflict on key phrase: {common!r}",
                    )
                )

    return {
        "sentences": len(sents),
        "findings": [
            {"a": f.statement_a, "b": f.statement_b, "reason": f.reason} for f in findings
        ],
    }


def _longest_common_key(a: str, b: str) -> str:
    """
    Return a representative common substring (not necessarily optimal),
    focusing on longer CJK/word sequences.
    """
    a2 = _normalize(a)
    b2 = _normalize(b)
    if not a2 or not b2:
        return ""

    # Take candidate n-grams from a and find first long one existing in b.
    # Keep it cheap: scan decreasing lengths.
    max_len = min(24, len(a2))
    for L in range(max_len, 9, -1):
        for start in range(0, len(a2) - L + 1, 2):
            sub = a2[start : start + L]
            if sub in b2:
                return sub
    return ""


def _normalize(s: str) -> str:
    s = re.sub(r"\s+", " ", s.strip())
    s = re.sub(r"[\"'“”‘’]", "", s)
    return s

