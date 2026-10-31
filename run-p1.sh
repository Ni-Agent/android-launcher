# usage: run-p1.sh <apk-name> <label>
E=/home/box/pr29-evidence; T=com.ni.launcher.e2e.LauncherE2ETest#manageTagBeforeShortcutsLoadKeepsSavedShortcuts
adb install -r -t $E/apks/final-e2e-debug.apk >/dev/null
adb install -r $E/apks/$1.apk || exit 1
adb logcat -c; adb shell rm -rf /data/local/tmp/ni-e2e
adb shell am instrument -w -r -e class $T com.ni.launcher.e2e/androidx.test.runner.AndroidJUnitRunner > $E/p1-$2-e2e.txt 2>&1
adb logcat -d -v time > $E/p1-$2-logcat.txt
adb pull /data/local/tmp/ni-e2e/manageTagBeforeShortcutsLoadKeepsSavedShortcuts.png $E/shots/p1-$2-failure.png 2>/dev/null
adb exec-out screencap -p > $E/shots/p1-$2-end.png
echo "== $2"; tail -4 $E/p1-$2-e2e.txt; grep -m1 -E "AssertionError|Exception" $E/p1-$2-e2e.txt
