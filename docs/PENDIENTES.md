# Pendientes

## Verificación
- Probar el APK en un teléfono real (táctil, área segura, vibración, guardado al
  cerrar desde multitarea, rendimiento en equipos modestos).
- Revisar legibilidad de la fuente pixel a ×2 (teléfonos de 720 px de ancho).

## Contenido (v2)
- Negocios 13–25 del documento (tienda de tecnología, hotel, fábrica, cadena de
  supermercados, transporte, constructora, parque industrial, shopping, tecnológica,
  red logística, complejo hotelero, franquicias, conglomerado). La arquitectura ya lo
  permite agregando datos (ver ARQUITECTURA.md); falta balancearlos y quizá subir el
  tope numérico (ECONOMIA.md).
- Más arquetipos de edificios y animaciones específicas (lavado con espuma animada,
  humo de parrilla animado).
- Música (hoy no hay; el ajuste no se muestra).

## Plataforma
- Firma release y AAB para Play Store (ANDROID.md).
- Cuentas y nube: el modelo se serializa con `GameModel.to_dict()`, así que basta un
  servicio que suba/baje ese payload; no hay botones de login en esta versión.
- Anuncios y compras reales (MONETIZACION.md).

## Conocido
- Las capturas automáticas (`tools/screenshots.sh`) abren una ventana; el gestor de
  ventanas a veces la agranda (la herramienta fuerza el tamaño).
- Los eventos no aparecen durante el tiempo offline (sólo corre su duración), por diseño.
