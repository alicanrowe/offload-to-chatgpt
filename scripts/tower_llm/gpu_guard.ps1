# Hive GPU guard: renders always win. Every 10 s, if a render/GPU app is running and Ollama holds a model
# in VRAM, unload it. Runs as a hidden scheduled task (S4U logon, no window), so the screen stays black.
$apps = 'blender','CLO_Standalone','CLO3D','MarvelousDesigner','TouchDesigner','UnrealEditor','Resolve','houdini','houdinifx','Cinema 4D'
$log = 'C:\offload\gpu_guard.log'
New-Item -ItemType Directory -Force -Path 'C:\offload' | Out-Null
while ($true) {
  try {
    $busy = Get-Process -ErrorAction SilentlyContinue | Where-Object { $n = $_.ProcessName; $apps | Where-Object { $n -like "$_*" } }
    if ($busy) {
      $ps = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/ps' -TimeoutSec 5
      foreach ($m in $ps.models) {
        $body = @{ model = $m.name; keep_alive = 0 } | ConvertTo-Json
        Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:11434/api/generate' -Body $body -ContentType 'application/json' -TimeoutSec 30 | Out-Null
        Add-Content $log ("{0} unloaded {1} because {2} is running" -f (Get-Date -Format s), $m.name, ($busy[0].ProcessName))
      }
    }
  } catch { }
  Start-Sleep -Seconds 10
}
