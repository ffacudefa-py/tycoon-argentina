# Minijuegos (11.2): asalto y coima

Existen en el modo normal y en el bien argentino. Ocupan toda la pantalla salvo
la barra superior (avatar y nombre de la empresa), con una franja debajo que
dice quién juega ("Los Pibes del Norte defiende Campo algodonero"). Los dos
arrancan con una animación (alarma o patrullero, cartel, reglas y 3-2-1); la
explicación se saltea tocando la pantalla.

## Código

| Pieza | Archivo |
|---|---|
| Robos, coima, multa y límite diario (modelo) | `scripts/events/security.gd` |
| Lógica del asalto (sin interfaz, con semilla) | `scripts/minigames/theft_game.gd` |
| Lógica de la coima | `scripts/minigames/bribe_game.gd` |
| Pantallas (todo en `_draw`) | `scripts/minigames/theft_view.gd`, `bribe_view.gd` |
| Capa que tapa todo menos la barra superior | `scripts/minigames/minigame_host.gd` |
| Arte (pixel art, paleta 11) | `tools/art/minigames_art.py` → `assets/pixel_art/minigames/` |
| Sonidos | `tools/sfx.py` (shot, hit, ricochet, empty, reload, bag, alarm, siren, swipe, shred, stamp, buzzer, tick) |
| Balance | `data/progression.json → balance.security` |

## Asalto

- Cada `theft_interval_*` (normal 8-15 min, bien argentino 4-8 min, sólo con la app
  abierta) una banda intenta robar un negocio con mercadería. Con la seguridad paga
  en esa provincia no pasa nada. Si no, queda un **robo pendiente** (se guarda con la
  partida) y `Main._process` abre el minijuego cuando no hay modales, tutorial ni
  inicio delante. Sin interfaz (pruebas) se resuelve al instante sin recuperar nada.
- Juego (24 s): 4-8 ladrones (según la dificultad) entran por los costados a rachas
  muy rápidas con pausas cortas, agarran una caja de la estantería y escapan en
  diagonal. **Tocar** = disparo (revólver de 6 balas; con el tambor vacío se toca el
  revólver para recargar, 0,6 s). Los de casco aguantan dos tiros. La caja de un
  ladrón caído queda en el piso con un aro de tiempo: hay que **arrastrarla a la
  bolsa** antes de que otro ladrón la levante o se pierda. Dispararle a un cliente
  traba el revólver 1,2 s.
- Resultado: se pierde `fracción × (1 − recuperado)` del stock. Defensa perfecta
  (nada perdido, nadie escapó) = un cofre.
- Dificultad `Security.difficulty`: 0,1 + 0,035 por provincia conquistada (+0,15 en
  el modo bien argentino), tope 1.

## Coima

- Botón "COIMEAR (n/5 HOY)" en Administrar negocio → seguridad. Cobra la coima (2 min
  de ingresos, mínimo $200) y gasta uno de los **5 intentos del día** (se reinicia a la
  medianoche local).
- Juego: 12-18 papeles. **Rojo → izquierda** (trituradora), **blanco → derecha**
  (carpeta del policía). Cada papel se da vuelta y tiene una barra de tiempo que va
  de ~1,5 s a ~0,8 s. Hay papeles blancos con sello rojo y rojos con etiqueta blanca:
  manda el color del papel. Nunca más de 3 del mismo color seguidos.
- Éxito: 30 min de seguridad en la provincia. Error o demora: **multa**, los
  ingresos bajan 20 % por 5 min (`Security.income_mult`). Una coima a medias (se
  cerró la app) cuenta como multa a los 2 min.

## Pruebas

- `tests/minigames/test_minigames.gd`: modelo (robos en los dos modos, pendiente y
  recuperación, multa, límite diario, coima abandonada), lógica de los dos juegos y
  **bots con tiempo de reacción y puntería** que miden la dificultad (novato,
  promedio y hábil en 0,2 / 0,6 / 0,9).
- Prueba de humo (`tools/run_tests.sh`): `MINIJUEGO_ROBO` y `MINIJUEGO_COIMA` juegan
  los dos minijuegos con toques y arrastres reales.
- Película para revisar animaciones (un cuadro cada ~0,1 s):
  `godot --path . -- --shots=<carpeta> --shots-set=minijuegos --dev-save=user://film.json`
