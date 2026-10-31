E=/home/box/pr29-evidence; U="python3 $E/ui.py"; L=$E/p2-$1-logcat.txt
F() { adb logcat -d -v time | grep -E "TEST-ONLY|graph flush failed|GraphPersistException|kept dirty|dropping batch|FATAL|AndroidRuntime: " | grep -vE "^\s+at " | cut -c1-220; }
adb shell setprop debug.ni.failwrites 0; adb shell setprop debug.ni.holdwrites 0
adb install -r $E/apks/$2.apk >/dev/null || exit 1
adb shell pm clear com.ni.launcher.dev >/dev/null; adb shell cmd package set-home-activity com.ni.launcher.dev/com.ni.launcher.MainActivity >/dev/null
adb logcat -c; adb shell input keyevent HOME; sleep 30
echo "### A: held transaction"; adb shell setprop debug.ni.holdwrites 1
$U addfav Settings; adb shell am start -a android.settings.SETTINGS >/dev/null; sleep 50; adb shell setprop debug.ni.holdwrites 0
echo "### B: batch + resync fail"; adb shell setprop debug.ni.failwrites 1; adb shell input keyevent HOME; sleep 8
$U addfav Chrome; sleep 3; adb exec-out screencap -p > $E/shots/p2-$1-B-two-favs-in-memory.png
adb shell am start -a android.settings.SETTINGS >/dev/null; sleep 15
echo "### C: writes recover, flush again"; adb shell setprop debug.ni.failwrites 0; adb shell input keyevent HOME; sleep 8
adb shell am start -a android.settings.SETTINGS >/dev/null; sleep 15
F; adb logcat -d -v time > $L
echo "### D: force-stop + cold start, home rows:"; adb shell am force-stop com.ni.launcher.dev; adb shell input keyevent HOME; sleep 40; $U texts
adb exec-out screencap -p > $E/shots/p2-$1-D-after-restart.png
