# PR #30 evidence (Grok)

Evidence for https://github.com/Dovonun/android-launcher/pull/30 ("Stop tracking e2e build outputs"). This orphan branch shares no history with the code and is not part of the PR.

- Head tested: `9e05d314323da7ea93cc96afa92ef7e1216feb36` (branch `Ni-Agent:chore/untrack-e2e-build`)
- Base: `7b032409e0de31f2300d11108cdd8391eac90b99` (`Dovonun/android-launcher` `main`; it had not moved when this was run)
- Run on: 2026-10-31, 06:25–06:29 Europe/Zurich (UTC+1), in worktree `/home/box/android-launcher-untrack`, OpenJDK 21.0.12.1, Gradle wrapper 8.13, `ANDROID_HOME=~/Android/Sdk`.
- Flags used for every Gradle call (`$F` below): `-I /tmp/ni-sdkext.init.gradle -Dorg.gradle.jvmargs=-Xmx2g --no-daemon`
- Each log starts with the exact command line and ends with `exit=<code>` (the shell exit code).

## build/
- `ni-sdkext.init.gradle`: the exact out-of-repo init script passed with `-I`. It sets `compileSdkExtension = 18` (because `android-36-ext1` is not published) and adds `x86` to `abiFilters`. It makes no repository changes.
- `00-clean.log`: `git rev-parse HEAD`, `./gradlew clean $F` (exit 0), `rm -rf e2e/build app/build` (exit 0), `ls -d e2e/build app/build` showing both are gone, and `git status --porcelain` (empty).
- `01-lint-test-assemble.log`: `./gradlew lint test assembleDebug assembleDevRelease $F` from that clean state. `BUILD SUCCESSFUL`, 224 tasks (221 executed, 3 up-to-date), exit 0. `assembleDebug` covers every project, so the e2e APK is rebuilt from scratch here as well (`:e2e:packageDebug`, `:e2e:assembleDebug` executed).
- `02-e2e-assembleDebug.log`: `./gradlew :e2e:assembleDebug $F` right after that. `BUILD SUCCESSFUL`, 29 tasks all up-to-date (already built by step 01), exit 0.
- `03-e2e-isolated-rebuild.log`: `rm -rf e2e/build`, then `./gradlew :e2e:assembleDebug --rerun-tasks $F`. This is an e2e-only rebuild with nothing reused: `BUILD SUCCESSFUL`, 29 tasks all executed, exit 0.
- `04-git-checks.log`: after the builds, with the e2e APK present:
  - `git rev-parse HEAD` gives `9e05d314323da7ea93cc96afa92ef7e1216feb36`
  - `git status --porcelain` is empty (exit 0)
  - `git status --ignored --porcelain` lists only `.gradle/`, `app/build/`, `e2e/build/` as ignored
  - `git ls-files e2e/build | wc -l` gives `0`
  - `ls -la e2e/build/outputs/apk/debug/` shows `e2e-debug.apk` (4852475 bytes) and `output-metadata.json`
  - `sha256(e2e-debug.apk)` = `e233bdef2f9fdc35bce0c959d2a103bea29384b5ed495206a5eea1904f2335c7`
  - `git check-ignore -v e2e/build/outputs/apk/debug/*.apk` gives `e2e/.gitignore:1:/build	e2e/build/outputs/apk/debug/e2e-debug.apk` (exit 0)

## Emulator
Not run. The PR only removes 190 generated files under `e2e/build/` from the index and adds `e2e/.gitignore` (`/build`). It changes no source, resource, or Gradle file, so runtime behaviour does not change.
