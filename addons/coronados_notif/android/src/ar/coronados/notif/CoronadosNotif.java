package ar.coronados.notif;

import android.app.Activity;
import android.app.AlarmManager;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;

import org.godotengine.godot.Godot;
import org.godotengine.godot.plugin.GodotPlugin;
import org.godotengine.godot.plugin.UsedByGodot;

/**
 * Notificaciones locales de Coronados de Gloria (15.0). Sin librerías externas:
 * AlarmManager + BroadcastReceiver (NotifReceiver) + NotificationManager.
 *
 * Desde GDScript (autoload PushNotifications):
 *   schedule(id, título, texto, epoch_ms)   una notificación a una hora
 *   cancel(id) / cancelAll()
 *   configureCheck(json)                    chequeo cada ~6 h en segundo plano:
 *                                           versión nueva y solicitudes de amistad
 *   enabled()                               el sistema permite notificaciones
 */
public class CoronadosNotif extends GodotPlugin {
    static final String PREFS = "coronados_notif";
    static final int CHECK_REQUEST = 900;

    public CoronadosNotif(Godot godot) {
        super(godot);
    }

    @Override
    public String getPluginName() {
        return "CoronadosNotif";
    }

    private Context ctx() {
        Activity a = getActivity();
        return a != null ? a.getApplicationContext() : null;
    }

    static PendingIntent showIntent(Context c, int id, String title, String text) {
        Intent i = new Intent(c, NotifReceiver.class);
        i.setAction(NotifReceiver.ACTION_SHOW);
        i.putExtra("id", id);
        i.putExtra("title", title);
        i.putExtra("text", text);
        return PendingIntent.getBroadcast(c, id, i, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    static PendingIntent checkIntent(Context c) {
        Intent i = new Intent(c, NotifReceiver.class);
        i.setAction(NotifReceiver.ACTION_CHECK);
        return PendingIntent.getBroadcast(c, CHECK_REQUEST, i, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    @UsedByGodot
    public void schedule(int id, String title, String text, long atMillis) {
        Context c = ctx();
        if (c == null) return;
        AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE);
        if (am == null) return;
        PendingIntent pi = showIntent(c, id, title, text);
        // Inexacta: no hace falta el permiso de alarmas exactas y cuida la batería.
        if (Build.VERSION.SDK_INT >= 23) {
            am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, atMillis, pi);
        } else {
            am.set(AlarmManager.RTC_WAKEUP, atMillis, pi);
        }
    }

    @UsedByGodot
    public void cancel(int id) {
        Context c = ctx();
        if (c == null) return;
        AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE);
        if (am != null) am.cancel(showIntent(c, id, "", ""));
        NotificationManager nm = (NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE);
        if (nm != null) nm.cancel(id);
    }

    @UsedByGodot
    public boolean enabled() {
        Context c = ctx();
        if (c == null) return false;
        NotificationManager nm = (NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE);
        return nm != null && (Build.VERSION.SDK_INT < 24 || nm.areNotificationsEnabled());
    }

    /** json: {"on", "api_key", "refresh_token", "uid", "project", "releases_url", "version"} ("on": false lo apaga). */
    @UsedByGodot
    public void configureCheck(String json) {
        Context c = ctx();
        if (c == null) return;
        SharedPreferences.Editor ed = c.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit();
        ed.putString("config", json);
        ed.apply();
        AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE);
        if (am == null) return;
        PendingIntent pi = checkIntent(c);
        am.cancel(pi);
        if (json.contains("\"on\":true")) {
            long every = AlarmManager.INTERVAL_HOUR * 6;
            am.setInexactRepeating(AlarmManager.RTC_WAKEUP, System.currentTimeMillis() + every, every, pi);
        }
    }
}
