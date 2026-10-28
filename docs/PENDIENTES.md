# Pendientes

## Verificación
- Probar el APK en un teléfono real (táctil, área segura, vibración, guardado al
  cerrar desde multitarea, rendimiento en equipos modestos).
- Revisar en un teléfono real la letra VT323 y la animación del saldo (0.6).

## 10.0 "Sigma Deza" (conquista de la Argentina)
- Balance largo: el bot cubre ~4 h (NOA y parte del NEA); falta revisar con
  corridas de varios días de juego (Cuyo en adelante) y el ritmo offline.
- Probar en teléfono real los toques sobre el mapa (provincias chicas: CABA,
  Tucumán) y el aviso de novedades.
- Las firestore.rules y el ranking de amigos siguen usando `lifetime`: con el
  reinicio de la 10.0 todos arrancan de cero (decisión de diseño).
- Ideas: animaciones propias por provincia (aspas del molino en la escena,
  vendimia), eventos regionales (vendimia en Mendoza, zafra en Tucumán).

- Más arquetipos de edificios y animaciones específicas (lavado con espuma animada,
  humo de parrilla animado).
- Música (hoy no hay; el ajuste no se muestra).

## Amigos (0.7)
- Probar en dos teléfonos reales: solicitud, aceptar, mates y ranking.
- Ideas: ver la foto de perfil de los amigos (necesita Cloud Storage), notificaciones
  push de solicitudes, desafíos semanales entre amigos.

## Plataforma
- Play Store: ver docs/PLAY_STORE.md (keystore de subida, publicar reglas y páginas
  legales con la cuenta dueña de coronadosdegloria, IDs de AdMob, formularios).
- Probar en el emulador con GPU (no swiftshader: supera GL_MAX_FRAGMENT_UNIFORM_VECTORS y
  la pantalla queda negra) qué pasa después de aceptar el consentimiento de anuncios.
- Foto y banner en la nube (el progreso ya se guarda en Firestore desde la 0.6; ver CUENTAS.md).
- IDs reales de AdMob y consentimiento UMP (MONETIZACION.md). Compras.
- Probar anuncios de prueba y el selector de la galería en un teléfono físico.

## Conocido
- El reloj del teléfono manda: recompensa diaria, mates por día y ganancias offline
  (tope 8 h) se pueden adelantar cambiando la hora. Sin servidor que simule la partida
  no hay forma segura de evitarlo; el ranking de amigos es de confianza.
- `scripts/core/game_model.gd` (~1180 líneas): conviene partirlo antes de los negocios 13–25.
- Las capturas automáticas (`tools/screenshots.sh`) abren una ventana; el gestor de
  ventanas a veces la agranda (la herramienta fuerza el tamaño).
- Los eventos no aparecen durante el tiempo offline (sólo corre su duración), por diseño.
