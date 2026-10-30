# PR #27 evidence (Grok)

Evidence for https://github.com/Dovonun/android-launcher/pull/27. This orphan branch shares no history with the code and is not part of the PR.

- Base: `177c6c522f6333469348f177c1e625dc74402b56`
- Heads tested: `5378156a02e1013569bde35b262fe79dcb24af61` (round 2), `1e8f4fdc816fdb5d46ef0fe2855fb5d374b38531` (round 3, before the dedup fix), `da6e37b92b6541256348a9c0c8ad5d5eb9f456b9` (round 3, final).
- Emulator: AVD `pixel_gapis`, API 30 Google APIs x86, 1080x1920, 420 dpi, headless, `-gpu swiftshader_indirect -accel off` (no KVM). `adbd` runs as root, which is used for `sqlite3` reads and `am start` of the non-exported-permission activity.
- Log timestamps are device local time, Europe/Zurich (UTC+1).

## build/
- `ni-sdkext.init.gradle`: the exact out-of-repo init script passed with `-I`. It sets `compileSdkExtension = 18` because `android-36-ext1` is not published, and adds `x86` to `abiFilters` so the APK installs on the x86 AVD. It makes no repository changes.
- `ci-build-<sha>.log`: output of `./gradlew lint test assembleDebug assembleDevRelease --quiet -I ni-sdkext.init.gradle -Dorg.gradle.jvmargs=-Xmx2g --no-daemon` (with `ANDROID_HOME=~/Android/Sdk`) for each head. `EXIT=0` is the Gradle exit code.
- Dev debug APK sha256: 5378156 `00bf204dae1cc758e06d4e49d9009ffe81b96d2349a7a94b4745e5edf48ed161`, 1e8f4fd `68f72d5cef2b9019802dd6cd9815461a7d4680f488ef5634a495c9175a15a227`, da6e37b `4ea292c2c25e993a5347c70c12301be3a2b299d515ae260bf32beac66faff5bb`. The fault-injection APK (5378156 + diff) is `c2adc78dfa8b6abdd395c80f80faa0bb537357b37855fef53a0d351e576ed345`.

## fault-injection/
- `fault-injection.diff`: the exact one-line change applied on top of 5378156 for the throwaway failed-save build. It was never committed; the committed APK was reinstalled afterwards.
- `fault-logcat.txt`: logcat lines for `PinShortcutActivity` from that run (`Log.e` with stack trace; no `FATAL`).

## lifecycle/ (round 3)
Each file contains the command, the activity-manager event log for `PinShortcutActivity` (`wm_create_activity`, `wm_on_create_called`, `wm_finish_activity`, `wm_on_destroy_called`), the relevant logcat lines, and the Pinned (`tagId=2`) rows from `launcher.db` afterwards (`itemOrder|packageName|shortcutId|labelOverride`).
- `a-invalid-request.txt`: `CONFIRM_PIN_SHORTCUT` with no `PinItemRequest` extra.
- `b-fresh-request-1.txt` / `b-fresh-request-2.txt`: two separate `requestPinShortcut` calls for the same shortcut id from the helper app.
- `c-recreate-*.txt`: `cmd uimode night yes|no` sent while pinning, to force a configuration-change relaunch.
- `persistence-after-force-stop.txt`: rows before and after `am force-stop` plus relaunch.
- `before-fix-1e8f4fd/`: the same invalid and fresh-request checks on 1e8f4fd, showing the duplicate Pinned row that da6e37b fixes.

## pinhelper/
Source of the throwaway helper app (`dev.ni.pinhelper`, not part of the PR). Its only activity calls `ShortcutManager.requestPinShortcut` for a shortcut with a fixed id (extras `id`, `label`) and then finishes. It is used to make fresh pin requests for the same shortcut id.

## screenshots/
- `round2-5378156/`: bottom anchoring, add/remove favorites, Chrome pin, popup with saved label, fault-injection run, and overflow (home Favorites and the 15-entry tag popup).
- `round3-da6e37b/`: home and All Apps after force-stop and relaunch, with the pinned helper shortcuts listed once each.

## anr/
- `anr-index.tsv`: every ANR trace on the emulator from both rounds (file, process). Most are Google/system processes (gms, phone, YouTube Music, and others), which is expected with software emulation.
- `anr_*.txt`: the 3 traces for `com.ni.launcher.dev`, all from round 2 (07:56–08:05). In two of them the launcher main thread is running Compose measure/draw (All Apps `LazyColumn` measure, graphics-layer draw). In the third it is idle in `Looper.pollOnce`. There were no launcher ANRs during round 3.
