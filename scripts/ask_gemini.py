#!/usr/bin/env python3
"""Send a text job (plus optional files) to Gemini and write the answer to a file.

usage: python3 ask_gemini.py -o answer.md [-f file ...] [-m model] "prompt"
       python3 ask_gemini.py -o answer.md -p prompt.txt -f big_log.txt

Needs GEMINI_API_KEY in the environment (source the private key file first).
Text files given with -f are inlined; images/PDFs (.png .jpg .jpeg .webp .pdf) are sent inline as base64.
Tries the models in order and falls back on 404/429/503 or a timeout; if all are busy it waits 30 s and tries again. Prints the model used and the
answer length; the answer itself only goes to the -o file, so the calling Claude reads only what it needs.
"""
import argparse, base64, json, mimetypes, os, pathlib, sys, time, urllib.error, urllib.request

MODELS = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.7-flash", "gemini-flash-latest", "gemini-3.5-flash-lite"]
BIN = {".png", ".jpg", ".jpeg", ".webp", ".pdf"}
URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"


def parts_for(files):
    parts = []
    for f in files:
        p = pathlib.Path(f)
        if p.suffix.lower() in BIN:
            mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
            parts.append({"inline_data": {"mime_type": mime, "data": base64.b64encode(p.read_bytes()).decode()}})
        else:
            parts.append({"text": f"--- file: {p.name} ---\n{p.read_text(errors='replace')}\n--- end {p.name} ---"})
    return parts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?", default="")
    ap.add_argument("-p", "--prompt-file")
    ap.add_argument("-f", "--file", action="append", default=[])
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("-m", "--model", action="append", help="model to try first (repeatable)")
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--rounds", type=int, default=2, help="passes over the model list (30 s apart) when all are busy")
    a = ap.parse_args()
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit("GEMINI_API_KEY is not set: source the private key file first")
    prompt = pathlib.Path(a.prompt_file).read_text() if a.prompt_file else a.prompt
    if not prompt.strip():
        sys.exit("no prompt")
    body = json.dumps({"contents": [{"parts": parts_for(a.file) + [{"text": prompt}]}]}).encode()
    last = ""
    order = (a.model or []) + MODELS
    for model in [m for r in range(a.rounds) for m in order]:
        if model == order[0] and last:
            time.sleep(30)  # every model was busy: wait, then try the list again
        req = urllib.request.Request(URL.format(model), data=body, method="POST",
                                     headers={"x-goog-api-key": key, "Content-Type": "application/json"})
        t = time.time()
        try:
            with urllib.request.urlopen(req, timeout=a.timeout) as r:
                data = json.load(r)
        except urllib.error.HTTPError as e:
            last = f"{model}: HTTP {e.code} {e.read()[:200]!r}"
            if e.code == 429 and b"PerDay" in last.encode():
                print("daily quota hit:", last, file=sys.stderr)
            if e.code in (404, 429, 500, 503):
                print("fallback:", last[:120], file=sys.stderr)
                continue
            sys.exit(last)
        except Exception as e:  # timeout or network
            last = f"{model}: {e}"
            print("fallback:", last[:120], file=sys.stderr)
            continue
        text = "".join(p.get("text", "") for c in data.get("candidates", [])[:1]
                       for p in c.get("content", {}).get("parts", []))
        if not text:
            last = f"{model}: empty answer {json.dumps(data)[:200]}"
            continue
        pathlib.Path(a.out).write_text(text)
        use = data.get("usageMetadata", {})
        print(f"ok model={model} secs={time.time()-t:.0f} chars={len(text)} "
              f"tokens_in={use.get('promptTokenCount')} tokens_out={use.get('candidatesTokenCount')} -> {a.out}")
        return
    sys.exit("all models failed; last: " + last)


if __name__ == "__main__":
    main()
