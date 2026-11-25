#!/usr/bin/env python3
"""Ask the tower's local model (the Drone bee) - only when the GPU is idle.

Runs ON the tower (Windows or Ubuntu). Stdlib only. Talks to Ollama on 127.0.0.1:11434.

  python ask_local.py --status
  python ask_local.py -o answer.md -f notes.txt "Summarise these notes in 10 bullets"
  python ask_local.py --light "Rename these files ..."      # small model
  python ask_local.py --unload                               # free the VRAM now

Exit codes: 0 ok, 3 GPU busy (renders/CLO/TouchDesigner running, or not enough free VRAM: use another bee),
            4 Ollama not reachable, 5 model error.
The GPU gate runs before every call. Never bypass it while a render may be running.
"""
import argparse, json, os, subprocess, sys, time, urllib.request

OLLAMA = os.environ.get("HIVE_OLLAMA", "http://127.0.0.1:11434")
BIG = os.environ.get("HIVE_BIG", "qwen3.8:27b")      # ~18 GB at Q4_K_M
LIGHT = os.environ.get("HIVE_LIGHT", "qwen3.5:9b")   # ~6.6 GB at Q4_K_M
NEED_GB = {BIG: 21.0, LIGHT: 9.0}                     # weights + 16K context + headroom
# Anything that renders or uses the GPU for the owner's work wins over the model.
GPU_APPS = ("blender", "clo_standalone", "clo3d", "marvelous", "touchdesigner", "unrealeditor", "resolve.exe",
            "houdini", "cinema 4d", "substance")
UTIL_BUSY = 20  # % GPU util (sampled) that counts as busy when no model of ours is loaded


def sh(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return ""


def gpu_state():
    q = sh(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"])
    if not q.strip():
        return None
    util, used, total = [float(x) for x in q.strip().splitlines()[0].split(",")]
    apps = sh(["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory", "--format=csv,noheader,nounits"])
    procs = sh(["tasklist", "/FO", "CSV", "/NH"]) if os.name == "nt" else sh(["ps", "-eo", "comm"])
    return {"util": util, "used_gb": used / 1024, "total_gb": total / 1024,
            "apps": apps.lower(), "procs": procs.lower()}


def api(path, body=None, timeout=900):
    req = urllib.request.Request(OLLAMA + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def loaded():
    try:
        return [m["name"] for m in api("/api/ps", timeout=10).get("models", [])]
    except Exception:
        return None


def unload_all():
    for m in loaded() or []:
        api("/api/generate", {"model": m, "keep_alive": 0}, timeout=60)
    return True


def gate(model):
    """Return (ok, reason). ok=False means: don't touch the GPU, route to another bee."""
    g = gpu_state()
    if g is None:
        return False, "nvidia-smi not found or failed"
    busy_apps = [a for a in GPU_APPS if a in g["procs"] or a in g["apps"]]
    if busy_apps:
        return False, "render/GPU app running: " + ", ".join(busy_apps)
    ours = loaded() or []
    ours_gb = 0.0
    if ours:
        # VRAM our own model holds is reusable (same model) or freed when Ollama swaps.
        ours_gb = sum(m.get("size_vram", 0) for m in api("/api/ps", timeout=10).get("models", [])) / 1e9
    free = g["total_gb"] - g["used_gb"] + ours_gb
    if not ours and g["util"] >= UTIL_BUSY:
        return False, f"GPU {g['util']:.0f}% busy with something else"
    if free < NEED_GB.get(model, 20):
        return False, f"only {free:.1f} GB VRAM free, {model} needs {NEED_GB.get(model, 20)} GB"
    return True, f"GPU idle ({g['util']:.0f}%), {free:.1f} GB free"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?")
    ap.add_argument("-f", "--file", action="append", default=[], help="input text file(s), added to the prompt")
    ap.add_argument("-o", "--out", help="write the answer here")
    ap.add_argument("--light", action="store_true", help="use the small model")
    ap.add_argument("--strict", action="store_true", help="don't fall back to the small model when the big one won't fit")
    ap.add_argument("--think", action="store_true", help="let the model reason first (slower, better on hard asks)")
    ap.add_argument("--ctx", type=int, default=16384)
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--unload", action="store_true")
    a = ap.parse_args()

    if loaded() is None:
        print("OLLAMA_DOWN: Ollama not reachable at " + OLLAMA, file=sys.stderr); sys.exit(4)
    if a.unload:
        unload_all(); print("unloaded"); return
    model = LIGHT if a.light else BIG
    ok, why = gate(model)
    if not ok and model == BIG and not a.strict:
        ok2, why2 = gate(LIGHT)
        if ok2:
            model, ok, why = LIGHT, True, why2 + " (big model won't fit, using light)"
    if a.status:
        print(json.dumps({"ok": ok, "why": why, "model": model, "loaded": loaded()}, indent=1)); return
    if not ok:
        print("GPU_BUSY: " + why, file=sys.stderr); sys.exit(3)
    if not a.prompt:
        ap.error("prompt required")
    text = a.prompt
    for p in a.file:
        with open(p, encoding="utf-8", errors="replace") as fh:
            text += f"\n\n--- {os.path.basename(p)} ---\n" + fh.read()
    t0 = time.time()
    try:
        r = api("/api/chat", {"model": model, "stream": False, "keep_alive": "2m", "think": a.think,
                              "messages": [{"role": "user", "content": text}],
                              "options": {"num_ctx": a.ctx}})
    except Exception as e:
        print(f"MODEL_ERROR: {e}", file=sys.stderr); sys.exit(5)
    ans = r["message"]["content"]
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(ans)
    else:
        print(ans)
    n, d = r.get("eval_count", 0), r.get("eval_duration", 1) / 1e9
    print(f"[{model} | {why} | {time.time()-t0:.1f}s | {n} tok out, {n/max(d,1e-6):.0f} tok/s]", file=sys.stderr)


if __name__ == "__main__":
    main()
