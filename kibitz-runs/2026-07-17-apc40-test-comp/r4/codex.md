VERDICT: yes-with-fixes — close, but not build-ready as-is because the plan still leaves port-selection, palette serialization, and self-contained build inputs ambiguous.

MUST-FIX BEFORE BUILD:
1. [Runbook sequencing] Unresolved either/or: “Add `--port-index`/`--port-name` … or drop port-select” leaves two valid incompatible builds. `C:\Art Projects\Res_Fable\apc40_led_test.py:25` currently picks first `"APC40"` match and has no argparse; exits are only implicit not contract-tested at lines 28 and 34. Concrete fix: choose one path. Recommended: add `--port-index` and `--port-name`, keep current first-match as default, and make acceptance require verified exit codes 0/1/2.

2. [Manifest builder] The exact velocity-to-screen-color mapping is still missing. Current plan says “Add an explicit velocity→RGB palette lookup,” but does not provide the lookup; `C:\Art Projects\Res_Fable\apc40_led_test.py:15` only gives velocities, while `docs\GRID_MAP_TEST_PLAN.md:36-37` requires on-screen color to match LED color. Concrete fix: freeze an 8-row table: velocity, color label, `screen_color_rgb`, serialized `ParamColor` integer. If unknown, add a build step to create/inspect one Avenue specimen per column and record the values before cloning.

3. [Unchanged from r2] The locked plan is not self-contained. `kibitz-runs\2026-07-17-apc40-test-comp\r3\final.md:38-40` replaces critical contracts with “Unchanged from r2,” including the manifest schema, FX per-kind behavior, preflight, and build path from `r2\final.md:4-55`. Concrete fix: inline those r2 contracts into the final plan, then apply the r3 changes directly. A builder should not need r2 open beside the final plan.

4. [Clip-clone builder] Exact v1 source/output invocation is not specified. The repo has both `compositions\Res React Live Gen.avc:2` as 4x8 and `compositions\Res React Orbit Gen.avc:2` as 4x9; docs target flipped React v4.4 at `docs\GRID_MAP_TEST_PLAN.md:28-31`. Concrete fix: add a single v1 invocation. [ASSUMPTION] For React v4.4, use `--src compositions/Res React Live Gen.avc --out compositions/Res React Grid Map Test.avc`; if Orbit is also desired, make that a separate later target.

SHOULD-FIX:
1. [Manifest builder] Do not store a singular `raw_status` for direct LED behavior. `apc40_led_test.py` sends both 0x90 and 0x95 at `C:\Art Projects\Res_Fable\apc40_led_test.py:37-43`, while `fx_row_paint.py` uses 0x96 at `C:\Art Projects\Res_Fable\fx_row_paint.py:30,52`. Concrete fix: split into `direct_led_statuses_tested`, `direct_led_status_selected`, and `fx_painter_status`.

2. [Clip-clone builder] Add explicit XML parse/no-media validation. `make_gen_avc.py` does `ET.fromstring(data)` at `C:\Art Projects\Res_Fable\make_gen_avc.py:172` and validates file refs at lines 159-168; current r3 validation only covers new duplicate IDs, placement, and text. Concrete fix: require XML parse, no `VideoFile`, no `.mov`, and no media-file refs.

3. [Runbook sequencing] “Launch a known visible clip” is under-specified for FX validation. Concrete fix: name the exact test clip, preferably note 8 / layer 1 / column 1, and require high-contrast visible output before pressing FX notes 1-5.

OPTIONAL / NICE-TO-HAVE:
1. Add source `.avc`, preset XML, and manifest SHA-256 values to the run log.
2. Add a one-page human table generated from the manifest for live testing.

CUT THESE:
1. [Manifest builder] Cut `fx_row_paint.py` from the manifest contract unless it becomes an acceptance tool. It is currently a separate one-shot painter (`C:\Art Projects\Res_Fable\fx_row_paint.py:49-54`), while the runbook requires painters stopped.
2. [Runbook sequencing] Cut “optionally clear LEDs” from required teardown. It is not needed to prove the map or color set and can remain an operator convenience outside acceptance.

VERIFY-AT-BUILD checklist:
1. Verify Text Block specimen schema from Avenue 7.27 before cloning: `ParamText`, `ParamColor`, and any background/source color fields.
2. Verify the specimen renders legibly in Avenue 7.27 before cloning.
3. Verify `C:\Art Projects\Res_Fable\apc40_led_test.py` path, CLI, selected port, and return codes before making it a required acceptance test.
4. Verify which LED status byte is the accepted bright solid path on hardware: 0x90, 0x95, or 0x96.
5. Verify the frozen velocity→RGB/`ParamColor` palette against both hardware LEDs and Avenue-rendered screen color.
6. Verify decoded preset map from `controllers\APC 40 MK II - React v4.4.xml`: notes 1-5 are FX bypass shortcuts, note 7 is `/composition/bypassed`, and notes 0/6 have no 0x90 shortcut.
7. Verify post-build `.avc` parses, introduces no new duplicate `uniqueId`s, contains exactly 32 test clips on the frozen layer/column map, has non-empty Text Block text, and contains no media-file refs.