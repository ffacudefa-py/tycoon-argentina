# Dirección de arte pixel art

- Resolución virtual **360×640** con `stretch_mode=canvas_items`, `aspect=expand` y
  `scale_mode=integer`: el escalado siempre es entero (×2, ×3, ×4) y la pantalla se
  extiende en alto/ancho en vez de deformarse. Un teléfono de 1080×2400 ve 360×800 a ×3.
- Texturas con filtro **nearest** (proyecto) y snap a píxel en transformaciones y vértices.
- Fuente: Pixelify Sans (OFL, `assets/fonts/OFL.txt`) sin antialiasing ni hinting.
  Tamaño mínimo 9 px virtuales (27 px físicos a ×3).
- Paleta cerrada de 36 colores (`tools/art/px.py`), contornos oscuros de 1 px, luz
  arriba/izquierda. Todo el arte se genera con `python3 tools/art/generate.py`
  (hoja de contacto en `docs/art_preview.png`).

## Recursos (`assets/pixel_art/`)

| Carpeta | Contenido |
|---|---|
| `businesses/` | `<id>_<0..4>.png` 200×150, apoyados en la fila inferior; `<id>_badge.png` 24×24 |
| `characters/` | `customer_<0..7>.png`, `worker_<0..7>.png` (spritesheets), `dog.png` |
| `backgrounds/` | `street_<zona>.png` 480×200 (vereda en y=150, base de edificio y=163, peatones y=172) |
| `map/` | `city_map.png` 360×540 (rectángulos de zonas en `data/world.json`) |
| `icons/` | íconos 16×16 dibujados a mano + `app_icon*.png` |
| `avatars/` | avatares 24×24 |
| `ui/` | marcos 9-slice: botones 16×16 (márgenes 4/4/4/6), paneles 24×24 (6), barras 8×8 (2), interruptores, mano del tutorial |
| `particles/` | `coin_spin.png` (4×8×8), `sparkle.png` (4×8×8), `smoke.png`, `confetti.png`, `star.png` |

### Spritesheets de personajes

- Cuadros de **16×24**, **10 columnas × 1 fila**, escala 1:1 con el mundo.
- Orden: 0–3 caminar (mirando a la derecha), 4–5 quieto, 6–7 trabajar, 8–9 celebrar.
- Para caminar a la izquierda se usa `flip_h`. Importación: nearest, sin mipmaps.
- `dog.png`: 4 cuadros de 16×12 (caminar).

### Evolución visual de los negocios

Niveles visuales en los niveles 1, 10, 25, 50 y 100 (`balance.visual_tiers`). Ej. puesto:
mesita con sombrilla → más productos, cajones y heladera → cartel con fileteado, caja
registradora y guirnalda → pequeño local → comercio de dos pisos con balcón.
Los arquetipos (puesto, kiosco, carrito, lavadero, almacén, café, restaurante, súper,
gimnasio, taller, depósito) están en `tools/art/buildings.py`.

Los personajes de la escena son decorativos: su cantidad sigue las ventas reales pero no
calculan nada; con calidad baja o ahorro de energía se reducen.
