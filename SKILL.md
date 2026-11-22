---
name: offload-to-chatgpt
description: Decide when a task should go to ChatGPT/Codex instead of Claude to save Claude usage, and how to hand it off cheaply. Use before starting bulk, mechanical or long-running work.
---

# Offload to ChatGPT

Goal: spend Claude usage on judgement (design, critique, skills, the site) and push bulk or
mechanical work to the person's ChatGPT plan.

## The rule that matters most
Only offload when the handoff is cheaper than doing the work. Driving the ChatGPT desktop app
by screenshots costs more Claude usage than most tasks it would replace (every screenshot is
read by Claude). Hand off by **command line**, not by clicking:

1. **Codex CLI, signed in with the ChatGPT account** (preferred). Uses the ChatGPT plan's
   allowance, no API bill. One line from Claude, results come back as files:
   `codex exec --skip-git-repo-check --full-auto -C <folder> "<task>. Write the result to <file>." </dev/null`
   Always add `</dev/null`: without it `codex exec` waits on "Reading additional input from stdin...".
   Default sandbox is read-only; `--full-auto` lets it write inside `-C <folder>` only.
   Runs on the person's computer (Remote Control session) or any machine where Codex is signed in.
   Check sign-in with `codex login status` ("Logged in using ChatGPT").
2. **OpenAI API key** (pay per use, needs the person's OK and a spending cap). Use for scripted
   bulk jobs from the cloud: captioning, tagging, summarising hundreds of items.
3. **ChatGPT app by hand**: only for one-off things the person does themselves. Claude writes
   the prompt, the person pastes it.

## Send to ChatGPT/Codex
- Bulk image captioning, alt text, tagging, file renaming plans.
- Summarising long transcripts, PDFs, email threads, research dumps.
- First drafts of boilerplate text (product descriptions, listings) that Claude then edits once.
- Simple standalone scripts, converters, data cleanup, CSV/JSON wrangling.
- Repetitive code changes across many files with a clear spec and a test to prove them.
- Second-opinion audits ("is this done? what's actually missing?") to stop endless polishing.

## Keep with Claude
- Design judgement, critique, the make-and-check loop, clipping checks, the taste guide.
- Skills and their self-improvement, project memory, ETA logging.
- The person's website pages (brand theme, check loop, PR and merge).
- Anything private (legal/LLC, client case files, personal data) unless the person OKs it.
- Anything that needs this project's tools (Drive backups, render farm, Blender, GitHub).

## How to hand off
- Give one self-contained brief: inputs (paths), exact output file and format, done-criteria.
- Batch: one call for 200 captions, not 200 calls.
- Claude checks a sample of the output (not all of it) and fixes the brief if it's off.
- Never paste secrets or private data into the brief.

## Cost notes (check current prices before quoting)
- A free ChatGPT account ran Codex jobs with no plan or limit message (tested 2026-11-22, a
  trivial job used ~7k tokens). Free limits are tighter; if a job reports a usage limit, stop
  and ask the person about Plus instead of retrying.
- ChatGPT Plus/Pro includes Codex usage with higher limits; no per-task bill.
- API: small models cost cents per thousand captions/summaries; set a monthly cap first.

## Setup (once per machine)
- Install: `npm install -g @openai/codex` (or `brew install codex` where Homebrew exists).
  Keep npm cache and temp files where the person wants scratch files (e.g. an external drive).
- Sign in: `codex login` → "Sign in with ChatGPT" in the browser. A saved login in `~/.codex` is reused.
- Smoke test: `codex exec --skip-git-repo-check "Reply with exactly: CODEX OK" </dev/null`.

## Excuses that don't count
| Excuse | Why it doesn't count |
|---|---|
| "It's quicker to just do it myself" | For bulk work it isn't cheaper; the point is saving Claude usage. |
| "I'll drive the ChatGPT app with screenshots" | Each screenshot costs Claude usage; use the CLI. |
| "Codex output looked fine at a glance" | Spot-check a sample against the done-criteria before using it. |

## Lessons
- 2026-11-21: the TikTok that started this was a Theo clip about a model auditing another
  model's unmerged work and saying "this is fine, merge it". Useful lesson: a quick outside
  audit can end over-iteration. It did not describe a ChatGPT routing setup.
