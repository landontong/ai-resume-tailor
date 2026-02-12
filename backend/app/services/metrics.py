from typing import List, Tuple
from rapidfuzz import fuzz

from .text_extract import extract_resume_items, strip_latex_commands
from .keywords import extract_keywords


# Heuristic vocab for "technical specificity"
TECH_MARKERS = {
    "implemented","designed","built","integrated","debugged","validated","tested","deployed",
    "docker","linux","kernel","driver","fastapi","postgresql","jwt","oauth","alembic","openapi",
    "api","rest","ci","cd","pipeline","cache","rate","limit","schema","migration","auth",
    "memory","mapped","interrupt","timer","latency","throughput","gdb","gcc","clang"
}

VALIDATION_MARKERS = {
    "test","tested","testing","validated","verification","benchmark","unit","integration","regression",
    "coverage","assert","gtest","pytest","ci"
}

SOFT_FLUFF = {
    "collaborated","cross-functional","stakeholders","communication","team","worked with"
}


def keyword_alignment(resume_text: str, jd_keywords: List[str]) -> Tuple[float, List[str], List[str]]:
    """
    Compute % of JD keywords present in resume (approx match).
    We use fuzzy matching to account for variations.
    """
    r = resume_text.lower()
    matched = []
    missing = []

    for kw in jd_keywords:
        k = kw.lower().strip()
        if not k:
            continue

        # direct contain for phrases
        if " " in k and k in r:
            matched.append(kw)
            continue

        # fuzzy check token-level
        score = fuzz.partial_ratio(k, r)
        if score >= 90:
            matched.append(kw)
        else:
            missing.append(kw)

    total = max(1, len(jd_keywords))
    pct = (len(matched) / total) * 100.0
    return round(pct, 1), matched, missing


def redundancy_level(bullets: List[str]) -> str:
    """
    Simple redundancy: average pairwise similarity between bullets.
    """
    if len(bullets) < 2:
        return "Low"

    sims = []
    for i in range(len(bullets)):
        for j in range(i + 1, len(bullets)):
            sims.append(fuzz.token_set_ratio(bullets[i], bullets[j]))

    avg = sum(sims) / max(1, len(sims))

    # Higher similarity means more redundancy
    if avg >= 70:
        return "High"
    if avg >= 55:
        return "Med"
    return "Low"


def technical_specificity_level(bullets: List[str]) -> str:
    """
    Rate bullets based on presence of technical markers and validation markers,
    while penalizing pure fluff.
    """
    if not bullets:
        return "Low"

    scores = []
    for b in bullets:
        low = b.lower()
        tech = sum(1 for w in TECH_MARKERS if w in low)
        val = sum(1 for w in VALIDATION_MARKERS if w in low)
        fluff = sum(1 for w in SOFT_FLUFF if w in low)
        scores.append(tech + val - fluff)

    avg = sum(scores) / len(scores)

    if avg >= 2.0:
        return "High"
    if avg >= 0.8:
        return "Med"
    return "Low"


def signal_density_score(bullets: List[str]) -> float:
    """
    Score 0-10. Each bullet can contribute points for:
      - tool/tech presence
      - constraints/precision (numbers, units)
      - validation/testing
      - architecture/system terms
    This is deliberately heuristic and stable.
    """
    if not bullets:
        return 0.0

    total = 0
    max_per = 4

    for b in bullets:
        low = b.lower()
        pts = 0

        # Tool/tech terms
        if any(t in low for t in TECH_MARKERS):
            pts += 1

        # Constraints / specificity: numbers, units, protocols, or key system words
        if any(ch.isdigit() for ch in low) or any(x in low for x in ["latency","throughput","ms","hz","kb","mb","gb","%","ax i","can","ethernet","tcp","udp"]):
            pts += 1

        # Validation/testing
        if any(t in low for t in VALIDATION_MARKERS):
            pts += 1

        # Architecture terms
        if any(t in low for t in ["schema","migration","driver","kernel","device","api","rate limit","auth","ownership","memory-mapped","interrupt","pipeline"]):
            pts += 1

        total += min(max_per, pts)

    score_10 = (total / (len(bullets) * max_per)) * 10.0
    return round(score_10, 1)


def compute_metrics(resume_latex: str, job_description: str):
    bullets = extract_resume_items(resume_latex)
    bullets_plain = [strip_latex_commands(b) for b in bullets]
    jd_keys = extract_keywords(job_description)

    resume_plain = strip_latex_commands(resume_latex)
    word_count = len(resume_plain.split())

    ka, matched, missing = keyword_alignment(resume_plain, jd_keys)
    sd = signal_density_score(bullets_plain)
    red = redundancy_level(bullets_plain)
    spec = technical_specificity_level(bullets_plain)

    avg_len = round(sum(len(b.split()) for b in bullets_plain) / max(1, len(bullets_plain)), 1)

    return {
        "signal_density": sd,
        "technical_specificity": spec,
        "keyword_alignment": ka,
        "redundancy": red,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "bullet_count": len(bullets_plain),
        "avg_bullet_length": avg_len,
        "word_count": word_count,
    }

def length_score(resume_plain: str) -> int:
    # crude proxy; tune threshold on your template
    return len(resume_plain.split())

