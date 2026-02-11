"use client";

import { useState } from "react";

type Track = "embedded" | "hardware_power" | "software";

export default function Home() {
  const [resume, setResume] = useState("");
  const [jd, setJd] = useState("");
  const [track, setTrack] = useState<Track>("embedded");
  const [loading, setLoading] = useState(false);

  const [keywords, setKeywords] = useState<string[]>([]);
  const [changes, setChanges] = useState<string[]>([]);
  const [latex, setLatex] = useState("");

  async function handleGenerate() {
    setLoading(true);
    setKeywords([]);
    setChanges([]);
    setLatex("");

    try {
      const res = await fetch("/api/tailor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_latex: resume,
          job_description: jd,
          track,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data?.error || "Request failed");

      setKeywords(data.keywords || []);
      setChanges(data.change_summary || []);
      setLatex(data.tailored_latex || "");
    } catch (e: any) {
      alert(e.message ?? "Error");
    } finally {
      setLoading(false);
    }
  }

  function downloadLatex() {
    const blob = new Blob([latex], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `tailored_resume_${track}.tex`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="mx-auto max-w-6xl p-6">
      <h1 className="text-3xl font-semibold">AI Resume Tailoring App</h1>
      <p className="mt-2 text-sm text-gray-600">
        Paste your base LaTeX resume and a job description. Get ATS keywords + a tailored full LaTeX document.
      </p>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <label className="text-sm">
          Track{" "}
          <select
            className="ml-2 rounded border px-2 py-1"
            value={track}
            onChange={(e) => setTrack(e.target.value as Track)}
          >
            <option value="embedded">Embedded / Firmware</option>
            <option value="hardware_power">Hardware / Power / Utilities</option>
            <option value="software">Software / Backend</option>
          </select>
        </label>

        <button
          className="rounded bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          onClick={handleGenerate}
          disabled={loading}
        >
          {loading ? "Generating..." : "Generate"}
        </button>

        <button
          className="rounded border px-4 py-2 text-sm disabled:opacity-50"
          onClick={downloadLatex}
          disabled={!latex}
        >
          Download .tex
        </button>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <div>
          <h2 className="text-base font-semibold">Base Resume LaTeX</h2>
          <textarea
            className="mt-2 h-[360px] w-full rounded border p-3 font-mono text-xs"
            value={resume}
            onChange={(e) => setResume(e.target.value)}
            placeholder="Paste your full LaTeX resume here..."
          />
        </div>

        <div>
          <h2 className="text-base font-semibold">Job Description</h2>
          <textarea
            className="mt-2 h-[360px] w-full rounded border p-3 font-mono text-xs"
            value={jd}
            onChange={(e) => setJd(e.target.value)}
            placeholder="Paste the job description here..."
          />
        </div>
      </div>

      <div className="mt-6">
        <h2 className="text-base font-semibold">ATS Keywords</h2>
        <div className="mt-2 flex flex-wrap gap-2">
          {keywords.map((k) => (
            <span key={k} className="rounded-full border px-3 py-1 text-xs">
              {k}
            </span>
          ))}
          {!keywords.length && <p className="text-sm text-gray-500">No keywords yet.</p>}
        </div>
      </div>

      <div className="mt-6">
        <h2 className="text-base font-semibold">Change Summary</h2>
        <ul className="mt-2 list-disc space-y-1 pl-6 text-sm">
          {changes.map((c, i) => (
            <li key={i}>{c}</li>
          ))}
          {!changes.length && <li className="text-gray-500">No changes yet.</li>}
        </ul>
      </div>

      <div className="mt-6">
        <h2 className="text-base font-semibold">Tailored LaTeX (Full)</h2>
        <textarea
          className="mt-2 h-[420px] w-full rounded border p-3 font-mono text-xs"
          value={latex}
          readOnly
          placeholder="Your tailored LaTeX will appear here..."
        />
      </div>
    </main>
  );
}
