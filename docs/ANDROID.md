# Android

## Estado

- APK de debug generado y firmado: `build/tycoon-argentina-debug.apk` (≈87 MB,
  arm64-v8a + armeabi-v7a + x86_64, targetSdk 36, sólo permiso `VIBRATE`, vertical).
- **No se probó todavía en un dispositivo ni en un emulador**: el AVD `Pixel_10_Pro`
  de esta PC fue borrado (sólo quedó su `.ini`) y con ~1,5 GB libres no conviene crear
  otro. La UI sí se probó renderizada a 360×699 y 1250×640 en escritorio.

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
- Preset en `export_presets.cfg` sin Gradle (no requiere `android_source.zip`).

## Exportar

```bash
godot --headless --path . --export-debug "Android" build/tycoon-argentina-debug.apk
```

## Release (pendiente)

1. Crear un keystore propio y guardarlo FUERA del repo:
   `keytool -genkeypair -keystore tycoon-release.jks -alias tycoon -keyalg RSA -keysize 2048 -validity 10000`
2. En el preset (o variables `GODOT_ANDROID_KEYSTORE_RELEASE_PATH/USER/PASSWORD`)
   configurar la firma release.
3. `godot --headless --path . --export-release "Android" build/tycoon-argentina.apk`
4. Para Play Store se necesita AAB: activar Gradle Build, bajar `android_source.zip`
   de las plantillas (~215 MB) e instalar la plantilla en el proyecto.

## Detalles de plataforma

- Botón "atrás": cierra el modal superior o vuelve a Imperio; nunca cierra el juego.
- Guarda al pasar a segundo plano (`NOTIFICATION_APPLICATION_PAUSED`) y calcula el
  progreso offline al volver.
- Respeta el área segura (notch y barra de gestos) con `get_display_safe_area()`.
- Renderer GL Compatibility (máxima compatibilidad y menor consumo).
