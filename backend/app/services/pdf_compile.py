from __future__ import annotations

import io
import subprocess
import tempfile
from pathlib import Path
from pypdf import PdfReader


def compile_latex_to_pdf_bytes(latex: str) -> bytes:
    """
    Compile LaTeX to PDF using tectonic and return PDF bytes.

    Requirements:
      - `tectonic` installed and available on PATH.
    """
    with tempfile.TemporaryDirectory() as td:
        workdir = Path(td)
        tex_path = workdir / "resume.tex"
        tex_path.write_text(latex, encoding="utf-8")

        # Compile in a temp directory
        cmd = ["tectonic", str(tex_path), "--outdir", str(workdir)]
        proc = subprocess.run(
            cmd,
            cwd=str(workdir),
            capture_output=True,
            text=True,
        )

        if proc.returncode != 0:
            raise RuntimeError(
                "PDF compile failed.\n"
                f"STDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}"
            )

        pdf_path = workdir / "resume.pdf"
        if not pdf_path.exists():
            raise RuntimeError("PDF compile failed: resume.pdf not produced.")

        return pdf_path.read_bytes()


def count_pdf_pages(pdf_bytes: bytes) -> int:
    """
    Count pages in a PDF byte string.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return len(reader.pages)
