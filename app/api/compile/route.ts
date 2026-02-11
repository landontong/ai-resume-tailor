import { NextResponse } from "next/server";
import { mkdtemp, writeFile, readFile } from "fs/promises";
import { tmpdir } from "os";
import path from "path";
import { execFile } from "child_process";
import { promisify } from "util";

// OPTIONAL: enable page count header (install pdf-lib)
// npm install pdf-lib
import { PDFDocument } from "pdf-lib";

export const runtime = "nodejs"; // IMPORTANT: needs Node runtime (not Edge)

const execFileAsync = promisify(execFile);

function sanitizeLatexForTectonic(latex: string) {
  // Tectonic uses XeTeX; pdfTeX-only commands can break compilation.
  // Strip the most common offenders in LaTeX resume templates.
  return latex
    .replaceAll("\\input{glyphtounicode}", "")
    .replaceAll("\\pdfgentounicode=1", "")
    // Some templates include these too; safe to remove for XeTeX:
    .replaceAll("\\pdfminorversion=7", "")
    .replaceAll("\\pdfobjcompresslevel=0", "");
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const latex: string = body?.latex ?? "";

    if (latex.length < 200) {
      return NextResponse.json(
        { error: "Missing LaTeX content." },
        { status: 400 }
      );
    }

    // Temp working directory
    const workDir = await mkdtemp(path.join(tmpdir(), "latex-"));
    const texPath = path.join(workDir, "resume.tex");

    // Write sanitized latex to file (IMPORTANT: do not overwrite later)
    const sanitized = sanitizeLatexForTectonic(latex);
    await writeFile(texPath, sanitized, "utf8");

    // Compile with tectonic -> outputs resume.pdf in the same directory by default
    // - No shell-escape
    await execFileAsync("tectonic", ["-X", "compile", texPath], {
      cwd: workDir,
      timeout: 30_000, // 30 seconds
      windowsHide: true,
      maxBuffer: 20 * 1024 * 1024, // increase buffer for verbose logs
    });

    const pdfPath = path.join(workDir, "resume.pdf");
    const pdf = await readFile(pdfPath);

    // OPTIONAL: page count (useful for enforcing 1-page later)
    let pageCount = 0;
    try {
      const doc = await PDFDocument.load(pdf);
      pageCount = doc.getPageCount();
    } catch {
      // If pdf-lib fails, just skip page count; PDF is still returned.
      pageCount = 0;
    }

    return new NextResponse(pdf, {
      status: 200,
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="resume.pdf"`,
        "Cache-Control": "no-store",
        ...(pageCount ? { "X-PDF-Pages": String(pageCount) } : {}),
      },
    });
  } catch (err: any) {
    console.error("PDF compile error:", err);

    // This helps you quickly see tectonic output when debugging
    const details =
      err?.stderr ||
      err?.stdout ||
      String(err?.message ?? err);

    return NextResponse.json(
      { error: "PDF compilation failed", details },
      { status: 500 }
    );
  }
}
