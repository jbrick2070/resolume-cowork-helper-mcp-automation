# Stability Protocol - how not to crash Resolume while an agent drives it

Every rule below was paid for with a real crash or a real ghost-hunt on the
rig this kit was built on (Avenue 7.27 + Resolume MCP 7.26, Windows 11).
Bake them into every prompt; they are already baked into this kit's.

## Load discipline

1. Batches of at most 8 operations; for FILE loads prefer one clip per
   call at a batch-of-4 cadence - rapid multi-file bursts have crashed
   Avenue with heap corruption while the same files loaded clean singly.
2. After any load burst: settle 12 seconds, then save (with the human's
   explicit confirmation). Save small, save often - crash recovery is
   "resume from last save", so the save cadence IS your blast radius.
3. On any load error: stop the batch. Read the cell's real state back
   before continuing. Never fire the next op blind after a timeout -
   structural ops can double-fire or late-land ~15 s after a timeout.

## Structural discipline

4. Layers / columns / decks: ONE structural op at a time, re-read state
   after each. After deleting or duplicating decks, verify by reading
   names AND probing a cell's actual parameters - cached clip lists can
   lie after deck operations; a parameter read is live truth.
5. Fresh/duplicated decks may be write-dark (clip loads 404) until the
   comp is saved and reloaded. Not a bug you can fight: save (confirmed),
   reload (confirmed), continue.
6. Filling the last column of a grid can auto-append a stray unnamed
   column. Check the column count after big fills; remove strays.

## Environment discipline

7. VRAM is the silent killer: check GPU memory BEFORE any load session.
   AI tools (ComfyUI, LLM runners) can quietly hold 8+ GB and Avenue will
   crash mid-burst on a starved card. Keep 2+ GB headroom during fills;
   close the model apps first.
8. Exclusive-audio apps (some players) can seize the audio device and
   wedge parts of the API. Close them while an agent drives.
9. Custom FFGL plugins: instances created mid-session may render black
   even though thumbnails look fine; comp-load instances render. Smoke
   test = seed, save, restart, verify pixels.

## Crash recovery (when it happens anyway)

10. Relaunch Resolume, wait a full 55 seconds before touching the API,
    dismiss any dialogs, click every deck tab once (unclicked tabs can be
    API-dark), then resume from the last save. Windows Event Viewer
    (Application, Event ID 1000) gives you the crash fingerprint fast -
    heap corruption means load-burst pacing, device-removed means VRAM.
