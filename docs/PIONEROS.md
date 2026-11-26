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
2. **Automático**: al instante (aviso de la página a la app web del script) o, si falla, en ≤1 minuto, cada inscripto recibe un mail de
   sarceapps@gmail.com (ver *Mail automático*) con 3 botones: unirse al Grupo de Google
   `coronados-pioneros@googlegroups.com` (eso lo habilita en la prueba), aceptar ser tester
   (`play.google.com/apps/testing/ar.tycoonargentina.juego`) e instalar. La planilla lo marca
   *invitado* con un ✉. Ya no hace falta cargar emails en Play Console.
3. (Sigue funcionando el método viejo: *Copiar emails sin invitar* → lista de emails en Play Console.)
4. Cada tester instala el AAB de la prueba desde Play. Al abrirlo gana la insignia
   **Pionero**; si tiene cuenta (Perfil → Amigos) queda en *Jugando* y se le cuentan los días.
   Sin cuenta la insignia queda sólo en su teléfono (el juego se lo avisa en el detalle de la insignia).
6. La pestaña **Jugando** muestra cuántos días lleva cada uno; el indicador *Cumplen 14 días*
   tiene que llegar a **12** (conviene invitar 15–20 por las bajas). *Sin abrir hace N días*
   = escribirle para que no lo desinstale.
7. Cumplidos los 14 días: Play Console → pedir acceso a producción.

## Mail automático

Script de Google Apps Script `tools/pioneros/Mailer.gs` (+ `appsscript.json`), **dueño:
sarceapps@gmail.com** (por eso el mail sale de ahí; sarceapps es owner del proyecto Firebase,
así que lee y marca `signups` por REST con su token OAuth, sin pasar por las reglas). El
proyecto está en plan Spark (sin Cloud Functions), por eso es Apps Script y no una función.
Cuota: 100 mails/día (cuenta Gmail común).

Instalación (una vez):
1. **Grupo** (con sarceapps): groups.google.com → Crear grupo → nombre `coronados-pioneros`
   → *Quién puede buscar*: cualquier persona en la Web; *Quién puede unirse*: **cualquier
   persona puede unirse**; *Quién puede ver conversaciones / publicar*: solo administradores.
2. **Play Console** (jjdefagot) → Prueba cerrada → Testers → **Grupos de Google** → agregar
   `coronados-pioneros@googlegroups.com` → Guardar (la lista de emails existente puede quedar).
3. **Script** (con sarceapps): script.google.com → Nuevo proyecto "Pioneros mailer" →
   pegar `Mailer.gs`; Configuración del proyecto → *Mostrar appsscript.json* → pegar
   `appsscript.json`. Ejecutar `testMail` (autorizar; llega un mail de prueba a sarceapps),
   después `setup` (crea el disparador cada 5 min). Opcional: `mailAlsoInvited` una vez para
   mandárselo también a los que ya estaban marcados como invitados.
4. Errores: script.google.com → Ejecuciones (y Google avisa por mail si el disparador falla).

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

### Seguridad del mail automático (revisado 2026-11-26)

- **Cuota de Firestore**: el script guarda un cursor (`created` de la última inscripción) y
  sólo consulta las nuevas (1 lectura por revisión si no hay nada). Antes leía todas cada
  minuto (~16.000 lecturas/día con 16 inscriptos) y con ~50 inscriptos se habría comido las
  50.000 lecturas gratis del proyecto, cortando los guardados del juego.
- **Abuso de la app web** (`doPost` público): no recibe datos y como mucho revisa una vez cada 10 s.
- **Spam desde sarceapps**: tope de 40 mails automáticos por día (`MAX_PER_DAY`); lo que pase
  del tope sale al día siguiente. Cada email se anota una sola vez (id = email).
- **Grupo**: cualquiera puede unirse (es la idea), pero sólo los administradores publican, las
  conversaciones las ven sólo miembros y la lista de miembros sólo administradores. Nunca usar
  `coronados-pioneros@googlegroups.com` como email de registro o de recuperación de ninguna cuenta.
