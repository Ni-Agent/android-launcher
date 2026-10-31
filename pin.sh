# usage: pin.sh <name> <id> <label>
E=/home/box/pr29-evidence; O=$E/r3/pin-$1.txt
adb logcat -c; adb logcat -b events -c
echo "== $1: am start dev.ni.pinhelper/.PinActivity --es id $2 --es label '$3'" > $O
adb shell am start -n dev.ni.pinhelper/.PinActivity --es id "$2" --es label "'$3'" >> $O
sleep 30
echo "-- events (PinShortcutActivity)" >> $O; adb logcat -d -b events -v time | grep PinShortcutActivity >> $O
echo "-- main (PinHelper / PinShortcutActivity / RoomGraphPersister / NiLauncher / FATAL)" >> $O
adb logcat -d -v time | grep -E "PinHelper|PinShortcutActivity|RoomGraphPersister|NiLauncher|FATAL|CONFIRM_PIN" >> $O
echo "-- system shortcut state" >> $O; adb shell dumpsys shortcut | grep -A3 "id=$2" | grep -E "id=|flags" | head -4 >> $O
echo "-- launcher.db Pinned (tagId=2) rows: tagId|itemOrder|type|pkg|shortcutId|target|labelOverride" >> $O
adb shell "sqlite3 /data/data/com.ni.launcher.dev/databases/launcher.db \"select 'tag',id,name from tags where id=2; select tagId,itemOrder,type,packageName,shortcutId,targetTagId,labelOverride from tag_items where tagId=2 order by itemOrder;\"" >> $O
cat $O
