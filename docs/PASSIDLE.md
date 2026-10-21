# Qué se aprovechó de PassIdle

Se inspeccionó el código real de `~/Descargas/PASSIDLE_SIGMA (3)/passidle` (Flutter/Dart)
y las notas de su desarrollo. No se copió código (otro motor y otro juego); se
trasladaron soluciones conceptuales:

| En PassIdle | En Tycoon Argentina |
|---|---|
| `RootShell` con `IndexedStack`: las pestañas no se reconstruyen y no pierden scroll ni animaciones | `Main` crea las 5 secciones una vez y alterna `visible` |
| `LocalGameRepository.saveCharacters` reemplazaba el mapa entero y borraba personajes no equipados (bug real de pérdida de progreso) | Se guarda siempre el estado completo y validado; nunca se escribe un archivo incompleto encima de uno bueno |
| `GameRepository.commit` con diario de escritura (journal) para cortes a mitad de guardado | Escritura atómica tmp → verificación → .bak → reemplazo, con checksum |
| `IdleMath`: progreso idle calculado al volver con `lastActiveAt`, tope de horas, reloj atrás = nada | `OfflineCalculator` + `max_seen` para que tampoco se pueda cobrar dos veces adelantando el reloj |
| Avisos (`AppToast/ToastHost`) montados por encima del navegador | `ToastHost` en una capa superior que no bloquea toques |
| `ui_kit.dart` como kit compartido | `U` + `ThemeBuilder`: un solo estilo para toda la UI |
| `MenuGuide`: tutorial la primera vez | `TutorialOverlay` que avanza cuando el jugador hace la acción |
| Overflow de 3 px a 360 dp en Colección | Se prueba siempre a 360 px de ancho con capturas reales (`tools/screenshots.sh`) |
| Preferencia del usuario: sin música, sólo efectos | Sólo efectos de sonido; el ajuste de música no se muestra |
| Gotchas de Android (JDK 25 incompatible, plantillas, disco lleno) | JDK 21 del sistema; plantillas Android bajadas por HTTP range (el disco tenía ~2 GB libres) |

No se reutilizó: Firebase, NFC, batallas ni dependencias de Flutter.
