# Monetización

## Anuncios recompensados (integrados con Google AdMob)

**Estado real (v0.5.0):** el código está integrado con el SDK de AdMob a través
del plugin [Poing Godot AdMob 5.1](https://github.com/poingstudios/godot-admob-plugin)
(`addons/admob/`, export con Gradle). El APK beta usa los **anuncios de prueba
oficiales de Google**. No hay cuenta de AdMob propia todavía, así que **no hay
anuncios reales ni ingresos**: en un build de producción sin IDs los anuncios
quedan desactivados y el juego lo dice ("Los anuncios todavía no están
configurados para esta versión").

En escritorio y en el editor no hay SDK: la pantalla de bonos muestra "Los
anuncios sólo están disponibles en la app de Android" (no se simula nada).

### Piezas

| Archivo | Qué hace |
|---|---|
| `data/ads.json` | Configuración central: entornos, IDs, límite diario (12), reintentos y las 4 ofertas |
| `scripts/ads/ad_config.gd` | Elige el entorno y valida (producción nunca acepta IDs de prueba) |
| `scripts/ads/ad_rewards.gd` | Lógica pura de recompensas: token por anuncio, una sola sesión, esperas, límite diario, registro en el guardado |
| `scripts/monetization/monetization.gd` | Autoload: elige proveedor, estado (cargando / listo / error), reintentos crecientes (5 s → 5 min), `watch()` |
| `scripts/monetization/admob_ad_provider.gd` | AdMob: inicializa, carga, muestra, confirma con `on_user_earned_reward`, destruye y precarga el siguiente |
| `scripts/monetization/fake_ad_provider.gd` | Sólo para pruebas automatizadas |
| `scripts/ui/modals/ads_modal.gd` | Pantalla "Bonos por anuncio" (Imperio → BONOS, o Perfil → Tienda y bonos) |

### Ofertas (`data/ads.json → offers`)

| id | Recompensa | Espera |
|---|---|---|
| `cash` | 5 minutos de tus ganancias (mínimo $500) | 5 min |
| `turbo` | Ganancias x2 durante 10 minutos (suma tiempo al turbo activo) | 15 min |
| `restock` | Llena gratis el depósito del negocio que estás viendo | 10 min |
| `daily_extra` | Vuelve a pagar la recompensa diaria de hoy (después de reclamarla) | 1 por día |

Máximo 12 anuncios por día. Los montos se calculan al tocar el botón y se
fijan para ese anuncio.

### Garantías

- La recompensa se entrega **sólo** cuando AdMob llama `on_user_earned_reward`.
  Cerrar antes, error al mostrar o sin internet → no se entrega nada.
- Cada anuncio tiene un token único. Si el SDK avisa dos veces, o llega un aviso
  viejo, se ignora. El token se guarda en `ads.granted` dentro de la partida y la
  partida se guarda en el acto.
- Una sola sesión a la vez: doble toque, tocar otra oferta o cambiar de pantalla
  no abre un segundo anuncio.
- Los anuncios nunca bloquean el progreso ni aparecen sin que el jugador toque.

### Probar con anuncios de prueba

1. Instalar el APK beta (`custom_features="beta"` en el preset → entorno `test`).
2. Imperio → **BONOS**. Con internet, en unos segundos los botones pasan de
   "CARGANDO ANUNCIO…" a "VER ANUNCIO". El modal dice "Modo prueba".
3. Ver el anuncio completo → toast con la recompensa. Cerrarlo antes → "Cerraste
   el anuncio antes de terminarlo: esta vez no hay recompensa".
4. Modo avión → "Sin conexión a internet. Se reintenta solo."; al volver la
   conexión (o volver a la app) se recarga.

### Activar anuncios reales (producción)

1. Crear la app en [AdMob](https://admob.google.com) y una unidad **Recompensado**.
2. En `data/ads.json → environments.production` poner `app_id` y `rewarded_unit`.
3. En Project Settings → `admob/general/android/app_id` poner el **mismo** App ID
   (va al AndroidManifest; hoy tiene el de prueba).
4. En `export_presets.cfg` quitar `beta` de `custom_features` (si no, el APK sigue
   usando anuncios de prueba).
5. Firmar con el keystore de release (`docs/ANDROID.md`) y configurar en AdMob
   `app-ads.txt` y el mensaje GDPR en AdMob → Privacidad y mensajes. El juego ya pide el
   consentimiento con UMP antes de iniciar AdMob (en el entorno de prueba simula la UE) y
   muestra "Privacidad de los anuncios" en Configuración cuando corresponde.
6. Probar en un dispositivo registrado como "dispositivo de prueba" en AdMob antes
   de publicar: tocar anuncios reales propios puede suspender la cuenta.

## Compras opcionales

Sin proveedor (`NotConfiguredPurchaseProvider`). Para integrarlas: Google Play
Billing (plugin oficial de Godot), verificar compras y entregar sólo cosméticos o
comodidad (`Monetization.PRODUCTS`). Sin cajas aleatorias pagas.
