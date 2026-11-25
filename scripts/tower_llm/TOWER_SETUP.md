# Drone bee: local model on the home tower (one-time setup)

Target: Windows side of the tower (the default boot), one RTX 4090 24 GB. Renders always win: the model only runs
when the GPU is idle, and is unloaded the moment Blender, CLO3D or TouchDesigner starts.

## What gets installed (about 26 GB of disk)
| Piece | What | Size |
|---|---|---|
| Ollama (Windows) | model server, OpenAI-compatible API on 127.0.0.1:11434 only | ~1 GB |
| `qwen3.8:27b` | the Drone (big): dense 27B, Q4_K_M, tools + thinking + vision, 256K context | 18 GB |
| `qwen3.5:9b` | the Drone (light): same family Ajax was tuned from, for when VRAM is tight | 6.6 GB |

## Steps (run in a terminal on the tower; no reboot; nothing opens on screen)
0. Python: `python --version`. If missing: `winget install --id Python.Python.3.12 -e --silent`.
1. Install Ollama silently: `winget install --id Ollama.Ollama -e --silent --accept-package-agreements --accept-source-agreements`
   (or the official `OllamaSetup.exe /VERYSILENT /NORESTART`). If the Ollama tray app or a window opens, quit it,
   remove its Startup shortcut (`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Ollama.lnk`), and put the
   black server console back in front.
2. Settings live in `serve.cmd` (localhost only, one model loaded, unload after 2 min idle, flash attention,
   q8 KV cache). Localhost only: nothing on the network can reach it; jobs run on the tower like Codex and Gemini jobs.
3. Copy `serve.cmd`, `ask_local.py` and `gpu_guard.ps1` to `C:\offload\hive\`.
4. Two hidden scheduled tasks (S4U logon = no window, no password stored), started now:
   ```
   $u = "$env:USERDOMAIN\$env:USERNAME"
   $p = New-ScheduledTaskPrincipal -UserId $u -LogonType S4U
   $s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -ExecutionTimeLimit 0 -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
   Register-ScheduledTask HiveOllama -Principal $p -Settings $s -Trigger (New-ScheduledTaskTrigger -AtStartup) -Action (New-ScheduledTaskAction -Execute cmd.exe -Argument '/c C:\offload\hive\serve.cmd')
   Register-ScheduledTask HiveGpuGuard -Principal $p -Settings $s -Trigger (New-ScheduledTaskTrigger -AtStartup) -Action (New-ScheduledTaskAction -Execute powershell.exe -Argument '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\offload\hive\gpu_guard.ps1')
   Start-ScheduledTask HiveOllama; Start-ScheduledTask HiveGpuGuard
   ```
   If `ollama` isn't on that user's PATH, put its full path (`(Get-Command ollama).Source`) in serve.cmd.
5. Pull the models **only while no render is running** (downloads use network, not the GPU):
   `ollama pull qwen3.8:27b` and `ollama pull qwen3.5:9b`.
6. Checks (all must pass, log the times in the ETA skill):
   - `python C:\offload\hive\ask_local.py --status` says `"ok": true` with Blender closed.
   - `python C:\offload\hive\ask_local.py "Reply with exactly: DRONE OK"` prints DRONE OK and a tok/s line
     (expect roughly 40-90 tok/s on the 27B).
   - Within 2 min of that answer, start Blender headless so nothing opens on screen
     (`blender.exe -b --python-expr "import time; time.sleep(40)"`): within ~10 s `ollama ps` shows nothing loaded and `C:\offload\gpu_guard.log`
     has an "unloaded" line; `ask_local.py --status` now says `"ok": false` "render/GPU app running".
   - `nvidia-smi` shows ~0 MB used by Ollama after the 2-minute keep-alive with no jobs.
   - The screen is still the black server console.

## Undo
`Unregister-ScheduledTask -TaskName HiveOllama -Confirm:$false` (and HiveGpuGuard), `ollama rm qwen3.8:27b qwen3.5:9b`, uninstall
Ollama from Settings > Apps.
