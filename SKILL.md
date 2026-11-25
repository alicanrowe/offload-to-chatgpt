---
name: offload-to-chatgpt
description: Route every task to the cheapest model that can do it well (the Hive) - Haiku scouts for checks, Sonnet builders for routine edits, Opus as Queen Bee for design and judgement, Codex and Gemini as neighbouring hives for offloaded coding, bulk work, videos and second opinions. Use before starting any task, delegating, or starting a thread.
---

# The Hive: route each task to the right model

Goal: spend the expensive model only on judgement. Everything else goes to a cheaper bee or out of the hive.
Industry practice (RouteLLM, FrugalGPT, Claude Code's own `opusplan`, multi-agent coding write-ups, 2026) says
the same three things: **route by task type before you start** (cheap), **cascade** (try cheap, escalate only
when a check fails), and **have a different model review the work than the one that wrote it**.

## The hive
| Bee | Model | Gets | Never gets |
|---|---|---|---|
| **Queen Bee** | Claude Opus (this thread) | Design, critique, taste, the make-and-check loop, plans, final say on anything the owner sees, skills, memory | Mechanical work it could hand down |
| **Scouts** | Claude Haiku | Tower/render watching, render QA against a checklist, clipping-report reading, private-data scans, link checks, log triage, file inventories, "did X land" checks | Design calls, anything it would have to judge by taste |
| **Builders** | Claude Sonnet | Routine edits with a clear spec: page copy swaps, front-matter fixes, renames across files, script fixes with a failing test, README updates | Open-ended design, the final check |
| **Neighbouring hive: Codex** | OpenAI Codex CLI on the owner's ChatGPT login | Standalone scripts, converters, bulk refactors with a test, data wrangling, a second-opinion code review | Private data, anything needing this project's tools (Drive, GitHub, Blender MCP) |
| **Neighbouring hive: Gemini** | Gemini API (the owner's key) | Videos (only model that watches them), very long docs/logs (1M context), bulk summaries, a cheap second opinion on a plan or text | Private data (free tier may train on it), final design calls |

Think "three goldfish and one elephant": many cheap, short-memory bees each get one self-contained job and
a file to write; the Queen keeps the long memory and only reads their result files.

## Routing rules
1. **Before starting**, name the bee for each step. If a step is mechanical and has a pass/fail check, it is not
   the Queen's.
2. **Hand down with a brief, get back a file.** Brief = inputs (paths), the exact output file and format,
   done-criteria. The bee writes the result file; the Queen reads that file, not the bee's whole transcript.
3. **Cascade, don't guess.** Scout first; escalate to a Builder (or the Queen) only when the scout's check fails
   or it reports it is unsure. Twice-failed fix: send it to a different model, not the same one again.
4. **Cross-review.** Code a Builder or Codex wrote gets a quick review by a different model before merge;
   a design the Queen made gets Gemini or Codex as a second opinion only when the owner is about to spend money.
5. **Batch.** One call for 200 captions, not 200 calls. Up to 10 YouTube links per Gemini request.
6. **Keep private things in the hive.** LLC, client files, logins, personal data stay with Claude. Before
   sending files out, strip keys, `.env` contents and personal details from what you pass.
7. **Weigh the second opinion, don't obey it.** Outside models confidently invent problems (Gemini's first review
   of this skill claimed Codex's own ChatGPT login breaks OpenAI's terms; it doesn't). Keep what you can verify.
8. **Log it.** Note the model and time of each offload in the thread's checklist or the ETA skill baselines.

## How a thread calls each bee
- **Scout / Builder (inside Claude Code):** the Agent tool with `model: "haiku"` or `model: "sonnet"`
  (`subagent_type: "general-purpose"`). Pass the brief; ask for a short report and write findings to a file.
  The built-in `Explore` agent is already a cheap read-only searcher. Check the subagent really ran on the
  asked model (some builds ignored the field); if `CLAUDE_CODE_SUBAGENT_MODEL` is set it can override it.
  Outside an agent tool: `claude -p --model haiku "<brief>" > out.md`.
- **Where Codex and Gemini run:** on the home server ("tower", Windows side, job folder `C:\offload\`), so the
  owner's laptop stays free. Threads can't reach the tower directly: send the job brief to the coordinator to
  relay to the tower's thread, with inputs in the job folder and the answer written to a file there. The
  laptop (via Remote Control) is the fallback when the tower is offline. The tower only needs Codex signed in and `GEMINI_API_KEY` set as a user variable there.
- **Codex:** `codex exec --skip-git-repo-check --full-auto -C <folder> -o <answer.md> "<brief>" </dev/null`
  (on Windows cmd, `< NUL`) on a machine where `codex login status` says "Logged in using ChatGPT".
  For a headless machine, sign in with `codex login --device-auth`: it prints a URL and a code the owner enters
  on any device.
  Claude Code's auto mode on the Mac blocks `codex exec` unless a permission rule allows it (`Bash(codex exec:*)`
  in the Mac's Claude Code settings). Claude can't add that rule itself, even with the owner's OK (it would be
  loosening its own permissions): the owner adds it once in `~/.claude/settings.json` under permissions.allow.
  `-o` writes only Codex's final message to the file. Details below.
- **Gemini (text, files, images, PDFs):** `. <private key file>` then
  `python3 scripts/ask_gemini.py -o answer.md -f input.txt "<brief>"`. It falls back across flash models on
  404/429/503 and prints the model, time and tokens. Videos: see "Videos" below.
- **Switching the thread's own model** (`switch_model`, effort level) is only on the owner's words. A thread
  started on Opus stays on Opus; save usage by handing work down, not by switching.

## Project default and coordinator rule
- Default model for threads: **Opus**, because most threads here end in design judgement the owner sees.
  Exception: a thread whose whole job is mechanical (tower watching, storage cleanup, link fixes, backups)
  can be started on **Sonnet** if the coordinator is able to pick the model; otherwise the Opus thread hands
  the steps down to Haiku/Sonnet agents.
- Coordinator: when starting a thread, write the bee for each step into the brief ("watch the tower with a
  Haiku agent; Codex writes the converter; you do the design pass").

# Offload outside Claude: Codex and Gemini

## The rule that matters most
Only offload when the handoff is cheaper than doing the work. Driving the ChatGPT desktop app
by screenshots costs more Claude usage than most tasks it would replace (every screenshot is
read by Claude). Hand off by **command line**, not by clicking:

1. **Codex CLI, signed in with the ChatGPT account** (preferred). Uses the ChatGPT plan's
   allowance, no API bill. One line from Claude, results come back as files:
   `codex exec --skip-git-repo-check --full-auto -C <folder> -o <answer.md> "<task>. Write the result to <file>." </dev/null`
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
  curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent" \
    -H "x-goog-api-key: $GEMINI_API_KEY" -H "Content-Type: application/json" \
    -d '{"contents":[{"parts":[{"file_data":{"file_uri":"<YouTube link>"}},{"text":"<question>"}]}]}'
  ```
  The answer is at `candidates[0].content.parts[*].text`. Models change often: new keys can't use
  `gemini-2.5-flash` (404), and the newest flash model can return 503 "high demand". On either, list the models
  (`GET .../v1beta/models`) and try the next flash model down. `gemini-3.5-flash` worked on 2026-11-24.
  Add `--max-time 120`; a busy model can hang for minutes.

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
`GEMINI_API_KEY` for cloud sessions (or a private key file the session sources, never inside a skill folder). The CLI installer doesn't verify a checksum; prefer the binary from the
repo's GitHub Releases. Composio's Gemini instant account can't do this (text-only, and generate-content isn't
on it), so the person's own key is needed.

**Many videos (a whole channel):** the free tier also caps requests, about 20 per model per day (429
"GenerateRequestsPerDayPerProjectPerModel-FreeTier"; tested 2026-11-25, it hit after 14 long tutorials). Up to
10 YouTube links fit in one request, which helps for shorts. For dozens of long tutorials, fetch the captions
instead (`pip install youtube-transcript-api`, run it in Composio's workbench if YouTube answers a cloud IP with
"confirm you're not a bot"), turn each transcript into notes with any LLM (Composio's `invoke_llm` in the
workbench took ~25 s each, 10 in parallel), and keep Gemini video requests for videos with no narration.
Stop a batch on a daily-quota 429 instead of retrying, and check the fallback model name still exists.

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
- Model names: "Astra" is OpenAI's GPT-6 Astra (reasoning model, text+image in, text out, no video input).
  Third-party price guides list it on Plus and up, not Free; API is $10/$50 per 1M in/out tokens. Before
  switching a job to it, run `codex exec -m gpt-6-astra ...` once: if the free login refuses it, ask the person
  about Plus instead of retrying.

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
| "Opus can just do this check itself" | A Haiku agent does a scan or link check for a fraction of the usage; hand it down. |
| "The second opinion said it's wrong, so it's wrong" | Outside models invent problems too; verify before acting. |
| "Codex output looked fine at a glance" | Spot-check a sample against the done-criteria before using it. |
| "I'll grab a few frames and guess the rest" | Frames miss the audio and the cuts; send the video to Gemini for a timestamped breakdown. |
| "A newer model will fix the renders" | Render quality comes from the scene, lighting and the check loop, not from which model writes the Blender script. Switch models only for a clear, tested gain. |
| "The caption is enough" | Often it is (check it first), but if steps are only shown on screen, run the breakdown. |

## Lessons
- 2026-11-21: the TikTok that started this was a Theo clip about a model auditing another
  model's unmerged work and saying "this is fine, merge it". Useful lesson: a quick outside
  audit can end over-iteration. It did not describe a ChatGPT routing setup.
- 2026-11-23: a TikTok showed giving Claude Code "eyes" with Google's Gemini API CLI: paste a YouTube link, get
  a breakdown by timestamps. Added the "Videos" section. Its full steps were in the caption, read via yt-dlp's
  info JSON in Composio's workbench, which is the cheap first check for any clip.
- 2026-11-24: an IG reel ("comment ASTRA for the skill") showed a 90s bedroom built and animated in Blender by
  GPT-6 Astra over Blender MCP, with Tripo for image-to-3D. The gain was the pipeline (reference image, AI mesh
  generation for props, scripted lighting), not the model; the skill itself was comment-gated. Video breakdowns
  stay with Gemini because Astra takes no video.
- 2026-11-24: first live test on a public YouTube link worked with `gemini-3.5-flash` (timestamped answer in
  ~20 s). `gemini-2.5-flash` was closed to new keys and `gemini-3.8-flash` was overloaded (503).
- 2026-11-25: built "The Hive" routing (Queen Bee Opus, Haiku scouts, Sonnet builders, Codex and Gemini as
  neighbouring hives) after the owner asked to save usage by switching models per task. Live tests: a Haiku agent ran
  the private-data scan of this skill in 28 s (2 findings, both the owner's own name in the LICENSE and banner, which
  are meant to be public: tell scouts what is allowed, they flag strictly); a Sonnet agent rewrote the README in
  10 s; Gemini gave a second-opinion review in 3 s via `scripts/ask_gemini.py` (on gemini-3.5-flash-lite: 3.5-flash
  was at its daily quota and the others 503), and one of its claims was false, hence rule 7. Codex: login and
  version checked on the Mac; Claude Code's auto mode there refused `codex exec` until the owner added the
  `Bash(codex exec:*)` allow rule. Then a read-only, stdout-only Codex coding job (script + unittest) took 26 s and
  ~9.4k tokens on the free ChatGPT login (model gpt-6-luna), no limit message. Its tests passed when run in the
  cloud, but a run on the real site flagged every nested url (`/digital/...`) and `/` as invalid: the brief was
  too loose, and only the cross-check caught it. Always run Codex output against real data before using it.
  `codex exec` still prints "Reading additional input from stdin..." with `</dev/null`; that's harmless.
