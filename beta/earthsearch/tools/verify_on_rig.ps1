# verify_on_rig.ps1 - acceptance test for EarthSearch_EP01_Live_Mix against a
# RUNNING Resolume Avenue.
#
# Requires: Preferences > Webserver > "Enable Webserver & REST API" on port 8080.
# Nothing here is destructive: it opens the composition, exercises the three
# safety controls, measures sync, and reports. It never saves.
#
#   powershell -File verify_on_rig.ps1
#   powershell -File verify_on_rig.ps1 -SkipOpen      (test what is loaded now)

param(
  [string]$Comp = 'C:/Art Projects/Res_Fable/earthsearch/output/EarthSearch_EP01_Live_Mix.avc',
  [switch]$SkipOpen,
  [int]$SyncSeconds = 120
)

$ErrorActionPreference = 'Continue'
$base = 'http://127.0.0.1:8080/api/v1'
$pass = 0; $fail = 0
function Check($name, $cond, $detail) {
  if ($cond) { $script:pass++; "  PASS  $name  $detail" }
  else       { $script:fail++; "  FAIL  $name  $detail" }
}
function Comp { Invoke-RestMethod -Uri "$base/composition" -TimeoutSec 90 }
function SetParam($id, $val) {
  $b = @{ value = $val } | ConvertTo-Json -Compress
  Invoke-RestMethod -Uri "$base/parameter/by-id/$id" -Method Put -Body $b `
    -ContentType 'application/json' -TimeoutSec 20 | Out-Null
}
function StartBoth {
  # exactly what the APC's START BOTH button does: three clip-connects that
  # share one MIDI key.
  foreach ($i in 1, 2, 8) {
    try { Invoke-RestMethod -Uri "$base/composition/layers/$i/clips/1/connect" `
        -Method Post -TimeoutSec 20 | Out-Null } catch {}
  }
}

"=== EarthSearch EP01 rig acceptance test ==="
try { $prod = Invoke-RestMethod -Uri "$base/product" -TimeoutSec 10 }
catch { "REST API unreachable on 8080. Enable Preferences > Webserver."; exit 1 }
"Resolume $($prod.name) $($prod.major).$($prod.minor).$($prod.micro).$($prod.revision)"

if (-not $SkipOpen) {
  $u = 'file:///' + ($Comp -replace ' ', '%20')
  "opening $u"
  # A 2.3 GB master pair takes a while to resolve; the HTTP call may time out
  # while the load itself succeeds, so poll instead of trusting the response.
  try { Invoke-RestMethod -Uri "$base/composition/open" -Method Post -Body $u `
      -ContentType 'text/plain' -TimeoutSec 240 | Out-Null } catch {}
  for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Seconds 3
    try { $c = Comp; if ($c.name.value -eq 'EarthSearch_EP01_Live_Mix') { break } } catch {}
  }
}

$c = Comp
""
"--- structure ---"
Check "composition name"  ($c.name.value -eq 'EarthSearch_EP01_Live_Mix') $c.name.value
Check "8 layers"          ($c.layers.Count -eq 8)  "layers=$($c.layers.Count)"
Check "8 columns"         ($c.columns.Count -eq 8) "columns=$($c.columns.Count)"
# Derived from the spec by the build, not hard-coded here - a stale literal in
# a test is a test that fails for the wrong reason.
$wantFx = 38 + 1
Check "$wantFx comp effects"  (@($c.video.effects).Count -eq $wantFx) `
                          "count=$(@($c.video.effects).Count) (38 + Transform)"
$names = @($c.video.effects | ForEach-Object { $_.name })
Check "CRT present"       ($names -contains 'CRT') "broadcast bank signature"
Check "Radar present"     ($names -contains 'Radar') ""
Check "WarpSpeed present" ($names -contains 'WarpSpeed') ""

""
"--- safety: nothing may auto-fire, nothing may be restarted by a column ---"
$allIgnore = $true
for ($i = 0; $i -lt 8; $i++) { if (-not $c.layers[$i].ignorecolumntrigger.value) { $allIgnore = $false } }
Check "all 8 layers ignore column triggers" $allIgnore ""
$noFaderStart = $true
for ($i = 0; $i -lt 8; $i++) { if ($c.layers[$i].faderstart.value) { $noFaderStart = $false } }
Check "no layer has fader-start" $noFaderStart "fader-start would restart a master on a fader move"
Check "MASTER A on crossfader bus A" ($c.layers[0].crossfadergroup.value -eq 'A') ""
Check "MASTER B on crossfader bus B" ($c.layers[1].crossfadergroup.value -eq 'B') ""
Check "crossfader opens hard on A" ($c.crossfader.phase.value -le -0.999) `
      "phase=$($c.crossfader.phase.value) on a -1..1 scale; 0 would be a 50/50 double exposure"

""
"--- STOP / RESET BOTH ---"
Invoke-RestMethod -Uri "$base/composition/disconnect-all" -Method Post -TimeoutSec 30 | Out-Null
Start-Sleep -Seconds 3
$c = Comp
$anyConn = $false
for ($i = 0; $i -lt 8; $i++) {
  if (@($c.layers[$i].clips | Where-Object { $_.connected.value -like 'Connected*' }).Count) { $anyConn = $true }
}
Check "disconnect-all clears every layer" (-not $anyConn) ""

""
"--- START BOTH @ 00:00 ---"
StartBoth
Start-Sleep -Seconds 3
$c = Comp
Check "MASTER A connected" ($c.layers[0].clips[0].connected.value -like 'Connected*') ""
Check "MASTER B connected" ($c.layers[1].clips[0].connected.value -like 'Connected*') ""
Check "SCOPE connected"    ($c.layers[7].clips[0].connected.value -like 'Connected*') ""
$a0 = $c.layers[0].clips[0].transport.position.value
$b0 = $c.layers[1].clips[0].transport.position.value
Check "both start together" ([math]::Abs($a0 - $b0) -lt 1.0) `
      ("A=$([math]::Round($a0)) ms B=$([math]::Round($b0)) ms")

""
"--- sync hold over $SyncSeconds s ---"
$worst = 0.0
for ($t = 0; $t -lt $SyncSeconds; $t += 5) {
  Start-Sleep -Seconds 5
  $c = Comp
  $d = [math]::Abs($c.layers[0].clips[0].transport.position.value - $c.layers[1].clips[0].transport.position.value)
  if ($d -gt $worst) { $worst = $d }
  "    t+$($t+5)s  drift = $([math]::Round($d,2)) ms"
}
Check "drift stays under one frame (41.67 ms)" ($worst -lt 41.67) "worst=$([math]::Round($worst,2)) ms over $SyncSeconds s"

""
"--- a column trigger must NOT disturb the masters ---"
$c = Comp
$before = $c.layers[0].clips[0].transport.position.value
Invoke-RestMethod -Uri "$base/composition/columns/3/connect" -Method Post -TimeoutSec 30 | Out-Null
Start-Sleep -Seconds 3
$c = Comp
$stillA = $c.layers[0].clips[0].connected.value -like 'Connected*'
$stillB = $c.layers[1].clips[0].connected.value -like 'Connected*'
$after = $c.layers[0].clips[0].transport.position.value
Check "masters survive a column trigger" ($stillA -and $stillB) ""
Check "masters kept playing through it" ($after -gt $before) `
      ("$([math]::Round($before)) -> $([math]::Round($after)) ms")

""
"--- an overlay pad must NOT disturb the masters ---"
$c = Comp
$before = $c.layers[0].clips[0].transport.position.value
Invoke-RestMethod -Uri "$base/composition/layers/3/clips/5/connect" -Method Post -TimeoutSec 20 | Out-Null
Invoke-RestMethod -Uri "$base/composition/layers/7/clips/2/connect" -Method Post -TimeoutSec 20 | Out-Null
Start-Sleep -Seconds 3
$c = Comp
$after = $c.layers[0].clips[0].transport.position.value
Check "overlay launches leave the masters running" `
      (($c.layers[0].clips[0].connected.value -like 'Connected*') -and ($after -gt $before)) `
      ("A $([math]::Round($before)) -> $([math]::Round($after)) ms")

""
"--- CLEAN / ALL FX OFF (composition dashboard links 1-8 to zero) ---"
foreach ($n in 1..8) { SetParam $c.dashboard."Link $n".id 0.0 }
Start-Sleep -Seconds 2
$c = Comp
$allZero = $true
foreach ($n in 1..8) { if ($c.dashboard."Link $n".value -gt 0.001) { $allZero = $false } }
Check "all eight CLEAN links reach zero" $allZero ""
$stillPlaying = $c.layers[0].clips[0].connected.value -like 'Connected*'
Check "CLEAN did not touch playback" $stillPlaying ""
foreach ($n in 1..8) { SetParam $c.dashboard."Link $n".id 1.0 }

""
"--- colours load as written (ParamColor is ABGR, not ARGB) ---"
$want = @{ 'CARRIER WAVE' = '#38ffa8'; 'TELEMETRY' = '#ffb03a';
           'DISTRESS' = '#ff3b2f'; 'VECTOR RISE' = '#4fe3ff' }
$badCol = @()
foreach ($lay in $c.layers) {
  foreach ($cl in $lay.clips) {
    $n = $cl.name.value
    if ($want.ContainsKey($n)) {
      $got = $cl.video.sourceparams.Color.value
      if ($got -notlike ($want[$n] + '*')) { $badCol += "$n=$got" }
    }
  }
}
Check "clip colours load as written" ($badCol.Count -eq 0) `
      $(if ($badCol.Count) { $badCol -join ', ' } else { 'phosphor / amber / alert / signal all correct' })

""
"--- wet ceilings are applied ---"
$ceil = @{ 'StaticEffect' = 0.12; 'NoisyEffect' = 0.25; 'Radar' = 0.45 }
$badCeil = @()
foreach ($k in $ceil.Keys) {
  $e = $c.video.effects | Where-Object { $_.name -eq $k }
  if (-not $e -or [math]::Abs($e.params.Opacity.out - $ceil[$k]) -gt 0.001) {
    $badCeil += "$k=$($e.params.Opacity.out)"
  }
}
Check "GRAIN / NOISE / RADAR carry their ceilings" ($badCeil.Count -eq 0) `
      $(if ($badCeil.Count) { $badCeil -join ', ' } else { 'GRAIN 0.12, NOISE 0.25, RADAR 0.45' })

""
"--- FFT is live (composition FFT, driven by the master's own audio) ---"
$hasAudio = $null -ne $c.layers[0].clips[0].audio -and `
            $c.layers[0].clips[0].audio.PSObject.Properties.Count -gt 0
Check "MASTER A has a decoded audio track" $hasAudio `
      "without one, every reactive parameter sits pinned at its floor"
$b1 = ($c.video.effects | Where-Object { $_.name -eq 'Bloom' }).params.Amount.value
$moved = $false
for ($i = 0; $i -lt 10; $i++) {
  Start-Sleep -Milliseconds 900
  $c = Comp
  $b2 = ($c.video.effects | Where-Object { $_.name -eq 'Bloom' }).params.Amount.value
  if ([math]::Abs($b2 - $b1) -gt 0.0005) { $moved = $true; break }
}
Check "Bloom Amount moves with the audio" $moved "$b1 -> $b2 (window 0.14-0.44)"

""
"=== $pass passed, $fail failed ==="
if ($fail -gt 0) { exit 1 }
