# Guía de estilo · Tycoon Argentina 11 (única fuente de verdad)

Referencias: `~/Descargas/inspo/` (escenario.webp, personajes.jpeg, icononegocio.webp).
Se replica la **técnica** (pixel art cálido de simulador de gestión), no personajes
ni objetos puntuales. Todo el contenido es original y argentino.

## 1. Paleta

Cálida, saturada y luminosa. Nada de negro puro ni grises fríos en los assets:
las sombras tiran a marrón/violeta cálido y las luces a crema.

| Rol | Hex | Uso |
|---|---|---|
| Contorno principal | `#3D1B0B` | borde exterior de personajes, íconos y muebles |
| Contorno suave | `#8E461F` | bordes internos, separación de piezas |
| Madera oscura / marco UI | `#94552A` | marcos de ventanas de la interfaz, muebles |
| Madera media | `#C88555` | pisos, mostradores |
| Madera clara / arena | `#E4AD69` | luces de madera, caminos |
| Dorado UI | `#F2D173` | marcos, botones principales, resaltes |
| Dorado brillante | `#F7EDA4` | destellos, borde superior de botones |
| Crema panel | `#F6EFE2` | fondos de paneles y cartas |
| Crema sombra | `#E4D7C7` | sombra de paneles, separadores |
| Cielo | `#60CAFE` → `#3DB4FE` | fondos de cielo (degradé en 3 bandas) |
| Agua | `#287AB2` | ríos, lagos, mar |
| Pasto | `#67D08E` / `#3F9E5E` | césped y vegetación |
| Rojo vivo | `#D5576E` / `#953730` | acentos, alertas, techos |
| Celeste argentino | `#74ACDF` | identidad (bandera), acentos fríos |
| Sol de Mayo | `#F6B40E` | identidad, monedas, recompensas |
| Piel | `#F3D2B6` / `#E3A988` / `#B87259` | luz / medio / sombra |
| Texto oscuro | `#3D1B0B` | texto sobre crema |
| Texto claro | `#FFFFFF` con contorno `#3D1B0B` | números grandes, cartel sobre color |

Saturación alta sólo en lo importante (botones de acción, recompensas, dinero);
fondos de UI limpios (crema) para que el color resalte.

## 2. Línea y forma

- Contorno de **1 px** en el borde exterior, color `#3D1B0B` (nunca negro).
- Bordes internos con el tono más oscuro de la rampa del material (no con el contorno).
- **Contorno selectivo**: en la cara de luz (arriba-izquierda) el contorno se aclara
  un paso (`#8E461F`) para que el volumen "respire".
- Formas **redondeadas y blandas**: esquinas recortadas 1-2 px, nada de cajas filosas.
- Sin píxeles huérfanos; diagonales en escalones regulares (1:1, 1:2).

## 3. Sombreado y luz

- Luz arriba a la izquierda. Rampa de **3-4 tonos** por material + 1 brillo.
- Sombreado suave (bloques, sin tramado salvo cielo y agua).
- Brillo especular de 1-2 px en superficies redondas (ojos, frutas, botellas, metal).
- Sombra de apoyo: elipse aplanada `#3D1B0B` al 35 % bajo personajes y objetos.

## 4. Nivel de detalle

- Alto en lo que se mira (caras, mercadería, carteles), bajo en fondos.
- Muebles y edificios con piezas reconocibles: barricas con aros, botellas con
  etiqueta, cajones con fruta, ventanas con marco y alféizar.
- Escenarios "llenos": siempre hay utilería en el piso (plantas, cajones, carteles).

## 5. Personajes

- **Chibi**: cuadro 32x48, cabeza ~**45 %** de la altura total (≈20 px), cuerpo
  corto (~22 px), pies en la fila 46.
- Ojos grandes (2x3) con brillo blanco; boca expresiva; rubor `#E3A988` en mejillas.
- Estados: **idle** (respira + parpadea), **caminar** (4 cuadros), **trabajar**
  (2), **feliz** (ojos ^^, boca abierta), **festejar** (brazos arriba, salto),
  **triste leve** (cejas caídas, gotita de sudor). Hoja de 12 cuadros:
  0-3 caminar · 4-5 idle · 6-7 trabajar · 8-9 festejar · 10 feliz · 11 triste.
- Identidad argentina: gorra, boina, pañuelo gaucho, delantal, mate, camiseta celeste y blanca.

## 6. Escenarios

- Vista **frontal elevada 3/4**: se ve el piso del negocio y la parte de arriba
  de mostradores y techos (como en escenario.webp), dentro del lienzo actual
  (calle 480x200, interior 400x170, edificios 192x150).
- Composición en 3 capas: fondo (cielo claro + paisaje regional), medio (edificio
  con detalle), frente (vereda / piso con utilería y personajes).
- Pisos con patrón suave (baldosa, madera, alfombra) y sombras de apoyo.
- Identidad regional argentina (cerros, viñedos, selva, estepa, llanura, ciudad).

## 7. Íconos

- Objeto **apoyado en una base** (plato, cajón o sombra) como icononegocio.webp.
- Silueta gorda y legible a 16 y 32 px; contorno `#3D1B0B`; 3 tonos + brillo.
- Pueden tener carita (`^^`) los íconos "simpáticos" (mascotas, recompensas).
- Fondos transparentes; sombra de apoyo elíptica.

## 8. Interfaz

- Marcos **dorados** (`#F2D173`) con borde exterior marrón (`#94552A`/`#3D1B0B`) y
  borde superior brillante (`#F7EDA4`); paneles crema con esquinas redondeadas.
- Barra superior: contadores grandes (plata, etapa) en cajas doradas; números
  blancos con contorno marrón.
- Botones: colores vivos (verde acción, dorado principal, rojo alerta, celeste
  información) con borde marrón, brillo arriba y sombra abajo; al tocar,
  squash 0,92 → rebote 1,05 → 1 en 150-250 ms.
- Tipografía pixel legible (mínimo 16 px virtuales), texto oscuro sobre crema.
- Minimalismo: la misma información de hoy, menos texto, íconos + números.

## 9. Recompensas (dopamina proporcional)

| Acción | Feedback |
|---|---|
| Tocar cualquier botón | squash/rebote + sonido corto |
| Vender a mano | moneda que salta, +$ flotante, combo |
| Subir nivel | destello en el botón, número que sube animado |
| Comprar mejora | brillo dorado en la tarjeta |
| Contratar | el empleado aparece saludando (feliz) |
| Reponer | camión/cajas + barra que se llena |
| Misión / logro | tarjeta verde con tick, confeti chico |
| Abrir negocio / conquistar provincia | confeti grande + personaje festejando |
| Completar región | celebración grande (pantalla completa) |
| Cofre | apertura con rebote y lluvia de monedas |
| Volver a entrar | resumen offline con contador que sube |

Respetar "Reducir movimiento" (Ajustes): sin rebotes ni partículas extra.
Nada de urgencia falsa ni culpa por no entrar. La animación nunca tapa el dato.

## 10. Identidad argentina que se mantiene

- Colores celeste y blanco + Sol de Mayo en acentos; la bandera en el logo.
- Referencias: mate, colectivo, fileteado porteño, productos regionales, provincias reales.
- Textos en castellano rioplatense con voseo ("Tocá", "Juntá", "¡Vamos!"), tono
  cálido y con humor.
- Tito, el guía del tutorial.

## 11. Información por pantalla (no se pierde nada)

- **Barra superior**: avatar, empresa · etapa, saldo (negativo en rojo), ingreso/s
  o cuenta regresiva del juicio, ajustes.
- **Imperio**: objetivo actual, escena del negocio (eventos, cofres, combo,
  fachada/adentro, bonos, anterior/siguiente), nombre, nivel, automatización,
  provincia, estrellas de nivel, por venta, ciclo, mercadería, próxima meta,
  barra de ciclo, VENDER, SUBIR NIVEL (x1/x10/máx), ADMINISTRAR.
- **Negocios**: propios (nivel, ganancia) y próximos (requisitos y costo).
- **Mapa**: país (regiones y avance) → región (provincias, cuota) → ficha.
- **Objetivos**: reclamar todo, recompensa diaria, principales/desafíos/diarias.
- **Perfil**: avatar, foto, banner, nombre, etapa, estadísticas, amigos.
- **Modales**: administrar (negocio, empleados, mejoras, datos), cofres, novedades,
  modo de juego, ajustes, evento, offline.

## 12. Cómo se genera el arte 11

```bash
python3 tools/art/chars3.py        # personajes chibi 32x48, 12 cuadros → assets/personajes/
python3 tools/art/generate.py      # arte base (edificios, íconos, mapas, paisajes) en assets/pixel_art/
python3 tools/art/pxl/build.py     # interiores y efectos (PXL)
python3 tools/art/restyle11.py     # pasa todo a la paleta 11 → assets/escenarios/ y assets/iconos/
                                   # (volumen 3/4 de edificios, sombras, íconos con base; al final ui11)
```
`U.tex()` busca primero en `assets/personajes`, `assets/escenarios` y `assets/iconos`
y, si no está, usa `assets/pixel_art` (arte anterior).
