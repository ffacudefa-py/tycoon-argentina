# Tycoon Argentina

Simulador de negocios pixel art para Android (Godot 4.7, GDScript, vertical).
**10.0 "Sigma Deza":** el objetivo es conquistar la Argentina región por región
y provincia por provincia. Empezás con un campito de algodón en Santiago del
Estero (NOA) y cada provincia tiene su negocio según su producto icónico:
papas andinas en Jujuy, Malbec en Mendoza, yerba en Misiones, medialunas en
CABA… Le ganás el mercado al rival local hasta el 100 % y la provincia es tuya.
Niveles, mejoras, mercadería, empleados, automatización, ingresos offline,
eventos, misiones, logros, prestigio y amigos. Reglas: `docs/CONQUISTA.md`.

Todo el arte, los sonidos, los nombres y las empresas son originales y ficticios.

## Ejecutar

```bash
godot --path ~/TycoonArgentina            # juego (ventana 405x880)
godot --path ~/TycoonArgentina -e         # editor
```
Godot 4.7.2 está instalado sin root en `~/.local/opt/godot` (`~/.local/bin/godot`).

## Pruebas

```bash
tools/run_tests.sh                # 91 pruebas + humo de UI headless + toques reales
tools/run_tests.sh --only=balance # sólo la simulación de balance
BALANCE_HOURS=4 tools/run_tests.sh --only=balance   # corrida más larga
tools/screenshots.sh              # capturas reales de todas las pantallas (abre ventana)
```

## Exportar a Android

Export con Gradle (por el SDK de anuncios). Comando completo, plantilla y firma en
`docs/ANDROID.md`. Resultado: `build/tycoon-argentina-<versión>.apk`.

## Regenerar arte y sonido

```bash
python3 tools/v10/build_data.py # datos de provincias/negocios/misiones (desde data/v10/provinces.json)
python3 tools/art/pxl/build.py  # interiores, calles, inicio y efectos (PXL)
python3 tools/art/generate.py   # personajes, íconos, logo, edificios, mapas y paisajes
python3 tools/sfx.py            # efectos de sonido sintetizados
```

## Documentación

- `docs/ARQUITECTURA.md` — sistemas, dependencias, cómo agregar negocios.
- `docs/ECONOMIA.md` — fórmulas, números grandes, balance y simulaciones.
- `docs/ARTE.md` — dirección pixel art, resolución, spritesheets.
- `docs/ANDROID.md` — exportación, firma, release.
- `docs/MONETIZACION.md` — anuncios recompensados (AdMob): estado, pruebas y producción.
- `docs/CUENTAS.md` — cuentas con Firebase Auth y verificación del email.
- `docs/AMIGOS.md` — amigos: códigos, ranking, mates, reglas y prueba con emuladores.
- `docs/PERFIL.md` — foto de perfil, banner, recorte y cómo probarlo.
- `docs/PASSIDLE.md` — qué se tomó de PassIdle y qué no.
- `docs/PLAY_STORE.md` — requisitos de Google Play: estado, formularios y pasos de publicación.
- `docs/PENDIENTES.md` — lo que queda para próximas versiones.
