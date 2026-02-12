import re
from typing import List, Set

# Minimal, robust keyword extraction tuned for SWE job descriptions
STOPWORDS = {
    "and","or","the","a","an","to","of","in","for","with","on","as","at","by","from",
    "be","is","are","was","were","this","that","it","their","our","you","your","we",
    "will","work","within","more","use","using","including","etc","plus"
}

# Add domain terms you want to always consider as keywords
BOOST_TERMS = {
    "fastapi","postgresql","docker","linux","git","github","jwt","oauth","rest","api",
    "typescript","react","tauri","rust","ci/cd","kubernetes","grpc","redis","alembic",
    "openapi","swagger","pytest","gtest","c++","c","python","sql","firebase"
}


def normalize_token(t: str) -> str:
    t = t.lower().strip()
    t = t.replace("c++", "cpp")
    t = t.replace("c#", "csharp")
    return t


def extract_keywords(job_description: str, max_keywords: int = 30) -> List[str]:
    """
    Extract a keyword list from the JD.
    Heuristic: keep tech-ish tokens and important phrases.
    """
    jd = job_description.lower()

    # Capture common compound phrases
    phrases = []
    for p in [
        "embedded linux", "device drivers", "real-time", "real time", "memory mapped",
        "rest api", "openapi", "unit test", "integration test", "continuous integration",
        "agile", "sprint", "jwt", "oauth", "git", "github", "docker", "postgresql",
        "c test", "g test", "gtest", "python", "c++", "linux"
    ]:
        if p in jd:
            phrases.append(p)

    # Tokenize
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9\+\#\/\.\-]{1,}", jd)
    cleaned: List[str] = []
    for tok in tokens:
        nt = normalize_token(tok)
        if nt in STOPWORDS:
            continue
        if len(nt) < 3:
            continue
        cleaned.append(nt)

    # Prefer boosted terms and phrases, then remaining tokens
    pool: List[str] = []
    pool.extend([normalize_token(p) for p in phrases])

    # Pull boosted tech terms present
    for bt in BOOST_TERMS:
        b = normalize_token(bt)
        if b in cleaned or b in jd:
            pool.append(b)

    # Add remaining unique tokens
    for t in cleaned:
        if t not in pool:
            pool.append(t)

    # Unique preserving order
    seen: Set[str] = set()
    out: List[str] = []
    for t in pool:
        if t in seen:
            continue
        seen.add(t)
        out.append(t)

    return out[:max_keywords]
