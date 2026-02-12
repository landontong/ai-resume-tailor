from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import TailorRequest, TailorResponse, TailorResult, Metrics
from .services.llm import generate_tailored_resume
from .services.metrics import compute_metrics
from .services.pdf_compile import compile_latex_to_pdf_bytes, count_pdf_pages

import os
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"  # backend/.env
load_dotenv(dotenv_path=ENV_PATH)

print("OPENAI_API_KEY loaded:", bool(os.getenv("OPENAI_API_KEY")))
print("OPENAI_MODEL:", os.getenv("OPENAI_MODEL"))


app = FastAPI(title="AI Resume Tailor Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


def passes_require_regen(metrics: dict, req: TailorRequest) -> bool:
    return (
        metrics["signal_density"] < req.min_signal_density
        or metrics["keyword_alignment"] < req.min_keyword_alignment
    )


def choose_best(results: list[TailorResult]) -> TailorResult:
    def score(r: TailorResult) -> float:
        red_penalty = 0.0
        if r.metrics.redundancy == "High":
            red_penalty = 0.8
        elif r.metrics.redundancy == "Med":
            red_penalty = 0.3
        return (r.metrics.keyword_alignment * 0.65) + (r.metrics.signal_density * 3.5) - red_penalty

    return sorted(results, key=score, reverse=True)[0]


@app.post("/tailor", response_model=TailorResponse)
async def tailor(req: TailorRequest):
    try:
        all_results: list[TailorResult] = []

        decision = {
            "ran_second_pass": False,
            "reason": None,
            "thresholds": {
                "min_signal_density": req.min_signal_density,
                "min_keyword_alignment": req.min_keyword_alignment,
            },
            "page_limit": 1,
            "page_count": None,
            "tighten_attempts": 0,
        }

        # PASS 1 (default)
        mode1 = "default"
        latex1 = await generate_tailored_resume(req.resume_latex, req.job_description, mode=mode1)

        # Enforce one-page by compile + count + tighten loop
        pages_limit = 1
        tighten_attempts_max = 2
        latex_current = latex1
        last_good_latex = latex_current
        pages_current = None

        for attempt in range(0, tighten_attempts_max + 1):
            # attempt=0 means compile original pass1; attempt>=1 means tightened versions
            try:
                pdf_bytes = compile_latex_to_pdf_bytes(latex_current)
                pages_current = count_pdf_pages(pdf_bytes)
                last_good_latex = latex_current
            except Exception as e:
                # If a tightened output breaks compilation, revert and stop tightening
                latex_current = last_good_latex
                decision["reason"] = f"Compile failed during tighten attempt {attempt}: {str(e)[:200]}"
                break

            if pages_current <= pages_limit:
                break

            # Too many pages → tighten
            decision["tighten_attempts"] = attempt + 1
            latex_current = await generate_tailored_resume(
                latex_current,
                req.job_description,
                mode="tighten_to_one_page",
            )

        decision["page_count"] = pages_current

        MIN_WORDS = 600
        MAX_EXPAND_ATTEMPTS = 1

        from .services.text_extract import strip_latex_commands

        # Always try to expand if underfilled (but only if we fit on 1 page)
        if pages_current == 1:
            resume_plain = strip_latex_commands(latex_current)
            word_count = len(resume_plain.split())

            if word_count < MIN_WORDS:
                for _ in range(MAX_EXPAND_ATTEMPTS):
                    latex_try = await generate_tailored_resume(
                        latex_current,
                        req.job_description,
                        mode="expand_to_fill_one_page",
                    )

                    try:
                        pdf_try = compile_latex_to_pdf_bytes(latex_try)
                        if count_pdf_pages(pdf_try) == 1:
                            latex_current = latex_try
                            decision["expanded_to_fill"] = True
                        else:
                            break
                    except Exception:
                        break

        # PASS 1: Compute metrics on the final latex_current (after tighten/expand)
        latex1 = latex_current
        m1 = compute_metrics(latex1, req.job_description)

        r1 = TailorResult(
            pass_index=1,
            mode=mode1,
            tailored_resume_latex=latex1,
            metrics=Metrics(**m1),
        )
        all_results.append(r1)

        # PASS 2 (conditional technical depth)
        mode2 = "default"  # default fallback
        if req.max_passes >= 2 and passes_require_regen(m1, req):
            decision["ran_second_pass"] = True
            decision["reason"] = "Below thresholds; regenerating with increase_technical_depth mode."

            mode2 = "increase_technical_depth"
            latex2 = await generate_tailored_resume(req.resume_latex, req.job_description, mode=mode2)

            # Enforce one-page for pass 2 as well
            latex_current = latex2
            last_good_latex = latex_current
            pages_current = None

            for attempt in range(0, tighten_attempts_max + 1):
                try:
                    pdf_bytes = compile_latex_to_pdf_bytes(latex_current)
                    pages_current = count_pdf_pages(pdf_bytes)
                    last_good_latex = latex_current
                except Exception:
                    latex_current = last_good_latex
                    break

                if pages_current <= pages_limit:
                    break

                latex_current = await generate_tailored_resume(
                    latex_current,
                    req.job_description,
                    mode="tighten_to_one_page",
                )

            latex2 = latex_current
            m2 = compute_metrics(latex2, req.job_description)

            r2 = TailorResult(
                pass_index=2,
                mode=mode2,
                tailored_resume_latex=latex2,
                metrics=Metrics(**m2),
            )
            all_results.append(r2)

        best = choose_best(all_results)

        return TailorResponse(
            best=best,
            all_passes=all_results,
            decision=decision,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
