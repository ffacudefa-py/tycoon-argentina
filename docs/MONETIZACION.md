# Monetización (preparada, NO integrada)

Estado actual: **no hay SDK de anuncios ni de compras**. `Monetization` usa
`NotConfiguredAdProvider` y `NotConfiguredPurchaseProvider`, que informan "no
disponible" y nunca entregan recompensas. En Perfil → "Tienda y bonos" se muestra
"En desarrollo" sin botones falsos. Todo el juego se puede completar sin pagar.

## Para habilitar anuncios recompensados

1. Agregar un plugin Android de un proveedor (p. ej. AdMob para Godot 4) y activar
   "Use Gradle Build" en el preset de exportación (requiere la plantilla
   `android_source.zip`, que no se descargó por falta de espacio).
2. Implementar `class_name MiAdProvider extends AdProvider`: `is_available()`,
   `provider_name()` y `show_rewarded(placement, done)` llamando `done.call(true)`
   **sólo** en el callback de recompensa confirmada del SDK.
3. En `Monetization._ready()`: `ads = MiAdProvider.new()`.
4. Las ofertas están en `Monetization.REWARDED_PLACEMENTS` (turbo x2 10 min, caja extra).
   La UI de Perfil muestra los botones automáticamente cuando `rewarded_available()`.

## Para compras opcionales

Implementar `PurchaseProvider` con Google Play Billing (plugin oficial de Godot),
verificar las compras y entregar sólo cosméticos o comodidad (`Monetization.PRODUCTS`).
Sin cajas aleatorias pagas. Si se agrega "quitar anuncios", primero hay que tener
anuncios intersticiales (hoy no existen).

Política: el jugador inicia cada anuncio; no hay anuncios por tocar botones; no se
bloquean negocios detrás de pagos.
