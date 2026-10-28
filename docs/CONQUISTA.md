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

## Partidas viejas

La migración v4 (`Migrations._v3_to_v4`) empieza de cero las partidas 0.7 y
conserva perfil (nombre, avatar, foto, banner), recompensa diaria, anuncios,
amigos y fecha de creación.

## Arte

- Mapas: `tools/art/map_art.py` (polígonos del IGN simplificados en `tools/art/map_data/`).
- Edificios por provincia: `tools/art/buildings3.py` · paisajes: `tools/art/landscapes.py`.
- Interiores: `tools/art/pxl/gen_interiors.py` + `furniture_v10.px.js`.
- Íconos de producto: `tools/art/icons_v10.py`.
