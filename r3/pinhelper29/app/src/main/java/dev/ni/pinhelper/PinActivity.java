package dev.ni.pinhelper;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.ShortcutInfo;
import android.content.pm.ShortcutManager;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;

// Throwaway test helper (not part of the PR): requests a pin for a shortcut with a fixed id.
public class PinActivity extends Activity {
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        String id = getIntent().getStringExtra("id");
        if (id == null) id = "r3-fixed";
        String label = getIntent().getStringExtra("label");
        if (label == null) label = "Helper " + id;
        ShortcutManager sm = getSystemService(ShortcutManager.class);
        ShortcutInfo si = new ShortcutInfo.Builder(this, id)
                .setShortLabel(label)
                .setIntent(new Intent(Intent.ACTION_VIEW, Uri.parse("https://example.com/" + id)))
                .build();
        boolean ok = sm.requestPinShortcut(si, null);
        Log.i("PinHelper", "requestPinShortcut id=" + id + " label=" + label + " returned " + ok);
        finish();
    }
}
