# Amigos (desde la 0.7)

Sistema social sobre Firestore (plan Spark, sin Cloud Functions). Necesita una cuenta
con el **email verificado**: hasta tocar el enlace del correo, la nube y los amigos
quedan en pausa, y las reglas de Firestore lo exigen también del lado del servidor
(`request.auth.token.email_verified == true`).

## Qué puede hacer el jugador

- **Código de amigo** de 6 caracteres (sin O/0/I/1/L para que no se confundan),
  se crea la primera vez que entra a Amigos. Se copia con un toque.
- **Agregar por código**: manda una solicitud; el otro la acepta o la rechaza. Si
  los dos se mandan solicitud, la segunda acepta directamente.
- **Ranking de amigos** por plata ganada en la historia (incluye al jugador).
- **Convidar un mate**: uno por día a cada amigo. Al abrirlo da
  `friends.gift_reward` (2 min de ganancia neta, mínimo $200) y se abren como mucho
  `friends.gifts_per_day` (5) por día. Todo en `data/progression.json`.
- **Sacar a un amigo**: se borra de las dos listas.
- **Bloquear o denunciar** (15.2, botón ⚠ en solicitudes y amigos): bloquear lo saca de
  amigos, borra su solicitud y su mate y no le deja mandar nada más ni ver el perfil;
  denunciar además deja un documento en `reports/` para que lo revise el equipo. Se
  desbloquea en la tarjeta *Bloqueados*.
- **Insignias** (15.2): cada uno elige hasta 3 (logros o especiales como *Pionero*) y
  sus amigos las ven al lado del nombre en el ranking (`Badges`, `scripts/profile/badges.gd`).
- Máximo `friends.max_friends` (50) amigos.
- **Tope de solicitudes** (15.2): 20 por día por cuenta (`FriendLogic.REQUESTS_PER_DAY` y
  `limits/<uid>` en `firestore.rules`, mismo número). La solicitud y el contador van en un
  solo commit; las reglas rechazan una solicitud que no sume 1.

Acceso: Perfil → tarjeta **Amigos** (muestra cuántas solicitudes y mates hay sin ver).

## Datos en Firestore

| Documento | Contenido | Quién lee / escribe |
|---|---|---|
| `players/<uid>` | empresa, avatar, etapa, ganado, prestigio, código, (15.0) `photo`: miniatura JPEG 64×64 en base64 si el jugador lo activa en Configuración (apagado de fábrica) y (15.2) `badges`: hasta 3 ids de insignias | desde la 15.2 lo leen **sólo** el dueño, sus amigos y a quien le mandó solicitud (antes, cualquiera verificado); no se listan; escribe el dueño |
| `codes/<CÓDIGO>` | `{uid}` | se lee de a uno; se crea una vez y no se cambia |
| `players/<uid>/requests/<de>` | solicitud recibida | la crea `<de>` (si no son amigos); el dueño la ve y la borra |
| `players/<uid>/friends/<uid2>` | `{since}` | el dueño; quien acepta escribe además en la lista del que pidió **sólo si existe la solicitud** |
| `players/<uid>/gifts/<de>` | mate sin abrir | lo crea `<de>` **sólo si está en la lista del dueño** (y no está bloqueado); el dueño lo abre (borra) |
| `players/<uid>/blocked/<uid2>` | (15.2) `{company, at}` | sólo el dueño; mientras exista, `<uid2>` no puede crear solicitudes ni mates ni leer el perfil |
| `reports/<auto>` | (15.2) `{reporter, target, reason, company, at}` | la crea el que denuncia a su nombre; nadie la lee desde el juego (se revisa en la consola); el que denunció la borra al borrar su cuenta |

Aceptar es un `documents:commit` atómico: las dos entradas de `friends` y el borrado de
la solicitud. Las reglas están en `firestore.rules`.

## Código

- `scripts/social/friend_logic.gd` (`FriendLogic`): códigos, ranking, cupo diario de
  mates (se guarda en la partida: `GameModel.social`) y formato de Firestore. Sin red;
  probado en `tests/social/test_social.gd`.
- `scripts/social/friends_service.gd` (autoload `Friends`): red. Las acciones son
  corrutinas (`await Friends.add_by_code(...)` → `{ok, msg}`). Actualiza perfil,
  solicitudes y mates al entrar y cada 5 min.
- `scripts/ui/modals/friends_modal.gd`, `verify_email_modal.gd` y la tarjeta en
  `profile_screen.gd`.

## Prueba de punta a punta (emuladores, no toca el proyecto real)

Requiere Java (JDK 21) y la CLI de Firebase. El emulador se descarga una vez.

```bash
export TYCOON_EMULATOR=127.0.0.1
firebase emulators:exec --only auth,firestore --project coronadosdegloria \
  "godot --headless --path . -s res://tools/dev/social_check.gd -- --dev-save=user://social_check_save.json"
```

Crea cuentas, comprueba que sin verificar la nube responde 403, abre el enlace de
verificación del emulador, y recorre solicitud → aceptar → mate → abrir → sacar,
incluyendo los intentos que las reglas deben rechazar (forzar una amistad, mandar
mates sin ser amigos). En esta PC: `FIREBASE_EMULATORS_PATH` en D: (C: está lleno).
