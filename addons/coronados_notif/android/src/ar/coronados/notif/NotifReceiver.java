package ar.coronados.notif;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.util.HashSet;
import java.util.Set;

/** Muestra las notificaciones agendadas y hace el chequeo en segundo plano. */
public class NotifReceiver extends BroadcastReceiver {
    static final String ACTION_SHOW = "ar.coronados.notif.SHOW";
    static final String ACTION_CHECK = "ar.coronados.notif.CHECK";
    static final String CHANNEL = "juego";
    static final int ID_UPDATE = 20;
    static final int ID_FRIENDS = 21;

    @Override
    public void onReceive(Context context, Intent intent) {
        final Context c = context.getApplicationContext();
        String action = intent.getAction();
        if (ACTION_SHOW.equals(action)) {
            show(c, intent.getIntExtra("id", 1), intent.getStringExtra("title"), intent.getStringExtra("text"));
        } else if (ACTION_CHECK.equals(action)) {
            final PendingResult pr = goAsync();
            new Thread(new Runnable() {
                @Override
                public void run() {
                    try {
                        check(c);
                    } catch (Exception ignored) {
                        // sin internet o token vencido: se reintenta en el próximo chequeo
                    } finally {
                        pr.finish();
                    }
                }
            }).start();
        }
    }

    static void show(Context c, int id, String title, String text) {
        NotificationManager nm = (NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE);
        if (nm == null || title == null) return;
        if (Build.VERSION.SDK_INT >= 26 && nm.getNotificationChannel(CHANNEL) == null) {
            NotificationChannel ch = new NotificationChannel(CHANNEL, "Avisos del juego", NotificationManager.IMPORTANCE_DEFAULT);
            ch.setDescription("Ganancias listas, eventos, amigos y versiones nuevas");
            nm.createNotificationChannel(ch);
        }
        Intent open = c.getPackageManager().getLaunchIntentForPackage(c.getPackageName());
        PendingIntent tap = open == null ? null : PendingIntent.getActivity(c, id, open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        int icon = c.getResources().getIdentifier("icon_monochrome", "mipmap", c.getPackageName());
        if (icon == 0) icon = c.getApplicationInfo().icon;
        Notification.Builder b = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(c, CHANNEL) : new Notification.Builder(c);
        b.setSmallIcon(icon).setContentTitle(title).setContentText(text).setAutoCancel(true)
                .setStyle(new Notification.BigTextStyle().bigText(text));
        if (tap != null) b.setContentIntent(tap);
        nm.notify(id, b.build());
    }

    // ------------------------------------------------------------------ red

    static String http(String method, String url, String body, String contentType, String bearer) throws Exception {
        HttpURLConnection h = (HttpURLConnection) new URL(url).openConnection();
        h.setConnectTimeout(15000);
        h.setReadTimeout(15000);
        h.setRequestMethod(method);
        h.setRequestProperty("User-Agent", "CoronadosDeGloria");
        if (bearer != null) h.setRequestProperty("Authorization", "Bearer " + bearer);
        if (body != null) {
            h.setDoOutput(true);
            h.setRequestProperty("Content-Type", contentType);
            OutputStream o = h.getOutputStream();
            o.write(body.getBytes("UTF-8"));
            o.close();
        }
        int code = h.getResponseCode();
        if (code < 200 || code >= 300) throw new Exception("HTTP " + code);
        InputStream in = h.getInputStream();
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buf = new byte[4096];
        int n;
        while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
        in.close();
        return out.toString("UTF-8");
    }

    static void check(Context c) throws Exception {
        SharedPreferences sp = c.getSharedPreferences(CoronadosNotif.PREFS, Context.MODE_PRIVATE);
        JSONObject cfg = new JSONObject(sp.getString("config", "{}"));
        if (!cfg.optBoolean("on", false)) return;
        // 1) Versión nueva publicada (repositorio público de descargas)
        String rel = cfg.optString("releases_url", "");
        if (!rel.isEmpty()) {
            try {
                JSONObject r = new JSONObject(http("GET", rel, null, null, null));
                String tag = r.optString("tag_name", "").replaceFirst("^v", "");
                String mine = cfg.optString("version", "");
                if (!tag.isEmpty() && !tag.equals(mine) && !tag.equals(sp.getString("notified_version", ""))) {
                    sp.edit().putString("notified_version", tag).apply();
                    show(c, ID_UPDATE, "¡Nueva versión " + tag + "!", "Hay una actualización de Coronados de Gloria esperándote. Entrá a ver las novedades.");
                }
            } catch (Exception ignored) {
            }
        }
        // 2) Solicitudes de amistad nuevas (Firestore REST con la sesión del juego)
        String key = cfg.optString("api_key", ""), refresh = cfg.optString("refresh_token", "");
        String uid = cfg.optString("uid", ""), project = cfg.optString("project", "");
        if (key.isEmpty() || refresh.isEmpty() || uid.isEmpty() || project.isEmpty()) return;
        JSONObject tok = new JSONObject(http("POST", "https://securetoken.googleapis.com/v1/token?key=" + URLEncoder.encode(key, "UTF-8"),
                "grant_type=refresh_token&refresh_token=" + URLEncoder.encode(refresh, "UTF-8"), "application/x-www-form-urlencoded", null));
        String id = tok.optString("id_token", "");
        if (id.isEmpty()) return;
        JSONObject list = new JSONObject(http("GET", "https://firestore.googleapis.com/v1/projects/" + project
                + "/databases/(default)/documents/players/" + uid + "/requests?pageSize=20", null, null, id));
        JSONArray docs = list.optJSONArray("documents");
        if (docs == null) return;
        Set<String> seen = new HashSet<>(sp.getStringSet("seen_requests", new HashSet<>()));
        String who = null;
        int fresh = 0;
        for (int i = 0; i < docs.length(); i++) {
            JSONObject d = docs.getJSONObject(i);
            String name = d.optString("name", "");
            if (seen.contains(name)) continue;
            seen.add(name);
            fresh++;
            JSONObject f = d.optJSONObject("fields");
            if (f != null && f.optJSONObject("company") != null) who = f.getJSONObject("company").optString("stringValue", null);
        }
        sp.edit().putStringSet("seen_requests", seen).apply();
        if (fresh > 0) {
            String text = fresh == 1 && who != null ? who + " quiere ser tu amigo. Entrá a aceptar la solicitud."
                    : fresh + " solicitudes de amistad nuevas te esperan.";
            show(c, ID_FRIENDS, "Solicitud de amistad", text);
        }
    }
}
