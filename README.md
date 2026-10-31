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

# Round 3: focused checks on 21ffad5 (2026-10-31, 09:15–09:48 Europe/Zurich)
Same final debug APK (`21ffad5`, emulator abi init script) and emulator. adbd runs as root, so `db.sh` / `pin.sh` read `launcher.db` with sqlite3.

## 1. Tag rename + delete survive force-stop and relaunch
Created "Settings Tag" (id 3) and "Chrome Tag" (id 4) and opened Tag Manager from the context-sheet badge. Renamed tag 4 to **Renamed29** with the pencil.
The first rename attempt hit tag 3 and an IME leftover produced "yRenamed29". Then long-pressed tag 3 → **Delete**.
- `r3/rename-delete-db-0-created.txt` → `r3/rename-delete-db-1-before-force-stop.txt` → (`am force-stop`, HOME) → `r3/rename-delete-db-2-after-relaunch.txt`:
  after the relaunch the tags are `Favorites`, `Renamed29`. Tag 3 and its items are gone, and Favorites holds only tag 4.
- Screenshots: `shots/r3/rd-1-tag-manager.png`, `rd-3-delete-dialog.png`, `rd-4-after-rename-delete.png`, `rd-5-tag-manager-after-relaunch.png`.

## 2. Real CONFIRM_PIN_SHORTCUT pin + re-pin
Helper: `r3/pinhelper29/` is the PR 27 `pinhelper` (evidence/pr27 @ 3b77085) with one addition, `DynActivity`, a launcher activity that
sets dynamic shortcuts. `PinActivity` calls `ShortcutManager.requestPinShortcut`. Script: `pin.sh`.
- `r3/pin-1-first.txt`: id `r29`, label "Saved R29". Contains `START ... CONFIRM_PIN_SHORTCUT ... PinShortcutActivity`, `requestPinShortcut returned true`,
  events `wm_on_create_called` → `wm_finish_activity app-request` → `wm_on_destroy_called`, system flags `PinStr` (accepted), and the Pinned row
  `2|0|SHORTCUT|dev.ni.pinhelper|r29||Saved R29`. No error logs from PinShortcutActivity, RoomGraphPersister or NiLauncher, and no FATAL.
- `r3/pin-2-repin.txt`: same id, label "Repin R29". It goes through the same CONFIRM_PIN_SHORTCUT path and leaves **one** row with the saved label "Saved R29".
- `r3/pin-3-db-after-force-stop.txt` and `shots/r3/pin-1-allapps-after-repin-and-force-stop.png`: after force-stop, All Apps lists "Saved R29" once.

## 3. Package / shortcut refresh updates the visible graph
- Dynamic shortcuts: PinHelper added to Favorites, then `DynActivity labels='Dyn A,Dyn B'`. Swiping the home row gives the popup `[Saved R29, Dyn B, Dyn A]`
  (`shots/r3/refresh-1-popup-dyn-a-b.png`). Then `labels='Dyn C'` → `NiGraph: shortcuts dev.ni.pinhelper updated` → popup `[Saved R29, Dyn C]`
  (`shots/r3/refresh-2-popup-dyn-c.png`, `r3/refresh-dynamic-logcat.txt`).
- Package: `adb uninstall dev.ni.pinhelper` → home shows only `Chrome` (`shots/r3/refresh-3-home-after-uninstall.png`). The saved edges stay in Room,
  unresolved (`r3/refresh-uninstall.txt`). Reinstalling → `PinHelper` is back on home (`shots/r3/refresh-4-home-after-reinstall.png`, `r3/refresh-package-logcat.txt`).
