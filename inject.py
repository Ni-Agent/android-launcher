# TEST-ONLY fault injection for RoomGraphPersister (never committed). Usage: python3 inject.py old|new
import sys
p='app/src/main/java/com/ni/launcher/data/RoomGraphPersister.kt'; s=open(p).read()
def rep(a,b):
    global s
    assert a in s, a
    s=s.replace(a,b,1)
rep('''    private suspend fun writeBatch(b: Batch) {
''','''    private suspend fun writeBatch(b: Batch) {
        if (failWrites()) throw SQLiteConstraintException("TEST-ONLY injected writeBatch failure v${b.version}")
        if (prop("debug.ni.holdwrites")) {
            Log.i(LOG_TAG, "TEST-ONLY holding transaction for v${b.version} 45 s")
            delay(45_000)
            Log.i(LOG_TAG, "TEST-ONLY releasing transaction for v${b.version}")
        }
''')
rep('''    private suspend fun writeFull(user: UserData) {
''','''    private suspend fun writeFull(user: UserData) {
        if (failWrites()) throw SQLiteConstraintException("TEST-ONLY injected writeFull failure")
''')
rep('''    private fun markPersisted(version: Long) {
''','''    // TEST-ONLY fault injection: `adb shell setprop debug.ni.failwrites 1`
    private fun prop(name: String): Boolean = try {
        Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
            .invoke(null, name) == "1"
    } catch (_: Exception) { false }
    private fun failWrites() = prop("debug.ni.failwrites")

    private fun markPersisted(version: Long) {
        Log.i(LOG_TAG, "TEST-ONLY markPersisted(v$version) watermark ${persisted.value} -> ${maxOf(version, persisted.value)}")
''')
if sys.argv[1]=='old':
    rep('''        if (persisted.value >= target) return
''','''        if (persisted.value >= target) {
            Log.i(LOG_TAG, "TEST-ONLY flush(v$version) target=v$target -> SUCCESS immediately (watermark v${persisted.value})")
            return
        }
''')
    rep('''        persisted.first { it >= target }
    }''','''        Log.i(LOG_TAG, "TEST-ONLY flush(v$version) target=v$target waiting")
        persisted.first { it >= target }
        Log.i(LOG_TAG, "TEST-ONLY flush(v$version) target=v$target -> SUCCESS (watermark v${persisted.value})")
    }''')
else:
    rep('''        if (persisted.value >= target) return
''','''        if (persisted.value >= target) {
            Log.i(LOG_TAG, "TEST-ONLY flush(v$version) target=v$target -> SUCCESS immediately (watermark v${persisted.value})")
            return
        }
''')
    rep('''        val seen = failure.value
''','''        Log.i(LOG_TAG, "TEST-ONLY flush(v$version) target=v$target waiting")
        val seen = failure.value
''')
    rep('''        if (p >= target) return
        throw GraphPersistException''','''        if (p >= target) {
            Log.i(LOG_TAG, "TEST-ONLY flush(v$version) target=v$target -> SUCCESS (watermark v$p)")
            return
        }
        Log.i(LOG_TAG, "TEST-ONLY flush(v$version) target=v$target -> FAILURE, watermark stays v${persisted.value}")
        throw GraphPersistException''')
open(p,'w').write(s)
