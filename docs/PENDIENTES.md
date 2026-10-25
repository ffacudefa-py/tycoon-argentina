# Pendientes

## Verificación
- Probar el APK en un teléfono real (táctil, área segura, vibración, guardado al
  cerrar desde multitarea, rendimiento en equipos modestos).
- Revisar en un teléfono real la letra VT323 y la animación del saldo (0.6).

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
- Foto y banner en la nube (el progreso ya se guarda en Firestore desde la 0.6; ver CUENTAS.md).
- IDs reales de AdMob y consentimiento UMP (MONETIZACION.md). Compras.
- Probar anuncios de prueba y el selector de la galería en un teléfono físico.

## Conocido
- Las capturas automáticas (`tools/screenshots.sh`) abren una ventana; el gestor de
  ventanas a veces la agranda (la herramienta fuerza el tamaño).
- Los eventos no aparecen durante el tiempo offline (sólo corre su duración), por diseño.
