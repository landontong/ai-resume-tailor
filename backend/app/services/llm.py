import os
import httpx


SYSTEM_RULES = """
You are an assistant that edits LaTeX resumes for job alignment.

Hard rules:
- Do NOT invent experience, metrics, tools, or claims not supported by the original resume text.
- Preserve LaTeX validity. Do not break braces or commands.
- Prefer concrete technical specificity (tools, interfaces, constraints, validation) over vague claims.
- Avoid fluff: do not add generic collaboration/communication lines unless already present.
- Keep overall layout similar; adjust bullets and skills for alignment.
- HARD CONSTRAINT: Output must fit on ONE page when compiled to PDF.
- Do NOT add new sections. Avoid adding new bullets; prefer rewriting/condensing existing bullets.
"""

DEFAULT_INSTRUCTIONS = """
Make the resume more aligned to the job description while staying truthful.
Improve bullet specificity and add relevant keywords ONLY if supported by resume.
Ensure the output can fit on one page by keeping bullets concise.
"""

DEPTH_INSTRUCTIONS = """
Increase technical depth WITHOUT adding fluff:
- Add implementation details (interfaces, components, constraints, tools) ONLY if implied by existing resume.
- Add validation/testing language ONLY if implied (e.g., "validated", "bench", "debugged").
- Prefer specifying mechanisms over general outcomes.
- Do not add soft-skill filler.
Keep it one-page: do not increase bullet count; shorten wording if needed.
"""

TIGHTEN_INSTRUCTIONS = """
The resume exceeds one page. Tighten it to fit on ONE PAGE when compiled.

Rules:
- Do NOT add new bullets or sections.
- Prefer removing weakest/least relevant bullets first (older/less aligned).
- Shorten bullets aggressively (remove adjectives, compress clauses).
- Keep formatting/template intact (do not change margins/font sizes unless already present).
- Keep bullets to ~1 line when possible.

Return ONLY valid LaTeX from \\documentclass through \\end{document}.
Do NOT include any explanation or markdown.
"""

EXPAND_INSTRUCTIONS = """
The resume is underfilled (too much whitespace) but must remain ONE PAGE.

Rules:
- Do NOT add new experience or claims.
- You may slightly expand bullets by adding technical mechanisms, constraints, validation steps ONLY if already implied by the resume.
- Prefer improving specificity over adding new bullets.
- If adding length, do it evenly across the most relevant sections.
- Do NOT change margins/font sizes.

Return ONLY valid LaTeX from \\documentclass through \\end{document}.
"""



async def _openai_chat(prompt: str) -> str:
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    if not openai_api_key:
        raise RuntimeError("OPENAI_API_KEY missing. Set it in your environment.")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {openai_api_key}"}

    payload = {
        "model": openai_model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": SYSTEM_RULES.strip()},
            {"role": "user", "content": prompt},
        ],
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, headers=headers, json=payload)

        # If OpenAI returns an error, surface it clearly
        if r.status_code >= 400:
            try:
                err = r.json()
            except Exception:
                err = {"raw": r.text}
            raise RuntimeError(f"OpenAI error {r.status_code}: {err}")

        data = r.json()

        # Defensive parsing
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError(f"OpenAI returned no choices: {data}")

        msg = choices[0].get("message", {})
        content = msg.get("content")
        if not content:
            raise RuntimeError(f"OpenAI response missing message content: {data}")

        return content



def build_prompt(resume_latex: str, job_description: str, mode: str) -> str:
    if mode == "default":
        instructions = DEFAULT_INSTRUCTIONS
    elif mode == "increase_technical_depth":
        instructions = DEPTH_INSTRUCTIONS
    elif mode == "tighten_to_one_page":
        instructions = TIGHTEN_INSTRUCTIONS
    elif mode == "expand_to_fill_one_page":
        instructions = EXPAND_INSTRUCTIONS
    else:
        instructions = DEFAULT_INSTRUCTIONS

    # IMPORTANT: escape braces inside f-string (\\end{document} -> \\end{{document}})
    return f"""
{instructions}

Return ONLY valid LaTeX source.
You MUST include the full document from \\documentclass ... through \\end{{document}}.
Do NOT include any explanation or markdown.

=== JOB DESCRIPTION ===
{job_description}

=== ORIGINAL RESUME (LATEX) ===
{resume_latex}
""".strip()


async def generate_tailored_resume(resume_latex: str, job_description: str, mode: str) -> str:
    prompt = build_prompt(resume_latex, job_description, mode)
    latex = await _openai_chat(prompt)

    # Ensure document wrappers exist (robust)
    if "\\begin{document}" not in latex or "\\end{document}" not in latex:
        start = latex.find("\\documentclass")
        end = latex.rfind("\\end{document}")
        if start != -1 and end != -1:
            latex = latex[start:end + len("\\end{document}")]
        else:
            latex = "\\documentclass{article}\\begin{document}\n" + latex + "\n\\end{document}"

    return latex
