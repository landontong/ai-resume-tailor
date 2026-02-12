import re
from typing import List


BULLET_RE = re.compile(r"\\resumeItem\{(.+?)\}", re.DOTALL)


def extract_resume_items(resume_latex: str) -> List[str]:
    """
    Extract \\resumeItem{...} bullets from your LaTeX format.
    """
    items = BULLET_RE.findall(resume_latex)
    # Normalize whitespace
    cleaned = [re.sub(r"\s+", " ", it).strip() for it in items]
    return [c for c in cleaned if c]


def strip_latex_commands(s: str) -> str:
    """
    Rough LaTeX stripper for metric scoring (good enough for heuristics).
    """
    # Remove common commands and braces
    s = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})?", " ", s)
    s = re.sub(r"[\{\}\\]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s
