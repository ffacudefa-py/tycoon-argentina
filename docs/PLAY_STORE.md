# Publicar en Google Play

Estado de la 0.7.1 frente a los requisitos de Google Play (revisado el 28/10/2026).
✅ cumplido y verificado · ⏳ falta un paso del dueño de la cuenta · ⚠️ decisión pendiente.

## Requisitos técnicos

| Requisito | Estado |
|---|---|
| API objetivo 36 (Android 16) para apps nuevas y actualizaciones desde el 31/08/2026 | ✅ `targetSdk 36` (plantilla Gradle de Godot 4.7.2; verificado con `aapt2 dump badging`) |
| Páginas de memoria de 16 KB (apps con targetSdk ≥ 35) | ✅ `libgodot_android.so` y `libc++_shared.so` con segmentos LOAD alineados a 0x4000; `zipalign -c -P 16` OK |
| 64 bits | ✅ arm64-v8a y x86_64 (además de armeabi-v7a) |
| Formato AAB | ✅ preset **"Android Play Store"** (`gradle_build/export_format=1`, sin la etiqueta `beta`) |
| Firma de subida propia | ⏳ crear el keystore (ver abajo); Play App Signing guarda la clave de la app |
| Permisos | ✅ sólo INTERNET, ACCESS_NETWORK_STATE y VIBRATE propios. El SDK de anuncios agrega AD_ID, WAKE_LOCK, FOREGROUND_SERVICE y READ_BASIC_PHONE_STATE (normales, sin diálogo) |

## Requisitos de políticas

| Requisito | Estado |
|---|---|
| Borrar la cuenta **desde la app** (apps que permiten crear cuentas) | ✅ Configuración → Cuenta → *Borrar mi cuenta*. Borra en un solo commit partida, perfil, código, amigos (de los dos lados), solicitudes y mates, y después la cuenta de Firebase. Probado de punta a punta en `tools/dev/social_check.gd` |
| Borrar la cuenta **desde la web** (sin reinstalar) | ⏳ página `web/borrar-cuenta.html` lista: falta publicarla (abajo) |
| Política de privacidad (URL en la ficha y dentro de la app) | ⏳ `web/privacidad.html` + botón en Configuración → Privacidad: falta publicarla |
| Consentimiento para anuncios en UE/Reino Unido (CMP certificado por Google) | ✅ UMP integrado; verificado en el emulador: aparece el formulario de Google antes de iniciar AdMob (`admob_ad_provider.gd`): pide consentimiento antes de iniciar AdMob y, si corresponde, muestra *Privacidad de los anuncios* en Configuración. ⏳ crear el mensaje GDPR en AdMob → Privacidad y mensajes |
| Anuncios reales | ⏳ cuenta AdMob, IDs de producción en `data/ads.json` y `project.godot`, `app-ads.txt` (MONETIZACION.md). Sin IDs, la versión de Play sale **sin anuncios** y el juego lo dice |
| Público objetivo | ⚠️ ver "Público y clasificación" |
| Contenido | ✅ sin apuestas con dinero real, sin compras, sin chat ni contenido generado por usuarios (sólo el nombre de la empresa, máx. 40 letras, visible para amigos) |

## Publicar las páginas legales

1. Responsable y contacto ya completados (Facundo Nahuel Defagot · facundo.n.defagot@gmail.com).
2. Con la cuenta dueña del proyecto (`firebase login --reauth`; la cuenta benjann8080 no tiene
   permiso sobre coronadosdegloria): `firebase deploy --only hosting --project coronadosdegloria` (Node 22: `~/.local/opt/node22/bin`).
   Quedan en `https://coronadosdegloria.web.app/privacidad.html` y `/borrar-cuenta.html`
   (las mismas URLs que usa el juego, `data/legal.json`).
3. Cargar las dos URLs en Play Console (Contenido de la app → Política de privacidad y
   Seguridad de los datos → Eliminación de datos).

## Reglas de Firestore

`firestore.rules` valida desde la 0.7.1 los campos y tamaños de cada documento y deja
borrar código y mates propios (borrado de cuenta). Probar y publicar:

```bash
export PATH=~/.local/opt/node22/bin:$PATH
TYCOON_EMULATOR=127.0.0.1 firebase emulators:exec --only auth,firestore --project coronadosdegloria \
  "godot --headless --path . -s res://tools/dev/social_check.gd -- --dev-save=user://social_check_save.json"
firebase deploy --only firestore:rules --project coronadosdegloria
```
**Publicar las reglas junto con la 0.7.1**: la 0.7.0 no borra cuentas, pero el resto
de lo que escribe ya cumple las reglas nuevas (mismos campos).

## Keystore de subida y AAB

```bash
keytool -genkeypair -v -keystore ~/claves/tycoon-upload.jks -alias tycoon-upload \
  -keyalg RSA -keysize 2048 -validity 10000
GODOT_ANDROID_KEYSTORE_RELEASE_PATH=~/claves/tycoon-upload.jks \
GODOT_ANDROID_KEYSTORE_RELEASE_USER=tycoon-upload \
GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD='…' \
godot --headless --path . --export-release "Android Play Store" build/tycoon-argentina-0.7.1.aab
```
Guardar el `.jks` y la contraseña fuera del repo y con copia de respaldo. Activar
Play App Signing al subir el primer AAB (si se pierde la clave de subida, Google
permite cambiarla).

## Formulario "Seguridad de los datos" (respuestas)

- ¿Recopila o comparte datos? **Sí**. ¿Cifrados en tránsito? **Sí**. ¿Se pueden borrar? **Sí** (app y web).
- **Información personal → Dirección de email**: recopilada, no compartida; obligatoria sólo para
  cuentas (la app se usa sin cuenta → *opcional*); fines: *Funcionalidad de la app*, *Administración de la cuenta*.
- **Información personal → IDs de usuario** (uid de Firebase): igual que el email.
- **Actividad en la app → Otro contenido generado por el usuario** (nombre de la empresa en el
  perfil público): recopilado, opcional, *Funcionalidad de la app*.
- **Actividad en la app → Interacciones en la app / progreso** (partida en la nube): recopilado, opcional, *Funcionalidad de la app*.
- **IDs de dispositivo u otros → ID de publicidad**: recopilado y **compartido** con Google (AdMob);
  fines: *Publicidad o marketing*, *Estadísticas*, *Prevención de fraudes*. Sólo si la versión tiene anuncios.
- **Información y rendimiento de la app → Diagnóstico**: lo recopila el SDK de AdMob (mismo caso).
- No se recopilan: ubicación, contactos, fotos (la de perfil queda en el teléfono), mensajes, finanzas, salud.

Declaraciones aparte en Contenido de la app: **Anuncios: Sí** (si hay IDs de producción;
si no, *No*), **ID de publicidad: Sí, se usa para publicidad** (lo declara el SDK aunque no
haya anuncios: responder según la versión), **Acceso a la app**: no requiere credenciales para
revisar (se juega como invitado).

## Público y clasificación ⚠️

- **Público objetivo**: recomendado **13 años o más** (o 16+ para simplificar el RGPD). Si se
  incluyen menores de 13, aplica la política de Familias: anuncios sólo de SDKs certificados
  para familias, sin ID de publicidad, y `tag_for_under_age_of_consent`; hoy el juego no está
  preparado para eso.
- **Cuestionario IARC**: juego de simulación sin violencia ni lenguaje fuerte; *no* hay apuestas
  (la animación "estilo casino" del saldo es sólo un contador, no se apuesta nada); interacción
  entre usuarios limitada (amigos por código, sin chat). Resultado esperado: PEGI 3 / Todos.
- Ficha: capturas en `build/shots_360x740/` (Play pide al menos 2, 16:9 o 9:16, lado mínimo 320 px),
  ícono 512×512 y gráfico de 1024×500 (pendientes).

## Cuentas de prueba para cerrar la prueba

Las cuentas personales nuevas de Play Console deben hacer una **prueba cerrada con al menos
12 testers durante 14 días** antes de poder publicar en producción.
