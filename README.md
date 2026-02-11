AI Resume Tailor

This is a web app I built to automatically tailor a LaTeX resume to a specific job description.

Instead of manually rewriting bullets for every application, you can paste your full LaTeX resume, paste the job description, choose the role type, and generate a revised version that stays ATS-friendly and keeps your formatting intact.

It also compiles the generated LaTeX into a downloadable PDF directly in the app (no Overleaf needed).

What it does

Takes a full LaTeX resume as input

Takes a job description

Rewrites bullets to better match the role

Extracts relevant keywords

Keeps everything formatted as a one-page resume

Lets you download the updated .tex file

Compiles and downloads a PDF using Tectonic

No resume data is stored.

Tech Stack

Frontend:

Next.js (App Router)

React

TypeScript

TailwindCSS

Backend:

Next.js API routes (Node runtime)

AI:

OpenAI Responses API with structured outputs

PDF compilation:

Tectonic (XeTeX-based LaTeX compiler)

Validation:

Zod

Setup Instructions
1. Clone the repo

git clone https://github.com/YOUR_USERNAME/ai-resume-tailor.git

cd ai-resume-tailor

2. Install dependencies

npm install

3. Install Tectonic (for PDF generation)

On Windows PowerShell:

iex ((New-Object System.Net.WebClient).DownloadString('https://drop-ps1.fullyjustified.net
'))

Make sure tectonic.exe is added to your system PATH.

Verify it works:

tectonic --version

4. Add your OpenAI API key

Create a file called:

.env.local

Add:

OPENAI_API_KEY=your_api_key_here

You can generate an API key at:
https://platform.openai.com/api-keys

Make sure billing is enabled on your OpenAI account.

5. Run the app

npm run dev

Open:

http://localhost:3000

How to use

Paste your full LaTeX resume

Paste the job description

Select the optimization track (Embedded, Hardware/Power, Software)

Click Generate

Download the tailored .tex or compiled PDF

Notes

The resume must already be valid LaTeX

Designed for single-page resumes

pdfTeX-specific commands are sanitized automatically for compatibility with Tectonic

API usage costs depend on OpenAI token usage (usually a few cents per generation)

Why I built this

Tailoring resumes for every job takes a lot of time. I wanted something that:

Keeps formatting consistent

Doesn’t break LaTeX

Stays ATS-friendly

Saves time during application season
