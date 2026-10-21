# Rediseño 2.0 — UI legible, pixel art detallado y logo

## 1. Interfaz para jugadores nuevos

### Diagnóstico de la v0.1
- Textos de 9–10 px virtuales (≈ 9–10 sp en el teléfono): chicos y apretados.
- La tarjeta del negocio mezcla 9 cosas a la vez (estadísticas, ciclo, stock, automatización, vender, subir, hito, administrar).
- El objetivo actual está escondido en la pestaña Objetivos.
- Colores sin regla: el amarillo se usa para "subir nivel", para avisos y para premios.

### Reglas nuevas
| Regla | Valor | Por qué |
|---|---|---|
| Tamaños de letra (px virtuales) | 12 mínimo · 14 texto · 18 títulos · 24 plata | A ×3, 12 px ≈ 13–14 sp: el mínimo legible de Android |
| Contraste | Texto oscuro #1B1A2E sobre crema/blanco, o blanco sobre #2E2B48 (≥ 7:1) | La fuente pixel pierde legibilidad con poco contraste |
| Interlineado / aire | 4 px entre líneas, 8 px entre bloques, 12 px de margen | Evita la sensación de pantalla saturada |
| Botón principal | Alto 44 px virtuales (≈ 50 dp), ancho completo | Supera el mínimo de 48 dp para el pulgar |
| Botón secundario | Alto 36 px, ícono + texto | |
| Íconos | 32×32 con etiqueta debajo; 16×16 sólo junto a números | Un ícono sin texto no se entiende la primera vez |
| Una acción principal por pantalla | Un solo botón grande destacado | El jugador nuevo sabe qué tocar |
| Feedback al tocar | Hundido 2 px + escala 0,95 por 80 ms + sonido + vibración 10 ms; deshabilitado = gris con candado y motivo | Confirma el toque y explica por qué no se puede |
| Color con sentido | Verde #4C9A4F = ganancia · Rojo #B83A3F = pérdida o peligro · Amarillo #F6B40E = aviso o atención · Celeste #74ACDF = acción o información · Blanco = neutro | Que el color signifique siempre lo mismo |
| Plata | Siempre arriba: saldo en 24 px blanco con moneda y "+$X/s" en verde debajo | Es lo que más mira el jugador |
| Objetivo actual | Franja fija bajo la barra superior: misión + barra + premio; tocándola se abre Objetivos | El jugador siempre sabe qué hacer después |

### Wireframes (360 px de ancho)

**IMPERIO (pantalla principal)**
```
┌──────────────────────────────────────┐
│ (☺) Mi Empresa        [⚙]           │  barra superior, 52 px
│      $ 12,5 mil                      │  saldo 24 px blanco
│      +$48/s  ▲                       │  ganancia 14 px verde
├──────────────────────────────────────┤
│ 🎯 OBJETIVO: Comprá tu mercadería    │  franja de objetivo, 40 px, toque → Objetivos
│ [██████░░░░] 1/1   Premio: $40       │
├──────────────────────────────────────┤
│                                      │
│  <   [ diorama del negocio 170 px ]  > │  flechas 36×36
│        PUESTO CALLEJERO · Nv 7       │  cartel sobre la escena
├──────────────────────────────────────┤
│ [💰 $3,2/venta] [⏱ 1,0 s] [📦 60 %] │  3 fichas: ícono 32 + valor 14 + etiqueta 12
├──────────────────────────────────────┤
│ ┌──────────────────────────────────┐ │
│ │        ¡VENDER!                  │ │  botón principal 44 px (cambia según el
│ └──────────────────────────────────┘ │  momento: REPONER / VENDE SOLO ✓)
│ ┌───────────────────────┐ ┌───────┐ │
│ │ ▲ SUBIR NIVEL  $48    │ │  x1   │ │  botón secundario 36 px
│ │   +$2/s               │ └───────┘ │
│ └───────────────────────┘           │
│ [ ⚙ ADMINISTRAR NEGOCIO ]            │  secundario, abre la hoja de categorías
├──────────────────────────────────────┤
│ [👑]   [🏪]    [🗺]   [🚩]   [👤]   │  barra inferior 60 px
│ IMPERIO NEGOCIOS MAPA OBJETIVOS PERFIL│  etiquetas 12 px, la activa sobre fondo amarillo
└──────────────────────────────────────┘
```

**ADMINISTRAR (hoja desde abajo, 4 categorías)**
```
┌──────────────────────────────────────┐
│ Puesto callejero            [ X ]    │
│ [NEGOCIO] [EMPLEADOS] [MEJORAS] [DATOS]│  pestañas con ícono 32 + texto
├──────────────────────────────────────┤
│ NEGOCIO: mercadería y zona           │
│ 🍫 Alfajores   ███████░░  40/60      │
│    Vendés $5 · Comprás $2,4 · +52 %  │  ganancia en verde
│ 🥤 Bebidas     ██░░░░░░░  12/60 ⚠    │  aviso en amarillo si < 25 %
│ [ REPONER TODO  $120 ]               │  botón principal
│ Zona: Barrio Villa Esperanza [Mudar] │
├──────────────────────────────────────┤
│ EMPLEADOS: tarjeta por persona       │
│ [🧑] Chiche Benítez · Vendedor        │
│     "Vende solo"  Sueldo -$1,2/s 🔴   │
│ Candidatos → [CONTRATAR $180]        │
├──────────────────────────────────────┤
│ MEJORAS: una por fila, la próxima   │
│ disponible primero, las bloqueadas   │
│ abajo con candado y requisito        │
│ [📦] Conservadora grande  Nv 1/5     │
│      +50 % mercadería → +$3/s 🟢     │
│      [ COMPRAR $48 ]                 │
└──────────────────────────────────────┘
```

**NEGOCIOS**
```
│ TUS NEGOCIOS                         │
│ [🏪] Puesto   Nv 7   +$12/s 🟢 [VER] │  una fila por negocio, 56 px
│ [🍬] Kiosco   Nv 3   SIN STOCK ⚠ [VER]│
│ PRÓXIMO PARA ABRIR                   │
│ [🌭] Puesto de comida                │
│     🔒 Kiosco nivel 10 (3/10)        │  requisito con barra de progreso
│     [ ABRIR $40 mil ] (gris)         │
```

**OBJETIVOS**
```
│ 🎁 RECOMPENSA DIARIA  [RECLAMAR]     │  fija arriba si está disponible
│ AHORA                                │  1 misión grande con barra y premio
│ PRÓXIMAS (2, en gris)                │
│ DESAFÍOS / DIARIAS (pestañas)        │
```

**TUTORIAL (capa encima de todo)**
```
│▓▓▓▓▓▓▓▓▓ pantalla oscurecida ▓▓▓▓▓▓▓▓│
│ ┌──────────────────────────────────┐ │
│ │ (Tito) Paso 2 de 6               │ │  globo con mascota, máx. 2 líneas
│ │ Comprá mercadería para vender.   │ │
│ └──────────────┬───────────────────┘ │
│        👆  [ REPONER $20 ]  ← recorte iluminado y pulsante
│                                [Saltar]│
```

### Misión guiada inicial (tutorial paso a paso)
El jugador arranca con el puesto **cerrado y sin mercadería** (hoy arranca abierto y con stock).

| Paso | Globo de Tito | Se completa cuando | Premio |
|---|---|---|---|
| 1 | "Abrí tu puestito: tocá la persiana." | Toca el puesto (la persiana sube) | — |
| 2 | "Comprá tu primera mercadería." | Primera reposición | $10 |
| 3 | "Vendé tu primer producto: tocá ¡VENDER!" | 1.ª venta | $20 |
| 4 | "Con la ganancia, subí de nivel: más clientes por venta." | Nivel 2 | $20 |
| 5 | "Contratá un vendedor y el puesto vende solo." | 1.ª contratación | Turbo x2 por 5 min |
| 6 | "¡Abrí tu primer kiosco!" | Compra del kiosco | $300 + avatar |

- Pasos 1–3 en menos de 30 s, sin texto extra. El resto de la pantalla queda oscurecido y sólo se puede tocar el objetivo; desde el paso 4 ya no se bloquea nada.
- Cada globo dice una sola cosa y nombra el botón tal como está escrito.
- "Saltar" siempre visible. Si el tutorial se abandona, la franja de objetivo sigue guiando.

### Lista de cambios concretos
1. **Escala tipográfica 12/14/18/24 y eliminar todo texto menor a 12.** Hoy el mínimo es 9. *Por qué:* es la queja principal; a ×3, 12 px ≈ 14 sp.
2. **Franja "Objetivo actual" fija bajo la barra superior.** *Por qué:* responde siempre "¿qué hago ahora?", clave para el objetivo de 30 s.
3. **Barra superior con la plata en 24 px y la ganancia en verde debajo; las estadísticas pasan a Perfil.** *Por qué:* jerarquía, lo más importante es lo más grande.
4. **Un único botón principal contextual** (VENDER → REPONER si no hay stock → "VENDE SOLO ✓" si está automatizado). *Por qué:* hoy "Vender", "Reponer" y "Subir" compiten; el jugador nuevo no sabe cuál tocar.
5. **Tarjeta del negocio reducida a 3 fichas** (por venta, ciclo, mercadería) más los botones. El resto pasa a Administrar. *Por qué:* hoy la tarjeta muestra 9 bloques.
6. **Administrar con 4 categorías: Negocio (mercadería y zona), Empleados, Mejoras, Estadísticas.** *Por qué:* es lo que pediste, y agrupa por intención.
7. **Íconos 32×32 con etiqueta debajo** en la navegación, las fichas y las pestañas. *Por qué:* reconocimiento más rápido y sin ambigüedad.
8. **Altos mínimos: botón principal 44 px, secundario 36 px, pestañas 40 px.** *Por qué:* táctil cómodo con el pulgar.
9. **Feedback al tocar** (hundido, escala, sonido, vibración), y los botones bloqueados muestran el motivo. *Por qué:* hoy un botón gris no explica nada.
10. **Colores con sentido** (tabla de arriba): costos impagables en rojo, ganancias en verde, avisos de stock en amarillo. Subir de nivel pasa de amarillo a celeste. *Por qué:* consistencia; el amarillo queda reservado para avisos.
11. **Tutorial con foco iluminado** y misión guiada de 6 pasos; arranque con el puesto cerrado y sin stock. *Por qué:* aprender haciendo, con el ciclo comprar → vender → reinvertir explícito.
12. **Avisos (toasts) abajo, sobre la barra de navegación, de a uno y en 2 líneas como máximo.** Hoy tapan la escena. *Por qué:* no compiten con la información principal.
13. **Requisitos con barra de progreso** ("Kiosco nivel 10: 3/10"). *Por qué:* convierte un candado en una meta.
14. **Paleta de interfaz limitada a la paleta 2.0:** fondos #2E2B48, tarjetas #F3E1BC/#FFFFFF, acentos celeste #74ACDF y amarillo sol #F6B40E. *Por qué:* coherencia con el arte y con la marca.

## 2. Pixel art 2.0

### Guía de estilo
**Escala del mundo:** 1 metro = 24 px. Todo se dibuja 1:1 en la resolución virtual y el juego escala ×2/×3/×4 enteros.

| Asset | Tamaño | Notas |
|---|---|---|
| Íconos de UI y productos | 32×32 (versión de 16×16 sólo para texto en línea) | Silueta reconocible en 1 color |
| Personajes | Cuadros de 32×48 (cuerpo ≈ 22×44) | Cabeza ≈ 12 px: grande para expresar |
| Edificios | 192×160 por nivel visual | Apoyados en la última fila |
| Vehículos | Colectivo 96×48, auto 48×24 | |
| Escena | 360(+ancho extra)×220 | Fondos por zona en 3 capas con parallax leve |
| Logo / ícono | 128×128 / 64×64 | |

**Paleta 2.0 (32 colores)**

| Rampa | Sombra → luz |
|---|---|
| Contorno y neutros | `#1B1A2E` `#2E2B48` `#4A4766` `#6E6B8C` `#9B98B5` `#C9C7DA` `#F0EEE6` `#FFFFFF` |
| Celeste | `#2F6EA8` `#4E8FC9` `#74ACDF` `#A9D2F2` |
| Amarillo sol | `#B5700A` `#F6B40E` `#FFD458` `#FFF0A8` |
| Rojo | `#7E2230` `#B83A3F` `#E2665A` |
| Verde | `#2D6A3E` `#4C9A4F` `#8CCB6C` |
| Madera / cuero | `#4A2E22` `#7A4B30` `#A8714A` `#D9A877` |
| Piel | `#8A5A40` `#C98E66` `#F2C6A0` |
| Crema / pared | `#D8BD8C` `#F3E1BC` |
| Naranja | `#E0802F` |

**Reglas de sombreado y línea**
1. Luz arriba a la izquierda, a 45°, en todo el set.
2. Cada material usa su rampa: sombra, medio y luz, más un brillo opcional. Máximo 4 tonos por material.
3. Contorno exterior de 1 px `#1B1A2E`. Las líneas internas usan el tono más oscuro de la rampa del material, nunca negro.
4. Sin "píxeles huérfanos": todo píxel debe tener al menos un vecino del mismo color, salvo brillos puntuales intencionales.
5. Líneas sin escalones irregulares: patrones de paso constantes (1-1, 2-2, 3-3 o 2-1-2) y nada de 1-3-1.
6. Curvas grandes (más de 8 px) con antialias manual de 1 tono intermedio, sólo hacia adentro; nunca sobre el contorno exterior.
7. Tramado (dither) de tablero sólo en cielos y superficies grandes. Nada de tramado en personajes ni íconos.
8. Sin degradados suaves ni filtros: cada color sale de la paleta.
9. Sombra proyectada: 1 tono más oscuro del suelo, elipse de 2 px de alto bajo personajes y objetos.
10. Texturas sugeridas, no dibujadas píxel a píxel: ladrillo cada 6 px, baldosa vainilla cada 5 px, chapa cada 4 px.
11. Animaciones de 2 a 4 cuadros, en el mismo lienzo, con el pivote en la base al centro y sin desplazamientos de subpíxel:
    - caminar 4 cuadros a 8 fps;
    - humo de parrilla 3 cuadros a 6 fps;
    - cartel parpadeando 2 cuadros con intervalo irregular (0,1 s apagado cada 2–4 s);
    - toldo flameando 2 cuadros a 3 fps;
    - colectivo pasando con rueda de 2 cuadros.

**Detalles argentinos y dónde van**

| Detalle | Uso |
|---|---|
| Mate y termo | Avatar, manos de empleados en reposo, ícono de "descanso" |
| Facturas y medialunas, empanadas | Productos del almacén, la cafetería y el puesto de comida; nuevo producto "Empanadas" |
| Colectivo fileteado | Pasa por la calle de fondo cada 20–40 s (decorativo) |
| Cartel "SE VENDE" / "SE ALQUILA" | Locales del mapa todavía bloqueados |
| Persiana metálica de kiosco | Negocio cerrado o sin stock: baja la persiana |
| Fileteado porteño | Carteles de los niveles 3+, marcos de logros, pantalla de prestigio |
| Camisetas de fútbol (genéricas, sin escudos reales) | Ropa de clientes, evento "Final del campeonato" |
| Obelisco | Silueta genérica en el horizonte del Microcentro (monumento público, sin marcas) |
| Baldosas vainilla, árboles de plátano, garita | Fondos del barrio |

### Assets prioritarios a rehacer
| Prioridad | Asset | Cantidad | Por qué primero |
|---|---|---|---|
| P1 | Íconos de UI a 32×32 (navegación, plata, ganancia, mercadería, reloj, candado, ajustes, objetivo) | ~20 | Se ven en todas las pantallas y resuelven la legibilidad |
| P1 | Puesto callejero, 5 niveles a 192×160, con persiana y animación de toldo | 5 | Es lo primero que ve todo jugador |
| P1 | Personajes 32×48: vendedor, 4 clientes, mascota Tito (caminar, quieto, atender, festejar) | 6 hojas | Dan vida a la primera pantalla |
| P2 | Kiosco y puesto de comida a 192×160 (humo de parrilla de 3 cuadros, cartel con parpadeo) | 10 | 2.º y 3.º negocio |
| P2 | Productos a 32×32 (alfajor, bebida, snack, golosina, empanada, choripán, facturas, mate) | ~24 | Lista de mercadería y efectos de venta |
| P2 | Fondo del barrio en 3 capas + colectivo | 3 + 1 | Escena principal |
| P3 | Resto de los negocios, fondos por zona con obelisco, mapa a 360×540 con más detalle | — | Se ven más adelante en la partida |
| P3 | Marcos de UI 9-slice con esquinas fileteadas, partículas 16×16 | — | Pulido |

## 3. Logo

Archivos generados en `assets/pixel_art/logo/` con `python3 tools/art/logo.py`:
- `logo_128.png`: logo completo, con `logo_512.png` escalado ×4 para mostrarlo grande.
- `icono_64.png`: variante de ícono, simplificada con la bandera más grande. Escalas: `icono_192.png` (launcher) y `icono_512.png` (tienda).
- `icono_adaptativo_frente.png` / `icono_adaptativo_fondo.png` (432×432, Android adaptativo, zona segura central).
- `preview_logo.png`: el logo junto al ícono a 192, 96, 48 y 24 px, para comprobar la legibilidad.

### Decisiones
- **Composición en dos planos:**
  - bandera arriba a la izquierda, en primer plano, flameando con 1,6 ondas;
  - el flameo crece hacia la punta, como con viento real;
  - almacén abajo a la derecha, sin que la bandera tape el cartel.
- **Volumen de la tela:** cada columna se sombrea según la pendiente de la onda (luz, medio, sombra). Sin degradados.
- **Sol de Mayo:**
  - 16 rayos que alternan rectos y ondulados, con carita en la versión grande;
  - en el ícono se simplifica a disco más rayos para que no ensucie en tamaño chico.
- **Almacén:**
  - cartel azul con letras amarillas de 5×7 px y volutas de fileteado;
  - toldo celeste y blanco con festón;
  - vidriera con estantes de mercadería;
  - persiana a medio bajar con cartel de oferta;
  - macetas y vereda de baldosas.
- **Colores:** usa `#74ACDF`, `#FFFFFF` y `#F6B40E` como base. 26 colores de la paleta 2.0 y contorno `#1B1A2E` en todo.
- **Legibilidad:** en 48 px la bandera con el sol sigue siendo reconocible; en 24 px queda la silueta celeste-blanco-celeste.

### Prompt para un generador de imágenes
> Pixel art app icon, 128x128 pixels, crisp hard pixel edges, no anti-aliasing, limited palette of 32 colors, clean 1px dark navy outlines (#1B1A2E), consistent top-left lighting with 3-tone shading ramps. Foreground: the Argentine flag (horizontal bands light blue #74ACDF, white #FFFFFF, light blue #74ACDF) waving in the wind on a wooden flagpole with a golden finial, the Sun of May in the center of the white band (golden yellow #F6B40E, 16 alternating straight and wavy rays, small friendly face), cloth folds shown with stepped light and shadow columns. Background: a charming Buenos Aires neighborhood corner store ("almacén de barrio") with a striped light blue and white scalloped awning, a dark blue sign with yellow pixel letters reading "ALMACÉN" framed with filete porteño ornaments, a shop window with shelves of colorful jars and packages, a half-rolled metal shutter with an offer sign, potted plants, vanilla-colored sidewalk tiles. Simple sky gradient background (light blue to white) with one small pixel cloud. Square, centered composition, readable at 48x48, cozy tycoon game style, cheerful, no text other than the store sign.
>
> Negative prompt: blurry, anti-aliased, smooth gradients, 3D render, photorealistic, noisy dithering, jagged inconsistent outlines, orphan pixels, extra flags, wrong flag colors, red or other colors in the flag, real brand logos, watermark, signature, cropped flag.

## Plan de implementación priorizado

**Fase 1, legibilidad y primeros 30 segundos (lo más urgente):**
1. Escala tipográfica 12/14/18/24 y quitar todo texto menor a 12.
2. Franja de objetivo fija y barra superior con la plata grande.
3. Botón principal contextual y tarjeta del negocio con 3 fichas.
4. Misión guiada de 6 pasos con foco iluminado; arranque con el puesto cerrado y sin stock.
5. Instalar el ícono nuevo en el preset Android (ya generado).
6. Verificación:
   - capturas automáticas a 360 px;
   - prueba con 3 personas que nunca jugaron: medir si llegan a la primera venta en menos de 30 s.

**Fase 2, organización y feedback:**
1. Administrar con 4 categorías (Negocio, Empleados, Mejoras, Estadísticas).
2. Colores con sentido, feedback de toque y motivo en los botones bloqueados.
3. Avisos abajo y de a uno; requisitos con barra de progreso.

**Fase 3, pixel art 2.0 (empezando por lo P1):**
1. Paleta 2.0 en `tools/art/px.py`.
2. Íconos a 32×32.
3. Puesto en 192×160.
4. Personajes 32×48 con animaciones.
5. Después P2 (kiosco, comida, productos, fondo del barrio con colectivo) y por último P3.
