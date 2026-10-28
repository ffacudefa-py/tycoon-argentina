# Tycoon Argentina 10.0 "Sigma Deza": conquistar la Argentina

## Contexto
El usuario quiere cambiar el objetivo del juego. Hoy hay 12 negocios urbanos genéricos en una ciudad ficticia, con 7 zonas. En la 10.0 el objetivo es **conquistar la Argentina región por región y provincia por provincia**, con los productos de `~/Descargas/productos_iconicos_argentina.xlsx`. La hoja 1 tiene 24 provincias, cada una con su producto estrella y 3 secundarios. La hoja 2 tiene el producto estrella de cada una de las 6 regiones.

Decisiones del usuario:
- **Negocios:** se reemplazan los 12 actuales. Cada provincia tiene su propio negocio (Mendoza: bodega de Malbec).
- **Conquista:** se domina el mercado. Hay una cuota contra un rival local; al llegar al 100 % la provincia es tuya. Con la región completa se gana el bonus del producto estrella regional.
- **Inicio:** se arranca en la región que menos ingresos genera (NOA). Montos y costos crecen región por región.
- **Partidas 0.7:** se empieza de cero sin premio. Se conservan perfil, avatar y amigos.
- **Arte:** un negocio dibujado a mano por provincia, con edificio en 5 niveles más interior.
- **Mapa:** pixel art con la forma real. Primero el país; al tocar una región se ve ampliada con sus provincias.

## Diseño del juego

**Orden de conquista** (los montos crecen ~×4,5 por provincia, unas 23 subidas que llevan los montos de cientos de pesos a ~1e15):
1. **NOA:** Santiago del Estero (algodón) → Jujuy (papas andinas) → Catamarca (aceite de oliva) → La Rioja (aceitunas) → Salta (torrontés) → Tucumán (limón).
2. **NEA:** Formosa (banana) → Chaco (algodón) → Corrientes (arroz) → Entre Ríos (arroz) → Misiones (yerba mate).
3. **Cuyo:** San Luis (cárnicos) → San Juan (pasas de uva) → Mendoza (Malbec).
4. **Patagonia:** Santa Cruz (cordero) → Chubut (lana) → Río Negro (peras) → Neuquén (manzanas) → Tierra del Fuego (electrónica).
5. **Pampeana:** La Pampa (carne vacuna).
6. **Centro:** Córdoba (salame de Colonia Caroya) → Santa Fe (lácteos) → Buenos Aires (trigo y harina) → CABA (medialunas).

Las regiones respetan el Excel, que pone Entre Ríos en NEA y Buenos Aires en Centro.

**Negocios repetidos:** algodón y arroz aparecen dos veces, así que se diferencian. Santiago tiene un campo algodonero y Chaco una desmotadora. Corrientes tiene una arrocera y Entre Ríos un molino arrocero.

**Productos de cada negocio:** el estrella más los 3 secundarios del Excel (4 productos, igual que el esquema actual).

**Conquista:**
- Cada provincia tiene `market_size` (ganancia/s necesaria) y un rival local ficticio.
- Tu cuota tiende a `clamp(ganancia_neta_s / market_size, 0, 1)` y se mueve suave hacia ese valor. Las campañas (se reusa `RivalSystem.campaign`) dan un empujón inmediato.
- Al llegar al 100 % la provincia queda conquistada para siempre. El rival cae, la provincia da +10 % de ingresos a los negocios de su región y se habilita la siguiente.
- Con todas las provincias de la región conquistadas: bonus de producto estrella regional (+25 % a todo) y se abre la región siguiente.
- La **etapa** pasa a ser la región actual (1–6). Los nombres son tipo "Conquistador del NOA".
- **Prestigio:** se mantiene y se habilita al conquistar Cuyo.

**Qué sigue igual y qué se ajusta:**
- Siguen igual: empleados, mejoras (con `upgrade_names` propios por negocio), eventos (con tags nuevos: agro, vino, frutas, ganadería, industria, panadería…), anuncios, amigos y perfil.
- Se elimina la **mudanza entre zonas**: cada negocio pertenece a su provincia.
- El rol director (`zone_revenue`) pasa a dar un bonus en la región.

## Fases
Cada fase cierra con pruebas pasando y un commit. La primera arranca con un commit de lo pendiente de la 0.7.1/0.7.2.

### F1 · Datos y lógica (con arte provisorio)
- `data/world.json`:
  - `regions[6]` con id, nombre, orden, estrella regional, bonus y forma en el mapa.
  - `provinces[24]` con id, nombre, región, orden, descripción, negocio, costo de apertura, `market_size` y rival.
  - `rivals[24]`.
  - Esto reemplaza a `zones`.
- `data/businesses.json`: 24 negocios en orden de conquista, con productos, tags y `upgrade_names`.
- `data/progression.json`: etapas = regiones, perk `franquicia` y avatares con logros nuevos.
- `data/missions.json`: cadena principal, desafíos, diarias y logros reescritos con métricas nuevas en `GameModel.metric()`: `share:<prov>`, `conquered`, `regions_conquered`, más las existentes `level:<bid>` y `sold:<prod>`.
- `scripts/core/game_data.gd`:
  - Índices `region_by_id` y `province_by_id`.
  - `_validate`: sacar el chequeo fijo de `"puesto"` y validar que el primer negocio sea el de la primera provincia.
- `scripts/core/game_model.gd`:
  - Reemplazar zonas por provincias: `_new_business_state`, `buy_business`, `zone_status`/`unlock_zone` → `province_status`/`open_province`, `businesses_in_zone` y la parte de zona de `_compute`.
  - Sumar cuota y conquista en el tick.
  - Sacar los ~17 ids fijos (`puesto`/`barrio`) y usar un `first_business()` que salga de los datos.
- `scripts/events/rival_system.gd`: un rival por provincia, con cuota en vez de `power` genérico, y campaña sobre la cuota.
- `scripts/persistence/migrations.gd`:
  - `CURRENT_VERSION = 4`.
  - `_v3_to_v4` conserva `profile`, `daily_reward`, `ads`, `social`, `time` y `stats.created`; el resto lo rellena `new_game()`.
  - `save_system.gd:179` valida el primer negocio en vez de `puesto`.
  - Las partidas de nube viejas también pasan por la migración al bajarse (`cloud_save.gd:183`), así que llegan limpias. En el resumen de la nube se agrega `season: 10` para que `CloudSync.decide` no prefiera una partida vieja con más `lifetime`.
- `scripts/ui/overlays/tutorial_steps.gd`: los 6 pasos se reescriben para el campo algodonero de Santiago del Estero.
- `main.gd`, `empire_screen.gd`, `prestige_modal.gd`, `ads_modal.gd` y `dev_shots.gd` usan `first_business()`.
- **Tests:** actualizar los ~159 ids en `tests/`. Reescribir `test_balance.gd` y `balance_bot.gd` con hitos nuevos (orientativos, el bot los ajusta):
  - primera provincia conquistada en ≤ 15 min,
  - NOA completo en ~2–3 h,
  - Cuyo en ~1–2 días de juego normal.
- **Arte provisorio:** el edificio genérico actual de `buildings2.generic()` con el nombre de la provincia, para poder jugar mientras se dibuja lo definitivo.

### F2 · Mapas
- Bajar una sola vez los polígonos públicos de provincias del IGN o de Natural Earth (GeoJSON) a `tools/art/map_data/`. Se simplifican en Python, se proyectan y se rasterizan en pixel art con contorno y la paleta `px2`:
  - `map/argentina.png` (360x540): 6 regiones con colores propios, incluyendo Malvinas y Antártida como detalle no jugable.
  - `map/region_<id>.png`: la región ampliada al ancho de la pantalla.
  - `map/mask_<vista>.png`: un color por provincia o región, para saber qué se tocó leyendo el píxel.
- `scripts/ui/screens/map_screen.gd`:
  - **Vista país:** regiones con candado o con el % conquistado.
  - Al tocar una región, **vista región** con botón Volver: provincias con el ícono del producto estrella y una barra de cuota.
  - Al tocar una provincia se abre el `ProvinceModal` nuevo, que reemplaza a `zone_modal.gd`, con el formato simple de ficha que ya hicimos:
    - producto estrella y secundarios,
    - rival y cuota,
    - Abrir negocio / Campaña / Ver negocio.
- Se borran `city_map.png`, `map.px.js` (ZONES) y las zonas de `backgrounds.py`.

### F3 · Arte por provincia (una subfase por región, en el orden de conquista)
Por cada provincia:
- **Edificio** en 5 niveles (192x150, 2 cuadros). Es una función propia en `tools/art/buildings3/<prov>.py` registrada en `ARCH`, que reemplaza a `GENERIC`. Ejemplos:
  - el algodonal crece de una chacra a una desmotadora,
  - el viñedo de Mendoza crece de un parral con galpón a una bodega con barricas.
- **Insignia** de 32x32.
- **Interior** en 5 niveles en `tools/art/pxl/gen_interiors.py`, con muebles nuevos en `furniture.px.js`: barricas, secadero de yerba, cajones de cítricos, línea de electrónica, corral, silo, horno de panadería, entre otros. Los que sean al aire libre llevan `has_interior:false` o `outdoor`.
- **Íconos de producto** de 16 px para los ~70 productos, en `icons.py`, más el estrella en 32 px.
- **Paisaje de fondo** de 480x200 por región en `locations.px.js`, con detalles por provincia:
  - NOA: cerros de colores,
  - NEA: selva roja,
  - Cuyo: Andes y viñedos,
  - Patagonia: estepa y lagos,
  - Pampeana: llanura y molino,
  - Centro: ciudad y sierras.

  `business_scene.gd` elige el fondo `locations/<prov>.png` y, si no está, el de la región.

Se revisa cada región con capturas de `dev_shots._run_scenes()` antes de pasar a la siguiente.

### F4 · Cierre de la versión
- `project.godot` y `export_presets.cfg`: versión `10.0`, código 10.
- Pantalla de inicio y aviso "Novedades 10.0 Sigma Deza" una sola vez.
- Documentación: `README.md`, `docs/PENDIENTES.md` y `docs/CONQUISTA.md` (nuevo, con las reglas de cuota y el balance).
- Compilar `build/tycoon-argentina-10.0.apk` e instalarlo en el emulador `Tycoon_Pixel`.

## Verificación
- `godot --headless --path . --import`, después `tools/run_tests.sh` en cada fase. Incluye las pruebas de humo reales que ya existen (`ARRASTRE_SCROLL`, `COLECTIVO_SIGUE`…) y suma nuevas:
  - `CONQUISTA_PROVINCIA`: subir la cuota al 100 % conquista y abre la siguiente,
  - `MAPA_REGION`: tocar una región entra a la vista región y Volver vuelve,
  - `MIGRACION_V4`: una partida 0.7 se carga de cero y conserva el perfil.
- Bot de balance (`tests/progression/balance_bot.gd`): los tiempos por provincia y por región quedan dentro de los márgenes de `test_balance.gd`.
- Capturas con `tools/screenshots.sh` a 360x740 de mapa país, mapa región, ficha de provincia y las 24 escenas en 5 niveles (`--shots-set=escenas`).
- APK final en el emulador, jugando el tutorial y la primera conquista.

## Riesgos y notas
- **Espacio en disco** (~2,3 GB libres): borrar los APK viejos y no generar varias exportaciones a la vez.
- **Tiempo:** F3 es la parte más larga (24 provincias a mano). Se entrega jugable al final de F2 con arte provisorio y el arte va llegando región por región.
- **Nombres:** los rivales locales son ficticios, para no usar marcas reales.

## Estado (28/10/2026, 12:20)
- Rama `v10-sigma-deza`. El primer commit guarda la 0.7.2 tal cual (estable, 89 pruebas OK).
- Hecho: `data/v10/provinces.json` con las 6 regiones y las 24 provincias en orden de conquista, más producto estrella, secundarios, nombre del negocio y rival ficticio. El juego todavía NO lo carga.
- Próximo paso (F1): con ese borrador, generar `data/world.json` (regions/provinces/rivals) y `data/businesses.json` (24 negocios con precios que escalen ~×4,5 por provincia). Después adaptar `game_data.gd`/`game_model.gd`, la migración v4, el tutorial y los tests, en el orden del plan.
