import { NextResponse } from "next/server";
import OpenAI from "openai";
import { TailorResultSchema } from "@/lib/schema";

type Track = "embedded" | "hardware_power" | "software";

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export async function POST(req: Request) {
  try {
    if (!process.env.OPENAI_API_KEY) {
      return NextResponse.json(
        { error: "Missing OPENAI_API_KEY. Add it to .env.local and restart `npm run dev`." },
        { status: 500 }
      );
    }

    const body = await req.json();
    const resume_latex: string = body.resume_latex ?? "";
    const job_description: string = body.job_description ?? "";
    const track: Track = body.track ?? "embedded";

    if (resume_latex.length < 200 || job_description.length < 100) {
      return NextResponse.json(
        { error: "Please provide your full LaTeX resume and a job description." },
        { status: 400 }
      );
    }

    const trackHints: Record<Track, string> = {
      embedded:
        "Optimize for embedded/firmware: C/C++, RTOS/real-time, drivers, board bring-up, debugging, CAN, FPGA SoCs.",
      hardware_power:
        "Optimize for engineering designer / electrical design / power distribution: CAD-style design language, schematics/PCB layout, documentation, power integrity/load analysis, field/customer communication, learn GIS/CAD quickly.",
      software:
        "Optimize for software: APIs, backend, testing, CI, reliability, metrics. ATS-friendly.",
    };

    const system = `
You are an expert engineering resume writer.

HARD CONSTRAINTS (must follow):
- The output MUST compile to exactly ONE page on US Letter (8.5x11).
- If content would overflow, you MUST shorten bullets (not margins), remove least relevant bullets, and/or compress wording.
- Keep margins and font size exactly as in the provided LaTeX template.
- Keep total bullets per role/project to a maximum of 4 unless explicitly instructed otherwise.
- Prefer: numbers/metrics, short phrases, remove adjectives.

Rules:
- Do NOT invent any employers, degrees, dates, tools, or achievements.
- Output a FULL LaTeX document that compiles.
- Preserve formatting and structure; make targeted edits (keywords, bullet wording, ordering).
- Keep it one page.
- Add ATS keywords naturally.

Track guidance:
${trackHints[track]}

Output MUST be valid JSON matching the provided JSON schema.
`;

    const resp = await client.responses.create({
      model: "gpt-5.2",
      input: [
        { role: "system", content: system },
        {
          role: "user",
          content: `RESUME_LATEX:\n${resume_latex}\n\nJOB_DESCRIPTION:\n${job_description}`,
        },
      ],
      text: {
        format: {
          type: "json_schema",
          name: "tailor_result",
          schema: {
            type: "object",
            additionalProperties: false,
            properties: {
              keywords: { type: "array", items: { type: "string" } },
              change_summary: { type: "array", items: { type: "string" } },
              tailored_latex: { type: "string" }
            },
            required: ["keywords", "change_summary", "tailored_latex"]
          }
        }
      }
    });

    const rawText = resp.output_text;

    let parsed: unknown;
    try {
      parsed = JSON.parse(rawText);
    } catch {
      return NextResponse.json(
        { error: "Model returned non-JSON output. Try again.", raw: rawText },
        { status: 502 }
      );
    }

    const result = TailorResultSchema.safeParse(parsed);
    if (!result.success) {
      return NextResponse.json(
        { error: "JSON did not match expected schema.", details: result.error.flatten(), raw: parsed },
        { status: 502 }
      );
    }

    return NextResponse.json(result.data);
  } catch (err: any) {
    console.error("Tailor route error:", err);
    const msg = err?.message || err?.error?.message || "Unknown error (check terminal logs).";
    const status = typeof err?.status === "number" ? err.status : 500;
    return NextResponse.json({ error: "Tailoring failed", details: msg }, { status });
  }
}
