# Pioneros: prueba cerrada (15.2)

Google Play exige a las cuentas personales nuevas una **prueba cerrada con al menos 12
testers durante 14 días seguidos** antes de publicar. Para organizarla hay tres piezas
conectadas, todas en Firebase (proyecto `coronadosdegloria`):

| Pieza | Dónde | Qué guarda |
|---|---|---|
| **Inscripción** | https://coronadosdegloria.web.app/pioneros.html (`web/pioneros.html`) | `signups/<email>`: `{name, email, created, consent, android}` (+ `invited`, `note` que pone la planilla) |
| **Registro desde el juego** | AAB de la prueba cerrada (`PRUEBA_CERRADA=1 tools/build_play.sh`), con cuenta verificada | `pioneers/<uid>`: `{email, company, first_day, last_day, days, version}` (días UTC; `days` = días distintos que abrió el juego) |
| **Planilla** | https://coronadosdegloria.web.app/pioneros-admin.html (`web/pioneros-admin.html`) | lee las dos colecciones y las denuncias (`reports`) |

## La página de inscripción (diseño)

Inspirada en la web de Arcaea: héroe a pantalla completa con el logo arriba al centro sobre
un arte grande, rótulos con chevrones y bandas oscuras y claras. Todo con piezas del juego:

- **Fondo**: `web/img/pilares.png` (1920×1080), las 6 regiones como pilares con capitel y base
  dorada, pintadas con la técnica de la postal del NOA. Se regenera con
  `python tools/art/pilares_web.py` (también deja `web/img/region_<id>.png` para las tarjetas).
  El NOA sale de las capas reales de la pantalla de inicio.
- **Paneles y botones**: las texturas 9-slice de `assets/iconos/ui` (`web/img/ui/`) con
  `border-image` y `image-rendering: pixelated`, a escala entera (3 px por píxel; 2 px en celular).
- **Tipografía**: VT323 (`web/fonts/`, licencia OFL) en títulos, botones y rótulos, como el juego.
- **Logo** (`assets/pixel_art/logo/logo_coronados.png`) siempre a 1× o 2×; íconos de producto
  estrella y capturas reales del juego en teléfonos.

## Paso a paso

1. **Difundir** el enlace de inscripción (Instagram, grupos, el reel).
2. En la **planilla** (entrar con la cuenta administradora, abajo): *Copiar emails sin invitar*.
3. Play Console → Pruebas → **Prueba cerrada** → Testers → lista de emails → pegar y guardar.
   Copiar el **enlace para unirse** de la prueba y mandárselo a los inscriptos (por email).
4. En la planilla: *Marcar esos como invitados*.
5. Cada tester instala el AAB de la prueba desde Play. Al abrirlo gana la insignia
   **Pionero**; si tiene cuenta (Perfil → Amigos) queda en *Jugando* y se le cuentan los días.
   Sin cuenta la insignia queda sólo en su teléfono (el juego se lo avisa en el detalle de la insignia).
6. La pestaña **Jugando** muestra cuántos días lleva cada uno; el indicador *Cumplen 14 días*
   tiene que llegar a **12** (conviene invitar 15–20 por las bajas). *Sin abrir hace N días*
   = escribirle para que no lo desinstale.
7. Cumplidos los 14 días: Play Console → pedir acceso a producción.

## Administración

- La planilla sólo deja entrar a emails **verificados** de la lista `isAdmin()` de
  `firestore.rules` (hoy: facundo.n.defagot@gmail.com). Para sumar a alguien, agregar su
  email ahí y publicar las reglas. La cuenta se crea desde la misma planilla (*Crear cuenta*
  → enlace del correo) o desde el juego.
- Desde la planilla se marca *invitado*, se anotan notas, se borra una inscripción (si alguien
  pide la baja) y se dan por resueltas las denuncias.
- *Descargar CSV* baja todo para Excel/Sheets.

## Seguridad

- La inscripción no pide cuenta: cualquiera puede anotarse **una vez por email** (el id es el
  email en minúsculas). Nadie la puede leer, cambiar ni borrar salvo la administración.
  Tiene una trampa para bots (campo oculto); si llegara spam, se borra desde la planilla.
- El registro desde el juego sólo suma **un día por día real** (lo controla el servidor con
  su propia hora) y el email tiene que ser el de la cuenta: no se pueden inventar días.
- Todo esto se prueba en `tools/dev/rules_check.sh` (emuladores).

## Pruebas locales

```bash
tools/dev/rules_check.sh          # reglas (incluye inscripción, registro y administración)
```
Las páginas aceptan `?emu=1` para usar los emuladores en vez del proyecto real.
