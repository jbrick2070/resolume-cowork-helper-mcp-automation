# plugins/ - the React FFGL plugins (source + DLLs)

Five custom FFGL plugins for Resolume Avenue/Arena 7, written with an AI
agent driving the build (prompt 06 documents the method). Ships as both
ready-to-use x64 DLLs and full source.

| Plugin | Type | One line |
|---|---|---|
| React Pulsar | SOURCE | 1967 - CP1919 pulsar ridgelines, stateless, 7 FFT-linkable params |
| React Video Music | SOURCE | 1977 - Atari Video Music raster patterns |
| React Gate | EFFECT | hard luma gate |
| React Anamorphic | EFFECT | anamorphic streak/squeeze with internal clock |
| React Scanline | EFFECT | scanline displace |

Placards and per-plugin details: `REACT_OPTICS_NOTES.md`.

## Install the DLLs (no coding)

1. Copy the DLLs from `dll/` into `Documents\Resolume Avenue\Extra Effects\`
   (Arena: `Documents\Resolume Arena\Extra Effects\`; create the folder if
   missing).
2. RESTART Resolume - it only scans Extra Effects at startup.
3. Sources appear under Sources ("React Pulsar", "React Video Musi" - the
   16-char display limit trims the last one); effects under Video Effects.

Windows x64 only, built against Avenue 7.27. SmartScreen may warn on
unsigned DLLs - that is expected for community plugins.

## Build from source

1. Clone the Resolume FFGL SDK: github.com/resolume/ffgl
2. Drop each plugin folder from here into the SDK's `source/plugins/`.
3. Copy the matching `.vcxproj` from `build/` into the SDK's
   `build/windows/` (they reference SDK-relative paths).
4. Build with VS2022 Build Tools:
   `MSBuild build\windows\ReactPulsar.vcxproj /p:Configuration=Release /p:Platform=x64`
5. Deploy the DLL from `binaries\x64\Release\` per the install steps above.

Constraints these plugins honor (and yours should too): GLSL 410 single
pass, x64 Release static CRT, display names 16 chars max, 0-1 scalar
params only (Resolume's FFT link drives one band per param), stateless
rendering.

## Known quirk

On some rigs, a plugin instance created MID-session renders black while
its thumbnail looks fine; instances created at composition load render
correctly. If a freshly added plugin cell is black: save, restart
Resolume, and it renders. Gigs always load the comp fresh, so live use is
unaffected.

## License

The plugin code in this folder: MIT (this repo's LICENSE).
Built with the FreeFrame FFGL SDK - its BSD 3-Clause license is reproduced
in `LICENSE-FFGL.md` and covers the SDK portions linked into the DLLs, as
its redistribution terms require. Not affiliated with or endorsed by
Resolume or FreeFrame.
