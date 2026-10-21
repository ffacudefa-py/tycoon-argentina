# Tycoon Argentina

Simulador de negocios pixel art para Android (Godot 4.7, GDScript, vertical).
Empezás con un puestito callejero en el Barrio Villa Esperanza y crecés hasta
un conglomerado: niveles, mejoras, mercadería, empleados, automatización,
ingresos offline, zonas, rivales, eventos, misiones, logros y prestigio.

Todo el arte, los sonidos, los nombres y las empresas son originales y ficticios.

## Ejecutar

```bash
godot --path ~/TycoonArgentina            # juego (ventana 405x880)
godot --path ~/TycoonArgentina -e         # editor
```
Godot 4.7.2 está instalado sin root en `~/.local/opt/godot` (`~/.local/bin/godot`).

## Pruebas

```bash
tools/run_tests.sh                # 48 pruebas + humo de UI headless + toque real
tools/run_tests.sh --only=balance # sólo la simulación de balance
BALANCE_HOURS=4 tools/run_tests.sh --only=balance   # corrida más larga
tools/screenshots.sh              # capturas reales de todas las pantallas (abre ventana)
```

## Exportar a Android

```bash
godot --headless --path . --export-debug "Android" build/tycoon-argentina-debug.apk
adb install -r build/tycoon-argentina-debug.apk
```
Requisitos (ya configurados en esta PC, ver `docs/ANDROID.md`):
plantillas de exportación 4.7.2 (sólo los APK de Android), Android SDK en
`~/Android/Sdk`, JDK 21 y keystore de debug en `~/.local/share/godot/keystores/`.

## Regenerar arte y sonido

```bash
python3 tools/art/generate.py   # todo el pixel art + docs/art_preview.png
python3 tools/sfx.py            # efectos de sonido sintetizados
```

## Documentación

- `docs/ARQUITECTURA.md` — sistemas, dependencias, cómo agregar negocios.
- `docs/ECONOMIA.md` — fórmulas, números grandes, balance y simulaciones.
- `docs/ARTE.md` — dirección pixel art, resolución, spritesheets.
- `docs/ANDROID.md` — exportación, firma, release.
- `docs/MONETIZACION.md` — qué falta para anuncios/compras reales.
- `docs/PASSIDLE.md` — qué se tomó de PassIdle y qué no.
- `docs/PENDIENTES.md` — lo que queda para próximas versiones.
