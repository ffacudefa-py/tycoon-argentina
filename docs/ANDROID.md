# Android

## Estado (v0.5.0)

- Export **con Gradle** (necesario para el SDK de AdMob). APK
  `build/tycoon-argentina-0.5.0.apk`: arm64-v8a + armeabi-v7a + x86_64,
  librerías nativas comprimidas, targetSdk 36, vertical.
- Permisos: `VIBRATE`, `INTERNET` y `ACCESS_NETWORK_STATE` (cuentas y anuncios).
  La galería NO necesita permisos (selector del sistema).
- Firmado con el keystore de debug de esta PC (el mismo de las versiones
  anteriores), así que se instala **encima** de la 0.4 sin perder la partida.
- Etiqueta `beta` en el preset → anuncios de prueba de Google (ver MONETIZACION.md).

## Instalar en un teléfono

```bash
adb install -r build/tycoon-argentina-debug.apk
```
(o copiar el APK al teléfono y abrirlo permitiendo "orígenes desconocidos").

## Configuración usada (sin root)

- Godot 4.7.2: `~/.local/opt/godot/`, enlace `~/.local/bin/godot`.
- Plantillas: `~/.local/share/godot/export_templates/4.7.2.stable/` con sólo
  `android_debug.apk`, `android_release.apk` y `version.txt` (extraídas del `.tpz` de
  1,28 GB por HTTP Range; el disco no tenía lugar para el paquete completo).
- Editor settings (`~/.config/godot/editor_settings-4.7.tres`):
  `export/android/android_sdk_path = ~/Android/Sdk`,
  keystore de debug `~/.local/share/godot/keystores/debug.keystore` (alias
  `androiddebugkey`, clave `android`). JDK 21 del sistema.
- Plantilla Gradle: `android/build/` (NO se versiona, 207 MB). Para recrearla:
  `mkdir -p android/build && cd android/build && unzip ~/.local/share/godot/export_templates/4.7.2.stable/android_source.zip && cd .. && echo 4.7.2.stable > .build_version && touch build/.gdignore`
  (o Editor → Proyecto → Instalar plantilla de compilación de Android).
- Plugin AdMob en `addons/admob/` con sus AAR en `addons/admob/android/bin/`;
  el editor lo activa desde `[editor_plugins]` en `project.godot`.

## Exportar

```bash
# APK beta (firma de debug, la misma de siempre; anuncios de prueba)
GODOT_ANDROID_KEYSTORE_RELEASE_PATH=~/.local/share/godot/keystores/debug.keystore \
GODOT_ANDROID_KEYSTORE_RELEASE_USER=androiddebugkey \
GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD=android \
godot --headless --path . --export-release "Android" build/tycoon-argentina-0.5.0.apk
```
La primera compilación Gradle baja dependencias (~5–10 min); después tarda ~3 min.

## Publicar en Play Store (pendiente)

1. Crear un keystore propio y guardarlo FUERA del repo:
   `keytool -genkeypair -keystore tycoon-release.jks -alias tycoon -keyalg RSA -keysize 2048 -validity 10000`
   (ojo: cambiar de firma obliga a desinstalar la versión beta).
2. Usarlo con las variables `GODOT_ANDROID_KEYSTORE_RELEASE_*`.
3. `gradle_build/export_format=1` para generar AAB.
4. Quitar `beta` de `custom_features` y completar los IDs reales de AdMob.

## Detalles de plataforma

- Botón "atrás": cierra el modal superior; si no hay, vuelve a Imperio; en Imperio
  abre el menú principal; en el menú principal, dos toques seguidos cierran el juego
  (guardando antes).
- Guarda al pasar a segundo plano (`NOTIFICATION_APPLICATION_PAUSED`) y calcula el
  progreso offline al volver.
- Respeta el área segura (notch y barra de gestos) con `get_display_safe_area()`.
- Renderer GL Compatibility (máxima compatibilidad y menor consumo).
