<p align="center">
  <img src="assets/pixel_art/logo/logo_coronados.png" alt="Coronados de Gloria" width="363">
</p>
<p align="center">
  <img src="assets/pixel_art/logo/icono_192.png" alt="Ícono de la app" width="96">
</p>

# Coronados de Gloria (antes Tycoon Argentina)

**Descargar:** todos los APK de Android, de la 0.1.0 a la última, están en un solo
lugar: [tycoon-argentina-descargas → Releases](https://github.com/ffacudefa-py/tycoon-argentina-descargas/releases)
([última versión](https://github.com/ffacudefa-py/tycoon-argentina-descargas/releases/latest)).
Son versiones de prueba firmadas con clave de depuración.

Simulador de negocios pixel art para Android (Godot 4.7, GDScript, vertical).
El objetivo es conquistar la Argentina región por región y provincia por
provincia. Empezás con un campito de algodón en Santiago del Estero (NOA) y cada
provincia tiene su negocio según su producto icónico: papas andinas en Jujuy,
Malbec en Mendoza, yerba en Misiones, medialunas en CABA… Le ganás el mercado al
rival local hasta el 100 % y la provincia es tuya. Niveles, mejoras, mercadería,
empleados, automatización, ingresos offline, eventos, misiones, logros,
prestigio, amigos y minijuegos. Reglas: `docs/CONQUISTA.md`.

Todo el arte, los sonidos, los nombres y las empresas son originales y ficticios.

## Cómo está organizado el repo

- **Una sola rama: `main`.** Tiene toda la historia, de la 0.1.0 a la última,
  en orden y sin ramas paralelas.
- **Cada versión tiene su etiqueta** (`v0.1.0` … `v15.1`) en el
  commit desde el que se armó. `git checkout v12.1` deja el código de esa versión.
- **Los APK** están sólo en el repo público de descargas, uno por release, con
  la misma etiqueta que acá.

## Historial de versiones

Lo más nuevo arriba. Cada versión dice sólo lo que **agregó**: lo anterior sigue
incluido. "Sin APK" = la versión existe en el código pero no se publicó.

### 15.3 — 27 nov 2026 · Prueba cerrada de Google Play
- Inicio sin sesión: INICIAR SESIÓN es el botón grande; JUGAR COMO INVITADO pasa a
  la fila chica junto a CONFIGURACIÓN (con cuenta se cuentan los días de la prueba).
- Tutorial: en todos los pasos se oscurece lo que no hay que tocar (más suave y sin
  bloquear en los pasos que sólo señalan).
- Cofres rebalanceados: plata 20–45 s de ingreso (antes 45–120 s) y 60–120 s (antes
  240–420 s), turbo x1,5 de 2–5 min (antes x2 de 5–15 min): ~50 s de ingreso por cofre
  en promedio, antes ~4 min. Botón ABRIR TODOS (sin ruleta, un solo festejo).
- Contador de combo con el estilo del juego: panel oscuro, rayo, número dorado (naranja
  en el máximo) y barra del tiempo que queda para seguir el combo.

### 15.2 — 23 nov 2026 · Sin APK (prueba cerrada de Google Play)
Preparación para Google Play:
- Asalto con la chancleta de la abuela en vez de la pistola (clasificación por
  edades más baja): se revolea hacia el toque y el ladrón queda mareado.
- Insignias: hasta 3 en el perfil; la de Pionero para quien juega la prueba cerrada.
- Bloquear y denunciar jugadores, perfil visible sólo para amigos y solicitudes,
  tope de 20 solicitudes por día y fotos sólo JPEG/PNG.
- Moderación desde la planilla de administración (ocultar foto, quitar nombre,
  expulsar de Amigos); el juego la respeta y avisa.
- Programa de pioneros (inscripción web y registro de días jugados).
- La versión de Play no avisa de APKs de GitHub.

### 15.1 — 22 nov 2026 · [APK](https://github.com/ffacudefa-py/tycoon-argentina-descargas/releases/tag/v15.1)
Correcciones de la revisión de código de la 15.0-prelanzamiento:
- Foto de perfil privada por defecto (se activa en Configuración); los envíos
  del perfil van de a uno.
- La nube sube una copia cada 5 min si hubo cambios; "Sincronizar ahora" sube
  en el momento.
- Notificaciones: se reprograman al reiniciar el teléfono, se agendan al salir
  con "atrás", se atienden al abrir en frío y dos avisos de evento no coinciden.
- Migración de partidas v5: sueldos de empleados ajustados a las bases nuevas;
  el costo de contratar usa el exponente del rol.
- Ventana de novedades actualizada a la 15.

### 15.0-prelanzamiento — 6 nov 2026 · [APK](https://github.com/ffacudefa-py/tycoon-argentina-descargas/releases/tag/v15.0-prelanzamiento)
- Sonidos propios hechos en FL Studio (toques, subir de nivel, mejoras,
  desbloqueos, contrataciones, misiones, eventos, caja y fanfarrias); la moneda
  tiene 5 golpes distintos.
- Guías de Tito en cada menú (solas la primera vez y con el botón (i)).
- Notificaciones en Android: caja llena, eventos, versión nueva y solicitudes de amistad.
- 62 logros en 6 categorías y 4 rangos, con insignias nuevas.
- Empleados: sueldos que siguen a la ganancia del local y 6 roles nuevos
  (pasante, sobrino, cadete, patovica, vendedor estrella, contador).
- Animaciones de trabajo según el rubro; menos clientes caminando.
- Modo bien argentino: ya no bloquea nada, sólo endurece inflación, juicios,
  robos y minijuegos.
- Varios eventos a la vez en una lista; ruleta de cofres visible en el teléfono;
  foto de perfil de los amigos (se puede desactivar).
- La nube sube la partida al salir del juego.

### 15.0-beta1 — 6 nov 2026 · [APK](https://github.com/ffacudefa-py/tycoon-argentina-descargas/releases/tag/v15.0-beta1)
- Música de fondo con loop sin cortes (se apaga o regula en Configuración).
- Pantalla de inicio nueva: postal animada del Noroeste.
- Tránsito: 15 vehículos redibujados; el colectivo para y abre las puertas.
- Textos más legibles en todo el juego (contraste corregido).

### 14.0 — 5 nov 2026 · [APK](https://github.com/ffacudefa-py/tycoon-argentina-descargas/releases/tag/v14.0)
- Fachadas con luz y sombras, sombra de cada edificio sobre la vereda.
- Paisajes regionales pintados con luz y calle propia por provincia (CABA usa la del centro).

### 13.0 — 4 nov 2026 · [APK](https://github.com/ffacudefa-py/tycoon-argentina-descargas/releases/tag/v13.0)
- Asalto: arreglados los ladrones invisibles; corren en curvas suaves y se frenan en cada tramo.
- Manos con volumen (guante de cuero, pistola más grande) y bolsa de arpillera.
- Interiores con luz de cada lámpara, ventana con vista según el rubro y muebles
  propios de cada rubro, sin nada encimado ni cortado.
- Escritorio de la coima con más detalle.

### 12.1 — 3 nov 2026 · [APK](https://github.com/ffacudefa-py/tycoon-argentina-descargas/releases/tag/v12.1)
- Asalto en primera persona (pistola y bolsa en pantalla) y coima con comisaría y patrullero.
- Botones "Practicar asalto/coima" en Ajustes, sin consecuencias.
- 46 muebles de interiores redibujados con aspecto 3D.
- Arreglo: clientes y colectivos ya no se quedan caminando en el lugar.

### 12.0 — 1 nov 2026 · [APK](https://github.com/ffacudefa-py/tycoon-argentina-descargas/releases/tag/v12.0)
- Minijuegos **¡Asalto!** y **La coima**, en los dos modos de juego.
- Accesibilidad: respetan "reducir movimiento", sin parpadeos rápidos y con marcas ✕/✓.

### 11.1 — 1 nov 2026 · sin APK (incluida en la 12.0)
- La conquista avanza según tu ritmo de inversión en vez de un temporizador;
  mejoras más caras y rival con tope de crecimiento.

### 11.0 — 30 oct 2026 · [APK](https://github.com/ffacudefa-py/tycoon-argentina-descargas/releases/tag/v11.0)
- Nuevo nombre **Coronados de Gloria**, con logo e ícono nuevos.
- Saldo tipo tragamonedas con rodillos y ruleta al abrir cofres.
- Botón de bonos por anuncio más visible, colectivos porteños de 4 líneas e
  ícono de producto para cada negocio.
- Provincias lejanas rebalanceadas; arreglos de nube, cuenta y amigos; mejor rendimiento.

### 10.3 — 28 oct 2026 · [APK](https://github.com/ffacudefa-py/tycoon-argentina-descargas/releases/tag/v10.3)
- Ciclo de juego: combo de ventas hasta x2, cofres que se ganan jugando,
  "próxima meta" por negocio y eventos regionales (Vendimia, Zafra, Fiesta de la Yerba…).
- Rediseño visual: guía de estilo y paleta cálida.
- Es la primera versión publicada de la serie 10 e incluye todo lo de 10.0 a 10.2.

### 10.2 — 28 oct 2026 · sin APK (incluida en la 10.3)
- Edificios con diseño distinto en cada uno de los 5 niveles.
- Cuenta regresiva del juicio laboral en la barra superior.

### 10.1 — 28 oct 2026 · sin APK (incluida en la 10.3)
- **Modo bien argentino** (opcional): +25 % de ingresos con inflación, juicios
  laborales, robos y coimas.
- Arreglo: Objetivos ya no se traba al cambiar de pestaña durante un reclamo.

### 10.0 "Sigma Deza" — 28 oct 2026 · sin APK (incluida en la 10.3)
- **Conquista de la Argentina**: 24 negocios, uno por provincia, contra un rival local.
- Mapa pixel art del país en dos niveles (regiones y provincias).
- Arte propio de cada provincia: edificios, interiores y paisajes por región.
- La partida empieza de cero (se conserva el perfil).

### 0.7.2 — 28 oct 2026 · sin APK (incluida en la 10.3)
- Monedas nuevas, empleados con retrato, scroll arrastrando desde cualquier parte.
- (0.7.1) Cambio y borrado de cuenta, consentimiento de anuncios y páginas legales.

### 0.7.0 — 25 oct 2026 · [APK](https://github.com/ffacudefa-py/tycoon-argentina-descargas/releases/tag/v0.7.0)
- Amigos: código de 6 letras, ranking y mates diarios.
- Verificación de email; correos de la cuenta en castellano.
- Reclamar todo de una vez en Objetivos; animaciones de botones, mejoras y negocios nuevos.
- Partidas más largas (ganancias al 80 %) y saldo negativo en rojo.

### 0.6.0 — 25 oct 2026 · [APK](https://github.com/ffacudefa-py/tycoon-argentina-descargas/releases/tag/v0.6.0)
- Progreso en la nube con Firestore.
- Saldo estilo casino, letra VT323, mapa y avatares nuevos, carteles que no se salen.

### 0.5.0 — 23 oct 2026 · [APK](https://github.com/ffacudefa-py/tycoon-argentina-descargas/releases/tag/v0.5.0)
- Pantalla de inicio, cuentas con email y foto de perfil con recorte.
- Negocios vistos por dentro, bonos opcionales por anuncio y configuración completa.

### 0.4.0 — 23 oct 2026 · [APK](https://github.com/ffacudefa-py/tycoon-argentina-descargas/releases/tag/v0.4.0)
- Pixel art nuevo: 12 negocios animados en 5 niveles, personajes e íconos más grandes.

### 0.3.0 — 21 oct 2026 · [APK](https://github.com/ffacudefa-py/tycoon-argentina-descargas/releases/tag/v0.3.0)
- Administrar en 4 categorías, colores con sentido y botones que dicen cuánto falta.

### 0.2.0 — 21 oct 2026 · [APK](https://github.com/ffacudefa-py/tycoon-argentina-descargas/releases/tag/v0.2.0)
- Letra más grande, objetivo siempre visible, botón principal único, tutorial y logo nuevo.

### 0.1.0 — 21 oct 2026 · [APK](https://github.com/ffacudefa-py/tycoon-argentina-descargas/releases/tag/v0.1.0)
- Primera versión jugable: 12 negocios, empleados, ingresos offline, mapa,
  rivales, misiones, logros y prestigio.

### Firmas de los APK
La 11.0 y la 14.0 se armaron en otra PC y tienen otra firma: para instalarlas
hay que desinstalar la versión que tengas (con cuenta, la partida vuelve desde
la nube). Las demás desde la 0.6 se instalan una encima de otra.

## Ejecutar

```bash
godot --path .            # juego (ventana 405x880)
godot --path . -e         # editor
```
Necesita Godot 4.7.2.

## Pruebas

```bash
tools/run_tests.sh                # pruebas + humo de UI headless + toques reales
tools/run_tests.sh --only=balance # sólo la simulación de balance
BALANCE_HOURS=4 tools/run_tests.sh --only=balance   # corrida más larga
FULL_GAME=1 tools/run_tests.sh --only=full_game     # partida completa (24 provincias, ~1 h)
tools/screenshots.sh              # capturas reales de todas las pantallas (abre ventana)
```

## Exportar a Android

Export con Gradle (por el SDK de anuncios). Comando completo, plantilla y firma en
`docs/ANDROID.md`. El APK se publica en el repo de descargas con la etiqueta
`v<versión>`, que debe coincidir con `application/config/version` (el aviso de
versión nueva compara esos textos).

## Regenerar arte y sonido

```bash
python3 tools/v10/build_data.py    # datos de provincias/negocios/misiones (desde data/v10/provinces.json)
python3 tools/art/pxl/build.py     # calles, inicio y efectos (PXL)
python3 tools/art/generate.py      # personajes, íconos, logo, edificios, mapas y paisajes
                                   # (el ícono de la app sale de tools/art/fuentes/iconocoronados.png)
python3 tools/sfx.py               # efectos de sonido sintetizados
python3 tools/audio/import_sfx.py  # sonidos exportados de FL Studio
python3 tools/audio/make_music.py  # música
```

## Documentación

- `docs/ARQUITECTURA.md` — sistemas, dependencias, cómo agregar negocios.
- `docs/CONQUISTA.md` — reglas y balance de la conquista.
- `docs/ECONOMIA.md` — fórmulas, números grandes, balance y simulaciones.
- `docs/ARTE.md` y `docs/style-guide.md` — dirección pixel art, resolución, spritesheets.
- `docs/ANDROID.md` — exportación, firma, release.
- `docs/MONETIZACION.md` — anuncios recompensados (AdMob): estado, pruebas y producción.
- `docs/CUENTAS.md` — cuentas con Firebase Auth y verificación del email.
- `docs/AMIGOS.md` — amigos: códigos, ranking, mates, reglas y prueba con emuladores.
- `docs/PERFIL.md` — foto de perfil, banner, recorte y cómo probarlo.
- `docs/MINIJUEGOS.md` — asalto y coima: reglas, balance, arte, pruebas y capturas.
- `docs/PASSIDLE.md` — qué se tomó de PassIdle y qué no.
- `docs/PLAY_STORE.md` — requisitos de Google Play: estado, formularios y pasos de publicación.
- `docs/PENDIENTES.md` — lo que queda para próximas versiones.
