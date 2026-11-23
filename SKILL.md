---
name: offload-to-chatgpt
description: Decide when a task should go to ChatGPT/Codex (or Gemini, for watching videos) instead of Claude to save Claude usage, and how to hand it off cheaply. Use before starting bulk, mechanical or long-running work, and whenever someone sends a video link to understand.
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

## Videos: hand them to Gemini, don't screenshot them
Claude can't watch a video, and pulling frames into Claude costs usage and misses the audio. Gemini watches
the whole video (picture and sound) and returns a timestamped breakdown as text. Use it whenever someone sends
a video link and wants it understood, summarised or copied as a technique.

**YouTube links (public videos only):** Gemini takes the link directly, nothing is downloaded.
- With the Gemini API CLI (github.com/google-gemini/gemini-api-cli, Apache-2.0, open beta, flags can change):
  `gemini-api analyze -i "<YouTube link>" "<question>"`. Repeat `-i` for several videos (up to 10 per request).
- Without the CLI (any machine with `curl` and the key, e.g. a cloud session):
  ```
  curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent" \
    -H "x-goog-api-key: $GEMINI_API_KEY" -H "Content-Type: application/json" \
    -d '{"contents":[{"parts":[{"file_data":{"file_uri":"<YouTube link>"}},{"text":"<question>"}]}]}'
  ```
  The answer is at `candidates[0].content.parts[*].text`.

**TikTok, Instagram and other links:** Gemini only takes YouTube links directly. Download the clip in a remote
sandbox (Composio's workbench: `pip install yt-dlp`, then `yt-dlp -o v.mp4 --write-info-json <link>`), read the
caption from the info JSON (many "how to" clips put the full steps there), and if the picture or speech still
matters, upload the file through the Gemini Files API and ask the same question. Never use the person's own
browser or computer to watch media they send.

**The breakdown prompt** (paste as the question, trim to what's needed):
> Break down this video second by second. 1) The hook: what is said and shown in 0-3 s, and why it stops the
> scroll. 2) Every cut or scene change with its MM:SS timestamp and what changes. 3) All on-screen text with
> timestamps. 4) Where attention is most likely to drop, and why. 5) The call to action: what, when, how it's
> phrased. 6) Three things I can repeat in my own video.

For a technique video ask instead: "List the exact steps, tools, commands and settings shown or said, with MM:SS
timestamps, and anything shown on screen but not said."

**Setup (once):** a free key from Google AI Studio (aistudio.google.com/apikey). Keep it out of files and
prompts: `gemini-api configure --api-key <key>` on a workstation (OS keychain), or an environment secret named
`GEMINI_API_KEY` for cloud sessions. The CLI installer doesn't verify a checksum; prefer the binary from the
repo's GitHub Releases. Composio's Gemini instant account can't do this (text-only, and generate-content isn't
on it), so the person's own key is needed.

**Limits and privacy:** free tier covers up to 8 hours of YouTube video a day. On the free tier Google may use
what you send to improve its products, so send public videos only, never private recordings, client material or
anything with personal details. Spot-check one timestamp against the video before relying on a breakdown.

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
| "I'll grab a few frames and guess the rest" | Frames miss the audio and the cuts; send the video to Gemini for a timestamped breakdown. |
| "The caption is enough" | Often it is (check it first), but if steps are only shown on screen, run the breakdown. |

## Lessons
- 2026-11-21: the TikTok that started this was a Theo clip about a model auditing another
  model's unmerged work and saying "this is fine, merge it". Useful lesson: a quick outside
  audit can end over-iteration. It did not describe a ChatGPT routing setup.
- 2026-11-23: a TikTok showed giving Claude Code "eyes" with Google's Gemini API CLI: paste a YouTube link, get
  a breakdown by timestamps. Added the "Videos" section. Its full steps were in the caption, read via yt-dlp's
  info JSON in Composio's workbench, which is the cheap first check for any clip.
