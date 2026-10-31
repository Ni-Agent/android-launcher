package dev.ni.pinhelper;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.ShortcutInfo;
import android.content.pm.ShortcutManager;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import java.util.ArrayList;
import java.util.List;

// Throwaway test helper (PR 29 evidence): replaces the app's dynamic shortcuts with extra "labels" (comma-separated).
public class DynActivity extends Activity {
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        String labels = getIntent().getStringExtra("labels");
        if (labels == null) labels = "Dyn A";
        List<ShortcutInfo> list = new ArrayList<>();
        int rank = 0;
        for (String l : labels.split(",")) {
            list.add(new ShortcutInfo.Builder(this, "dyn-" + l.trim().replace(' ', '-'))
                    .setShortLabel(l.trim()).setRank(rank++)
                    .setIntent(new Intent(Intent.ACTION_VIEW, Uri.parse("https://example.com/" + l.trim())))
                    .build());
        }
        boolean ok = getSystemService(ShortcutManager.class).setDynamicShortcuts(list);
        Log.i("PinHelper", "setDynamicShortcuts " + labels + " returned " + ok);
        finish();
    }
}
