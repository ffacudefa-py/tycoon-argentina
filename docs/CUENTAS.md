# Cuentas (Firebase Authentication)

- Proyecto Firebase: `tycoon-argentina-juego` (plan Spark, gratis). Sólo está
  activado **Authentication → Email/contraseña**.
- `data/firebase.json` tiene la API key web. No es un secreto: identifica al
  proyecto; lo que protege es la configuración de Authentication (y las reglas
  si en el futuro se usa Firestore/Storage).
- `scripts/auth/auth_service.gd` (autoload `Auth`) usa la API REST:
  `accounts:signUp`, `accounts:signInWithPassword`, `accounts:sendOobCode`
  (recuperar contraseña) y `securetoken` (renovar sesión). No necesita SDK
  nativo ni Gradle.
- `scripts/auth/auth_errors.gd`: validaciones locales y mensajes en castellano.
  Por privacidad, "email no existe" y "contraseña incorrecta" dan el mismo mensaje.

## Sesión

- Se guarda en `user://session.cfg` (uid, email, nombre y refresh token; nunca
  la contraseña). Al abrir el juego se restaura sin pedir nada y se renueva el
  token en segundo plano. Sin internet, la sesión se mantiene.
- Si el servidor dice que la sesión no vale más (cuenta borrada/deshabilitada),
  se cierra y se avisa.
- **Cerrar sesión no toca la partida**: sigue en el teléfono y se juega como invitado.

## Lo que todavía NO hay

- Progreso en la nube: la partida y la foto de perfil siguen sólo en el teléfono.
  Próximo paso sugerido: Firestore con un documento por `uid` que guarde
  `GameModel.to_dict()` (ya es JSON) + reglas `request.auth.uid == uid`; la foto
  necesita Cloud Storage (requiere plan Blaze).
- Inicio con Google: requiere plugin nativo de Google Sign-In + Gradle.

## Verificación manual contra el servidor real

```bash
godot --headless --path . -s res://tools/dev/auth_check.gd
```
Crea una cuenta descartable, prueba contraseña corta, cuenta repetida, clave
incorrecta, ingreso, renovación y recuperación, y **borra** la cuenta al final.
