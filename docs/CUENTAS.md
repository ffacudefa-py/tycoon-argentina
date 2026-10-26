# Cuentas (Firebase Authentication)

- Proyecto Firebase: `coronadosdegloria` (plan Spark, gratis; cuenta del dueño del
  juego). Tiene **Authentication → Email/contraseña** y **Firestore** en
  `southamerica-east1`. Hasta la 0.5 se usó `tycoon-argentina-juego` (otra cuenta).
- Reglas versionadas en `firestore.rules`; se publican con
  `firebase deploy --only firestore:rules` (`firebase.json` y `.firebaserc` en la raíz).
- `data/firebase.json` tiene la API key web. No es un secreto: identifica al
  proyecto; lo que protege es la configuración de Authentication (y las reglas
  si en el futuro se usa Firestore/Storage).
- `scripts/auth/auth_service.gd` (autoload `Auth`) usa la API REST:
  `accounts:signUp`, `accounts:signInWithPassword`, `accounts:sendOobCode`
  (recuperar contraseña) y `securetoken` (renovar sesión). No necesita SDK
  nativo ni Gradle.
- `scripts/auth/auth_errors.gd`: validaciones locales y mensajes en castellano.
  Por privacidad, "email no existe" y "contraseña incorrecta" dan el mismo mensaje.

## Verificación del email (desde la 0.7)

- Al crear la cuenta se manda el correo de verificación (`accounts:sendOobCode`,
  `VERIFY_EMAIL`) y se abre "Verificá tu email". Al iniciar sesión se consulta
  `accounts:lookup`; si el email no está verificado se abre el mismo aviso.
- "Ya lo verifiqué" vuelve a consultar y, si ya está, **renueva el token** (el viejo
  trae `email_verified=false`). "Reenviar" tiene un límite de 60 s por cuenta.
- Sin verificar se puede jugar, pero la nube y los amigos están en pausa. Las reglas
  de Firestore exigen `email_verified` en todos los documentos: no alcanza con
  saltearse el aviso en el cliente.
- Las cuentas creadas con la 0.6 también tienen que verificar (la 0.6 sin
  actualizar deja de sincronizar con las reglas nuevas).
- El estado queda en `user://session.cfg` (`verified`) y se revisa en segundo plano
  al abrir el juego.

## Sesión

- Se guarda en `user://session.cfg` (uid, email, nombre y refresh token; nunca
  la contraseña). Al abrir el juego se restaura sin pedir nada y se renueva el
  token en segundo plano. Sin internet, la sesión se mantiene.
- Si el servidor dice que la sesión no vale más (cuenta borrada/deshabilitada),
  se cierra y se avisa.
- **Cerrar sesión no toca la partida**: sigue en el teléfono y se juega como invitado.

## Progreso en la nube (desde la 0.6)

- **Firestore** (plan Spark): un documento `saves/<uid>` por cuenta con el mismo
  sobre que el guardado local (`format`, `version`, `checksum`, `payload`) en el
  campo `save`, más un resumen (`saved_at`, `stage`, `money`, `lifetime`, `company`,
  `prestige`, `play_time`, `app_version`) para comparar sin descargar todo.
- Reglas en `firestore.rules`: cada cuenta verificada lee y escribe sólo su
  `saves/<uid>`; el resto del archivo son los amigos (docs/AMIGOS.md).
- `scripts/cloud/cloud_save.gd` (autoload `Cloud`) usa la API REST con el token de
  `Auth.get_token()`; `scripts/cloud/cloud_sync.gd` tiene las decisiones (probadas en
  `tests/cloud`).
- **Al conectarse** (`CloudSync.decide`): si la nube está vacía o no cambió desde la
  última sincronización de este teléfono, se sube; si la partida del teléfono recién
  empieza (menos de $500 ganados y sin prestigio), se baja la de la nube; si las dos
  tienen progreso distinto, `CloudConflictModal` pregunta cuál conservar (no se cierra
  sin elegir).
- **Después**: copia cada 90 s si hubo cambios y al pasar a segundo plano. Sin
  internet queda pendiente y reintenta cada 2 min. La partida se guarda siempre primero
  en el teléfono.
- Estado en Configuración → Cuenta ("Guardado en la nube hace 3 min", "Sincronizar
  ahora"). Las capturas y las herramientas `-s` nunca tocan la nube.
- `user://cloud.cfg` recuerda la cuenta y el `saved_at` de lo último sincronizado.

## Lo que todavía NO hay

- Foto de perfil y banner en la nube (necesitan Cloud Storage, plan Blaze).
- Inicio con Google: requiere plugin nativo de Google Sign-In + Gradle.

## Verificación manual contra el servidor real

```bash
godot --headless --path . -s res://tools/dev/auth_check.gd
```
Crea una cuenta descartable, prueba contraseña corta, cuenta repetida, clave
incorrecta, ingreso, renovación y recuperación, y **borra** la cuenta al final.

Para la nube y los amigos (con las reglas verdaderas, en los emuladores locales):
`tools/dev/social_check.gd`, ver docs/AMIGOS.md. Prueba que una cuenta sin verificar
recibe 403, que una verificada guarda su partida y que no puede tocar la de otro.
