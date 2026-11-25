# Offload to ChatGPT

A Claude skill for deciding when a task should go to ChatGPT/Codex (or to Gemini, for watching videos) instead
of Claude, and for handing it off cheaply. The rule at its core: only offload when the handoff costs less than
the work, so hand off by command line (`codex exec`, the Gemini API) rather than by driving an app with
screenshots.

What it covers:

- Which jobs to send out (bulk captioning, summaries, boilerplate drafts, simple scripts, second-opinion
  audits) and which to keep with Claude (design judgement, private material, anything needing the project's
  own tools).
- Setting up the Codex CLI signed in with a ChatGPT account, and an OpenAI API key with a spending cap.
- Getting a timestamped breakdown of a video from Gemini: YouTube links directly, other links by downloading
  the clip in a remote sandbox first.
- How to write a one-shot brief and spot-check what comes back.

See `SKILL.md` for the full steps.
