# Prompt 06 - Build a Custom FFGL Plugin (advanced)

Prereq: comfort with the idea of C++ compiling on your machine. Windows:
Visual Studio 2022 Build Tools (free). Expect an hour the first time.
This is how the React Pulsar source in the Orbit manifests was born.

---

Help me build a custom FFGL SOURCE plugin for Resolume from the official
Resolume FFGL SDK.

Setup and law:
1. Clone the Resolume FFGL SDK (github.com/resolume/ffgl). Read its
   LICENSE and tell me what it allows before we write anything.
2. Hard constraints for Resolume 7: GLSL 410 core in a single pass, x64
   Release build with static CRT (MultiThreaded, not DLL), plugin display
   name 16 CHARACTERS OR FEWER (longer names truncate in the browser),
   a unique 4-char plugin id, and parameters are 0-1 scalars only - FFT
   linking gives you one band per param, never a spectrum array. Design
   stateless: no feedback buffers; every frame renders from (time, params).

Build it:
3. Scaffold by COPYING the closest SDK example pair (.h/.cpp) and its
   .vcxproj (new GUID, renamed preprocessor define) - nothing picks up
   new plugins automatically, so also write a small build script (MSBuild
   one-liner) and a deploy script that checks the DLL is really x64
   (PE header machine type 0x8664) before copying it to Documents >
   Resolume > Extra Effects, and verifies the copy by hash. Scripts must
   exit nonzero on any failure - silent partial success is how you deploy
   a stale DLL and debug a ghost for an hour.
4. The effect itself: my idea is [YOUR VISUAL IDEA]. Keep the parameter
   count to 5-7, name them for a performer, and make ONE param the
   obvious FFT-link driver.
5. Resolume only rescans Extra Effects at startup: deploy, then restart
   Resolume, then check the plugin appears in Sources with the right name
   and param count, then load it in a clip and confirm pixels move.

Known gotcha (paid for in blood): on some rigs a plugin instance created
MID-SESSION renders black while its thumbnail looks fine - instances
created at composition load render correctly. So the real smoke test is:
seed the clip, save, restart Resolume, verify pixels. If it renders after
a restart, it will render at the gig - gigs always load the comp fresh.

VERIFY (me): the plugin shows in Sources, seven params slide, and an FFT
link on the driver param makes it breathe with music.
