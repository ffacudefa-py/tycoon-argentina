# Arquitectura

```
data/*.json            Todo el contenido y balance (sin lógica)
scripts/core/          GameData (carga/valida JSON), GameModel (estado + acciones),
                       Game (autoload: bucle, guardado, offline), Fmt (formatos)
scripts/economy/       Economy: saldo int64, earn/spend/spend_up_to, libro de transacciones
scripts/businesses/    BusinessSim: ciclos de venta, pedidos, reposición automática
scripts/employees/     EmployeeSystem: candidatos, contratar/despedir, sueldos, experiencia
scripts/events/        EventSystem (eventos + inflación opcional), RivalSystem
scripts/progression/   ProgressionSystem (misiones, diarias, logros, recompensa diaria),
                       PrestigeSystem
scripts/offline/       OfflineCalculator
scripts/persistence/   SaveSystem (atómico, checksum, respaldo), Migrations
scripts/settings/      SettingsData (puro) + Settings (autoload, aplica al instante)
scripts/auth/ cloud/   Auth (cuentas, verificación del email), Cloud (partida en Firestore)
scripts/social/        FriendLogic (puro) + Friends (autoload: amigos en Firestore)
scripts/audio/         Sfx (autoload: efectos + vibración)
scripts/monetization/  Monetization (autoload) + interfaces AdProvider/PurchaseProvider
scripts/ui/            Main (raíz), U (kit de widgets), ThemeBuilder, components/,
                       screens/ (5 secciones), modals/, overlays/ (modales, avisos,
                       efectos, tutorial), DevShots (QA visual)
tests/                 runner propio, economía, progresión, persistencia, bot de balance
tools/                 generadores de arte/sonido, scripts de pruebas y capturas
```

## Principios

- **El modelo no conoce la UI.** `GameModel` es un `RefCounted` sin nodos. La UI llama
  acciones (`buy_levels`, `restock`, `EmployeeSystem.hire`…) que devuelven
  `{ok, msg}` y escucha señales (`money_changed`, `business_changed`, `sale`,
  `notify`, `celebrate`…). Los tests crean modelos con reloj falso.
- **Una sola lógica de tiempo.** `GameModel.simulate(dt, offline)` corre igual con
  pasos de 0,1 s (online, acumulando el delta real → independiente de los FPS) o de
  5 s (offline). Los cálculos no se hacen por fotograma.
- **Todo el dinero pasa por `Economy`.** El efectivo nunca es negativo; las compras se
  rechazan si no alcanza; sueldos impagos generan deuda (equipo al 50 %). La barra
  superior muestra el saldo neto (`net_balance()` = efectivo − deuda): con deuda queda
  en rojo y con "-" adelante.
- **Valores derivados con caché** (`derive(id)`), invalidados ante cualquier cambio.
- **Secciones vivas**: las 5 pantallas se crean una vez y se alternan con `visible`.
- **Capas**: modales (10), efectos (20), tutorial (30), festejo de negocio nuevo (35, `UnlockShow`), avisos (40). Efectos y avisos
  ignoran toques. Los `CanvasLayer` cortan la herencia del tema, por eso cada capa
  recibe el tema explícitamente.

## Animaciones de festejo

- Botones (`U.press_feedback`): se aplastan y se aclaran al apretar; vuelven con rebote elástico.
- `Juice.gold_shine(tarjeta)`: barridos dorados en degradé (shader pixelado) unos 2,5 s; se usa al comprar una mejora.
- `Juice.mission_done(tarjeta, al_terminar)`: relleno verde, tick y salida hacia la izquierda; `ObjectivesScreen` no se rearma hasta que termina.
- `UnlockShow.play(negocio)`: al comprar un negocio, rayos de luz girando detrás del edificio y confeti de fondo; se cierra solo o tocando.
- Con "Reducir movimiento" todo se acorta y no hay desplazamientos.

## Dependencias entre sistemas

```
Game ──> GameModel ──> Economy
              │──> BusinessSim ──> EventSystem (modificadores), Economy
              │──> EmployeeSystem ──> Economy
              │──> RivalSystem (competencia por zona)
              │──> ProgressionSystem ──> metric() del modelo, Economy, avatares
              │──> PrestigeSystem ──> _reset_run()
Game ──> SaveSystem ──> Migrations          Game ──> OfflineCalculator ──> simulate()
UI (Main, pantallas, modales) ──> Game.m (acciones/señales), Settings, Sfx, Monetization
```

## Agregar un negocio

1. Agregar una entrada en `data/businesses.json` (copiar una existente): `id`,
   `cycle`, `level_cost_base`, `level_cost_growth`, `unlock` (costo, etapa, requisito),
   productos (precio, costo, demanda, etiquetas), `tags`, `upgrade_names` y `art`
   (`archetype` de `tools/art/buildings.py`, colores, ícono del cartel).
2. `python3 tools/art/generate.py` genera sus 5 niveles visuales y su insignia.
3. `tools/run_tests.sh` (valida datos y corre el bot de balance).

No hace falta tocar código: economía, mejoras, empleados, misiones y UI lo toman solos.

## Guardado

`user://tycoon_save.json` (+ `.tmp`, `.bak`, y `.corrupt-<fecha>` si algo se dañó).
Formato versionado con checksum SHA-256 del payload. Escritura: tmp → verificación →
el anterior pasa a .bak → reemplazo. Carga: principal → tmp → bak → partida nueva.
Enteros grandes como texto (JSON pierde precisión arriba de 2^53). Campos faltantes
toman valores seguros (`GameModel.from_dict`). Para cambiar el formato: subir
`Migrations.CURRENT_VERSION` y agregar la función de migración.
Guardado automático cada 30 s, al pausar/cerrar la app y tras acciones importantes.
Preferencias aparte en `user://settings.cfg`.
