set -e
E=/home/box/pr29-evidence; cd /home/box/android-launcher-graph
export JAVA_HOME=/home/box/jdk/jdk-17.0.21+9 PATH=/home/box/jdk/jdk-17.0.21+9/bin:$PATH ANDROID_HOME=~/Android/Sdk
B() { ./gradlew :app:assembleDevDebug --quiet -I $E/emu-abi.init.gradle -Dorg.gradle.jvmargs=-Xmx2g --no-daemon 2>&1 | grep -E "^e:|FAIL" && exit 1 || true; cp app/build/outputs/apk/dev/debug/ni-launcher-dev-debug.apk $E/apks/$1.apk; echo built $1; }
R() { git checkout -q $1 -- app/src/main; }
[ "$1" = new ] && { B final-dev-debug; python3 $E/inject.py new; git diff -- app/src/main/java/com/ni/launcher/data/RoomGraphPersister.kt > $E/p2-fault-injection-on-fix.diff; B new-inject; R HEAD; }
[ "$1" = old ] && { R 76e90cc; git apply $E/stage4-delay.diff; B old-delay; R 76e90cc; python3 $E/inject.py old; git diff 76e90cc -- app/src/main > $E/p2-fault-injection-on-old.diff; B old-inject; R HEAD; }
git status --short | grep -v '^??' | grep -v e2e/build || echo clean
