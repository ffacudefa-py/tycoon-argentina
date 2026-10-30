# Conquista de la Argentina (10.0 "Sigma Deza")

## Mapa y orden

6 regiones y 24 provincias (según `~/Descargas/productos_iconicos_argentina.xlsx`,
copiado en `data/v10/provinces.json`). Se conquistan en cadena, de la región que
menos ingresos genera a la que más:

1. **NOA**: Santiago del Estero → Jujuy → Catamarca → La Rioja → Salta → Tucumán
2. **NEA**: Formosa → Chaco → Corrientes → Entre Ríos → Misiones
3. **Cuyo**: San Luis → San Juan → Mendoza
4. **Patagonia**: Santa Cruz → Chubut → Río Negro → Neuquén → Tierra del Fuego
5. **Pampeana**: La Pampa
6. **Centro**: Córdoba → Santa Fe → Buenos Aires → CABA

Cada provincia tiene **un negocio** (su producto estrella + 3 secundarios del
Excel) y **un rival local ficticio**. El negocio siguiente se abre al conquistar
la provincia anterior.

## Cuota de mercado

`ConquestSystem` (scripts/progression/conquest_system.gd):

- Objetivo = ganancia neta/s del negocio ÷ (`market_size` × (0,5 + 0,1 × poder del rival)).
- La cuota sube hacia el objetivo como mucho a 100 % cada `conquest_minutes`
  (11 min en la primera provincia, ×1,25 por provincia). También avanza offline.
- Al 100 %: provincia conquistada para siempre, el rival cae a poder 1 y los
  negocios de esa región ganan **+10 %**. Región completa: **+25 % a todo**.
- Las campañas de marketing bajan el poder del rival y suman 8 % de cuota.
- Etapa = 1 + regiones completas (7 = toda la Argentina). El prestigio se
  habilita al completar Cuyo (etapa 4).

## Balance

La economía de cada provincia interpola en escala logarítmica la curva de los
12 negocios de la 0.7 (~×4,5 por provincia). Todo se genera con
`python3 tools/v10/build_data.py` (constantes `MARKET_*` y `CONQUEST_*`).
Con el bot de balance (juego activo y razonable): primera provincia ~11 min,
NOA completo ~2 h. `tests/progression/test_balance.gd` vigila esas ventanas.

**Corrección 11.0 (simulación de 20 h).** Con el balance de la 10.x el bot quedaba
trabado: Misiones tardaba 6 h y San Luis no caía en 7,5 h, con todos los negocios
anteriores al nivel 100 y la plata sin nada útil en qué gastarse. Causas:
- El mercado crecía ×1,6 por provincia más rápido que el propio negocio: desde San
  Juan superaba la ganancia a nivel 100 con todas las mejoras (en CABA, ×150), así
  que el juego **no se podía terminar**. Ahora deja de crecer desde la provincia 11
  (`MARKET_GROWTH_CAP_AT`): hace falta entre el 33 % y el 60 % del máximo.
- Los costos de nivel y de apertura crecían ~×4 por provincia contra ~×2 de la
  ganancia: pagar los 100 niveles pasaba de 5 h a meses, y los últimos costos tocaban
  el tope de los enteros (9e18). Desde la provincia 9 se multiplican por
  `COST_DAMP` = 0,64 por provincia: ahora se pagan en 5-22 h al máximo.
`test_toda_la_argentina_es_conquistable` vigila las dos cosas en las 24 provincias.

## Partidas viejas

La migración v4 (`Migrations._v3_to_v4`) empieza de cero las partidas 0.7 y
conserva perfil (nombre, avatar, foto, banner), recompensa diaria, anuncios,
amigos y fecha de creación.

## Arte

- Mapas: `tools/art/map_art.py` (polígonos del IGN simplificados en `tools/art/map_data/`).
- Edificios por provincia: `tools/art/buildings3.py` · paisajes: `tools/art/landscapes.py`.
- Interiores: `tools/art/pxl/gen_interiors.py` + `furniture_v10.px.js`.
- Íconos de producto: `tools/art/icons_v10.py`.

## Modo bien argentino (opcional)

Se elige una sola vez al empezar la cuenta (`HardModeModal`; el prestigio lo
conserva) y reemplaza al viejo ajuste de inflación ficticia. Lógica en
`scripts/events/hard_mode.gd`, balance en `progression.json → balance.hard_mode`:

- **+25 %** en todos los ingresos.
- **Inflación fuerte** siempre activa (remarcación cada 6 min, +12 %).
- **Juicios laborales**: con sueldos atrasados más de 2 min, el empleado de mayor
  sueldo hace juicio (15 min de sueldo; lo que no se pueda pagar queda como deuda) y se va.
- **Robos**: cada 4-8 min una banda se lleva 20-40 % de la mercadería de un negocio.
- **Seguridad (coima)**: 2 min de ingresos por provincia → 30 min sin robos.
- Juicios y robos sólo pasan con el juego abierto.

## Ciclo de enganche (10.3)

`scripts/progression/engagement.gd`, balance en `progression.json → balance.engagement`:

- **Combo**: vender a mano seguido sube un multiplicador sobre esas ventas
  (+0,1 por venta hasta x2; si pasan 3 s sin vender baja 0,25 por segundo).
- **Cofres** con premio variable (plata, turbo x2 o avatar). Sólo se ganan
  jugando: conquistar una provincia (1), completar una región (2), cada logro (1),
  niveles 25/50/100 de cada negocio (1 c/u) y desafíos de eventos. Nunca se compran.
- **Próxima meta** debajo del negocio: la más cercana entre cuota de mercado,
  próximo hito de nivel y la mejora más barata.
- **Eventos regionales con desafío**: Vendimia, Zafra, Fiesta de la Yerba Mate,
  Temporada de esquí y Exposición Rural (bonus por 8-10 min y cofre si llegás a N ventas).
  Perderlos no tiene castigo.
