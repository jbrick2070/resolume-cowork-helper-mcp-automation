# calibrate_fft.ps1 - measure how much of its range each FFT band actually
# uses, against the real soundtrack, and pick gains from data instead of taste.
#
# The house FFT recipe card is written for club material. A 1981 BBC radio
# drama is band-limited, dialogue-dominated and quiet, and at the 3-6 dB that
# card suggests every reactive parameter here moved less than 6% of its range -
# invisible. This script is how the shipped numbers were chosen.
#
# Requires: Resolume running, Webserver REST API on 8080, the EarthSearch
# composition open and PLAYING (the analysis is of whatever is under the
# playhead, so let it run through a talky passage AND a musical one).
#
#   powershell -File calibrate_fft.ps1
#   powershell -File calibrate_fft.ps1 -Gains 24,30,36 -Samples 32

param(
  [int[]]$Gains = @(12, 24, 30, 36, 42),
  [int]$Samples = 24,
  [int]$IntervalMs = 220
)

$ErrorActionPreference = 'Continue'
$base = 'http://127.0.0.1:8080/api/v1'

function Comp { Invoke-RestMethod -Uri "$base/composition" -TimeoutSec 90 }
function SetP($id, $v) {
  $b = @{ value = $v } | ConvertTo-Json -Compress
  Invoke-RestMethod -Uri "$base/parameter/by-id/$id" -Method Put -Body $b `
    -ContentType 'application/json' -TimeoutSec 20 | Out-Null
}

# One anchor per band - the same three the Track Control knobs steer live.
$targets = @(
  @{ band = 'LOW '; fx = 'Trails';   param = 'Feedback'; lo = 0.42;  hi = 0.66 },
  @{ band = 'MID '; fx = 'Bloom';    param = 'Amount';   lo = 0.14;  hi = 0.44 },
  @{ band = 'HIGH'; fx = 'ShiftRGB'; param = 'Distance'; lo = 0.015; hi = 0.070 }
)

$c = Comp
if ($c.name.value -ne 'EarthSearch_EP01_Live_Mix') {
  "The EarthSearch composition is not open (found '$($c.name.value)')."; exit 1
}
if ($c.layers[0].clips[0].connected.value -notlike 'Connected*') {
  "MASTER A is not playing. Press START BOTH first - the FFT analyses the"
  "composition's own audio, so nothing is measurable while it is stopped."
  exit 1
}

"Reading what each band does to its parameter, $Samples samples per gain."
"Span = how much of the output range the band used. FloorLift = how far the"
"quiet moments sat above the floor; a high floor lift reads as 'always on'."
""

foreach ($t in $targets) {
  $fx = $c.video.effects | Where-Object { $_.name -eq $t.fx }
  $prm = $fx.params.($t.param).id
  $ps = Invoke-RestMethod -Uri "$base/parameter/by-id/$prm/phase-source" -TimeoutSec 20
  if ($ps.phase_source -ne 'composition_fft') {
    "  $($t.band) $($t.fx).$($t.param) is not on composition FFT - skipping"
    continue
  }
  $gid = $ps.parameters.Gain.id
  $original = $ps.parameters.Gain.value
  "$($t.band) [$($t.fx).$($t.param)]  out-range $($t.lo)-$($t.hi)  band $($ps.parameters.FrequencyRange.in)-$($ps.parameters.FrequencyRange.out)"
  foreach ($g in $Gains) {
    SetP $gid ([double]$g)
    Start-Sleep -Milliseconds 700
    $v = @()
    for ($i = 0; $i -lt $Samples; $i++) {
      $v += (Invoke-RestMethod -Uri "$base/parameter/by-id/$prm" -TimeoutSec 20).value
      Start-Sleep -Milliseconds $IntervalMs
    }
    $mn = ($v | Measure-Object -Minimum).Minimum
    $mx = ($v | Measure-Object -Maximum).Maximum
    $rng = $t.hi - $t.lo
    $pin = ($v | Where-Object { $_ -ge ($t.hi - $rng * 0.02) }).Count
    "    {0,3} dB  min={1:F4} max={2:F4}  span={3,5:F1}%  floorLift={4,5:F1}%  pinned={5}/{6}" -f `
      $g, $mn, $mx, (($mx - $mn) / $rng * 100), (($mn - $t.lo) / $rng * 100), $pin, $Samples
  }
  SetP $gid ([double]$original)
  "    restored to $original dB"
  ""
}

"Pick the gain with the largest span, a floor lift under about 10%, and"
"nothing pinned. The shipped values chosen this way were LOW 27 dB,"
"MID 30 dB, HIGH 30-36 dB."
