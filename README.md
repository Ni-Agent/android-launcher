# PR 29 evidence (Grok / Mai)

PR: https://github.com/Dovonun/android-launcher/pull/29
Head tested: `21ffad5a7e4a6926cb9cf8b04b7f2a5ff6245681` (app code identical to `30cdcff`; 21ffad5 only hardens the e2e row reader).
Base: `7b032409e0de31f2300d11108cdd8391eac90b99`. "Before" runs use the previous head `76e90ccae7b2f643e1f4e1665029e07d8bfa510c`.
Emulator: pixel_gapis (API 30, x86 image), swiftshader, no KVM (`-accel off`). Debug APKs for the emulator are built with
`emu-abi.init.gradle`, which adds x86/x86_64 to the app's arm64-only `abiFilters`. Local build only, nothing committed.

## Build (CI command, exact head)
- `build-final.log`: `./gradlew lint test assembleDebug assembleDevRelease` → EXIT 0.

## P1: Manage Tag before shortcut discovery must keep saved shortcuts
e2e test `manageTagBeforeShortcutsLoadKeepsSavedShortcuts`. It creates "Settings Tag" (Settings plus 3 shortcuts), cold-starts with
shortcut discovery held, opens Manage Tag (only the app is resolved), confirms, restarts, and compares Manage rows.
- Before (76e90cc + TEST-ONLY `stage4-delay.diff`): **FAIL**, `expected [Add items…, Battery, Data usage, Wi‑Fi, Settings] but was [Add items…, Settings]`.
  `p1-before-76e90cc-e2e.txt`, `p1-before-76e90cc-logcat.txt`, `shots/p1-before-76e90cc-failure.png`
- After (21ffad5, shipped debug-only hold via `setprop log.tag.NiE2EHoldShortcuts DEBUG`): **PASS**. The test now asserts that the hold
  happened and that Manage opened with only the app; it no longer skips. The logcat shows `holding shortcut discovery for 30000 ms`.
  `p1-after-21ffad5-e2e.txt`, `p1-after-21ffad5-logcat.txt`, `shots/p1-after-21ffad5-end.png`
- Full suite on 21ffad5: **OK (5 tests)**, no skips, 0 FATAL. `e2e-full-21ffad5.txt`, `e2e-full-21ffad5-logcat.txt`

## P2: flush() durability contract (TEST-ONLY fault injection, not committed)
`inject.py` patches RoomGraphPersister: `debug.ni.holdwrites=1` holds the write transaction for 45 s, and `debug.ni.failwrites=1` makes
writeBatch throw SQLiteConstraintException and writeFull throw too. It also adds flush/markPersisted logs. Diffs:
`p2-fault-injection-on-fix.diff` (against the fixed head) and `p2-fault-injection-on-old.diff` (against 76e90cc). Script: `run-p2.sh`.
Results (`p2-fix-21ffad5-summary.txt`, `p2-fix-21ffad5-logcat.txt`, times Europe/Zurich):
- A, held transaction: `holding transaction v6` 08:35:33 → `flush(v6) waiting` 08:35:43 → `releasing` 08:36:18 → `markPersisted 0 -> 6` → `flush SUCCESS`. flush stayed suspended until the commit.
- B, batch and resync both fail: `batch v7 kept dirty, not persisted` → `flush(v7) FAILURE, watermark stays v6` → `GraphPersistException` logged by NiLauncher. No crash.
- C, writes recover: the next flush retries the kept batch → `markPersisted 6 -> 7` → SUCCESS.
- D, force-stop and cold start: home shows `['Chrome', 'Settings']`. The edit that failed at first (Chrome) was kept dirty and then saved.

## Smoke: tag reorder + remove survive a restart
`smoke-reorder-remove.txt`, `shots/smoke-*.png`: Create Tag on Settings → drag Wi‑Fi to the top → swipe-remove Battery → confirm →
force-stop → Manage shows `[Add items…, Wi‑Fi, Data usage, Settings]`.

## Not covered here
Rename/delete, pin/re-pin, and package/shortcut refresh were not re-run on this head.

## Helpers
`ui.py` (adb/uiautomator driver), `run-p1.sh`, `run-p2.sh`, `build-variants.sh`, `stage4-delay.diff`, `emu-abi.init.gradle`.
