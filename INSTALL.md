# INSTALL - verified APC40 mkII visual twin

The stable release is one tested composition/preset pair. Windows paths are
shown; Arena uses `Resolume Arena` instead of `Resolume Avenue`.

## 1. Install the composition

Copy:

    compositions\APC40_Visual_QA_148.avc

to:

    Documents\Resolume Avenue\Compositions\

Open it from Resolume's Composition menu. It contains 148 native Text Animator
clips and has no external media dependencies.

## 2. Install the MIDI preset

Close Resolume, then copy:

    controllers\APC 40 MK II - Visual QA.xml

to:

    Documents\Resolume Avenue\Shortcuts\MIDI\

If Windows redirects Documents to OneDrive, use the matching OneDrive
Documents folder. On macOS use:

    ~/Documents/Resolume Avenue/Shortcuts/MIDI/

Start Resolume with the APC40 mkII connected. In Preferences > MIDI:

1. enable `APC40 mkII` as both MIDI INPUT and MIDI OUTPUT;
2. leave the device in Alternate Ableton Live Mode;
3. select `APC 40 MK II - Visual QA`.

Trigger column 1 once if the labels are dark. Grid/buttons should toggle their
matching labels, faders should move vertically, knobs should rotate, and the
crossfader should move horizontally.

## Beta material

`beta/` contains the older React Live and Orbit compositions and their matching
controller presets. They are retained as experiments and are not claimed as
end-to-end controller-verified releases.

The FFGL plugins and FFT prompts are optional building material for those beta
experiments; they are not required by the stable visual twin.

## Troubleshooting

- No pad colors: enable the APC40 mkII as MIDI OUTPUT as well as INPUT.
- Preset missing: confirm the XML is in `Shortcuts\MIDI`, then restart Resolume.
- Labels remain dark: trigger column 1.
- Wrong device behavior: close Ableton or any other app using the APC, then
  power-cycle it before reopening Resolume.
- Full MIDI folder reference:
  https://resolume.com/support/en/directory-list
