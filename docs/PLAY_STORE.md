# Publicar en Google Play

Estado de la 15.1 frente a los requisitos de Google Play (revisado el 22/11/2026).
✅ cumplido y verificado · ⏳ falta un paso del dueño de la cuenta · ⚠️ decisión pendiente.

## Requisitos técnicos

| Requisito | Estado |
|---|---|
| API objetivo 36 (Android 16) para apps nuevas y actualizaciones desde el 31/08/2026 | ✅ `targetSdk 36` (plantilla Gradle de Godot 4.7.2; verificado con `aapt2 dump badging`) |
| Páginas de memoria de 16 KB (apps con targetSdk ≥ 35) | ✅ `libgodot_android.so` y `libc++_shared.so` con segmentos LOAD alineados a 0x4000; `zipalign -c -P 16` OK |
| 64 bits | ✅ arm64-v8a y x86_64 (además de armeabi-v7a) |
| Formato AAB | ✅ preset **"Android Play Store"** (`gradle_build/export_format=1`, sin la etiqueta `beta`) |
| Firma de subida propia | ✅ clave `coronados-upload` creada el 22/11/2026, **fuera del repo** (SHA-256 `E9:6C:55:76:…:35:1F:C6`); Play App Signing guarda la clave de la app |
| Permisos | ✅ AAB de la 15.1: INTERNET, ACCESS_NETWORK_STATE, VIBRATE, POST_NOTIFICATIONS y RECEIVE_BOOT_COMPLETED. Sin AdMob no hay AD_ID. El plugin de notificaciones declara `uses-sdk` desde la 15.1: sin eso el merger agregaba READ_PHONE_STATE y almacenamiento implícitos (están en los APK 15.0 y 15.1 de GitHub) |

## Requisitos de políticas

| Requisito | Estado |
|---|---|
| Borrar la cuenta **desde la app** (apps que permiten crear cuentas) | ✅ Configuración → Cuenta → *Borrar mi cuenta*. Borra en un solo commit partida, perfil, código, amigos (de los dos lados), solicitudes y mates, y después la cuenta de Firebase. Probado de punta a punta en `tools/dev/social_check.gd` |
| Borrar la cuenta **desde la web** (sin reinstalar) | ✅ publicada el 22/11/2026: https://coronadosdegloria.web.app/borrar-cuenta.html |
| Política de privacidad (URL en la ficha y dentro de la app) | ✅ publicada el 22/11/2026: https://coronadosdegloria.web.app/privacidad.html |
| Consentimiento para anuncios en UE/Reino Unido (CMP certificado por Google) | ✅ UMP integrado; verificado en el emulador: aparece el formulario de Google antes de iniciar AdMob (`admob_ad_provider.gd`): pide consentimiento antes de iniciar AdMob y, si corresponde, muestra *Privacidad de los anuncios* en Configuración. ⏳ crear el mensaje GDPR en AdMob → Privacidad y mensajes |
| Anuncios reales | ⚠️ **la versión de Play sale sin anuncios y sin el SDK de AdMob** (`tools/build_play.sh`). Decisión del 22/11/2026: no usar la cuenta de AdMob de benjann para esta app. Con una cuenta propia: IDs de producción en `data/ads.json` y `project.godot`, `app-ads.txt` (MONETIZACION.md) y sacar el `[admob] enabled=false` del script |
| Público objetivo | ⚠️ ver "Público y clasificación" |
| Contenido | ✅ sin apuestas con dinero real, sin compras, sin chat ni contenido generado por usuarios (sólo el nombre de la empresa, máx. 40 letras, visible para amigos) |

## Publicar las páginas legales

1. Responsable: Sarce (Juan José Defagot), desde el 22/11/2026; contacto facundo.n.defagot@gmail.com.
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

La clave está en `D:\Users\Family\Tools\keystores\upload\` (PC de la familia), con la
contraseña en `LEER-clave-de-subida.txt` al lado. **Guardar copia de los dos archivos fuera de la PC**
y nunca subirlos a GitHub. Si se pierde: Play Console → Integridad de la app → restablecer la clave de subida.

```bash
KEYSTORE=/ruta/coronados-upload.jks KEYSTORE_PASS='…' GODOT=/ruta/godot tools/build_play.sh
```
Genera `build/CoronadosDeGloria-<versión>.aab` sin AdMob y falla si el AAB trae el SDK o AD_ID.
Activar Play App Signing al subir el primer AAB. Los testers que tengan el APK de GitHub
tienen que desinstalarlo antes (otra firma): conviene entrar con la cuenta para que la
partida quede en la nube.

## Formulario "Seguridad de los datos" (respuestas)

- ¿Recopila o comparte datos? **Sí**. ¿Cifrados en tránsito? **Sí**. ¿Se pueden borrar? **Sí** (app y web).
- **Información personal → Dirección de email**: recopilada, no compartida; obligatoria sólo para
  cuentas (la app se usa sin cuenta → *opcional*); fines: *Funcionalidad de la app*, *Administración de la cuenta*.
- **Información personal → IDs de usuario** (uid de Firebase): igual que el email.
- **Actividad en la app → Otro contenido generado por el usuario** (nombre de la empresa en el
  perfil público): recopilado, opcional, *Funcionalidad de la app*.
- **Actividad en la app → Interacciones en la app / progreso** (partida en la nube): recopilado, opcional, *Funcionalidad de la app*.
- **Fotos y videos → Fotos** (desde la 15.0): miniatura 64×64 de la foto de perfil, **sólo si el jugador lo activa**
  (viene apagado); recopilada, opcional, *Funcionalidad de la app*; se borra al desactivarlo o al borrar la cuenta.
- **IDs de dispositivo u otros → ID de publicidad** (NO aplica mientras Play salga sin AdMob): recopilado y **compartido** con Google (AdMob);
  fines: *Publicidad o marketing*, *Estadísticas*, *Prevención de fraudes*. Sólo si la versión tiene anuncios.
- **Información y rendimiento de la app → Diagnóstico**: lo recopila el SDK de AdMob (mismo caso).
- No se recopilan: ubicación, contactos, mensajes, finanzas, salud.

Declaraciones aparte en Contenido de la app (AAB 15.1, sin AdMob): **Anuncios: No**,
**ID de publicidad: No** (el AAB no tiene el permiso AD_ID), **Acceso a la app**: no requiere
credenciales para revisar (se juega como invitado).

## Público y clasificación ⚠️

- **Público objetivo**: recomendado **13 años o más** (o 16+ para simplificar el RGPD). Si se
  incluyen menores de 13, aplica la política de Familias: anuncios sólo de SDKs certificados
  para familias, sin ID de publicidad, y `tag_for_under_age_of_consent`; hoy el juego no está
  preparado para eso.
- **Cuestionario IARC** (actualizado 15.x): desde la 12.0 hay minijuegos con **violencia de fantasía**
  (en el asalto se dispara a ladrones pixelados, sin sangre) y una **coima a la policía** (referencia a
  actividad delictiva, en tono de humor). Responder eso con honestidad: el resultado ya no sería
  PEGI 3 sino probablemente PEGI 7–12. Sin lenguaje fuerte; *no* hay apuestas
  (la animación "estilo casino" del saldo es sólo un contador, no se apuesta nada); interacción
  entre usuarios limitada (amigos por código, sin chat).
- Ficha (22/11/2026): ícono 512, gráfico 1024×500, 8 capturas 1080×1920 y textos en
  `D:\Users\Family\Download\PlayStore_Coronados\`. Capturas: `godot --path . --resolution 540x960 -- --shots=<dir> --shots-scale=1.5`,
  ampliadas ×2 sin suavizado (Play pide proporción máxima 2:1; la ventana por defecto 405×880 no sirve).

## Cuentas de prueba para cerrar la prueba

Las cuentas personales nuevas de Play Console deben hacer una **prueba cerrada con al menos
12 testers durante 14 días** antes de poder publicar en producción.
