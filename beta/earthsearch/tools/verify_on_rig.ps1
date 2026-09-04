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
  [int]$SyncSeconds = 20
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
Check "38 comp effects"   (@($c.video.effects).Count -eq 38) `
                          "count=$(@($c.video.effects).Count) (37 + Transform)"
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
Check "drift stays under one frame (41.67 ms)" ($worst -lt 41.67) "worst=$([math]::Round($worst,2)) ms"

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
"--- CLEAN / ALL FX OFF (composition dashboard links 1-7 to zero) ---"
foreach ($n in 1..7) { SetParam $c.dashboard."Link $n".id 0.0 }
Start-Sleep -Seconds 2
$c = Comp
$allZero = $true
foreach ($n in 1..7) { if ($c.dashboard."Link $n".value -gt 0.001) { $allZero = $false } }
Check "all seven CLEAN links reach zero" $allZero ""
$stillPlaying = $c.layers[0].clips[0].connected.value -like 'Connected*'
Check "CLEAN did not touch playback" $stillPlaying ""
foreach ($n in 1..7) { SetParam $c.dashboard."Link $n".id 1.0 }

""
"--- FFT is live (composition FFT, driven by the masters' own audio) ---"
$c = Comp
$bloom = $c.video.effects | Where-Object { $_.name -eq 'Bloom' }
$amt = $bloom.effect.params | Where-Object { $_.name -like '*Amount*' -or $_.name -like '*Brightness*' } | Select-Object -First 1
if ($amt) {
  $v1 = $amt.value
  Start-Sleep -Seconds 3
  $c = Comp
  $bloom2 = $c.video.effects | Where-Object { $_.name -eq 'Bloom' }
  $amt2 = $bloom2.effect.params | Where-Object { $_.name -like '*Amount*' -or $_.name -like '*Brightness*' } | Select-Object -First 1
  Check "Bloom Amount is moving with the audio" ($amt2.value -ne $v1) "$v1 -> $($amt2.value)"
} else {
  "  SKIP  could not locate Bloom Amount in the REST tree"
}

""
"=== $pass passed, $fail failed ==="
if ($fail -gt 0) { exit 1 }
