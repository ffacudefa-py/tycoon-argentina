#!/usr/bin/env bash
# Arma el AAB para Google Play (preset "Android Play Store") con anuncios de AdMob
# reales (cuenta de Juan José Defagot; IDs en data/ads.json y project.godot).
# Controla que el AAB lleve el App ID de producción y ningún ID de prueba.
# SIN_ANUNCIOS=1 arma la versión sin el SDK de AdMob (sin AD_ID).
#
# Uso: KEYSTORE=/ruta/coronados-upload.jks KEYSTORE_PASS='…' GODOT=/ruta/godot tools/build_play.sh
# La clave de subida NO va en el repo (ver docs/PLAY_STORE.md).
set -euo pipefail
cd "$(dirname "$0")/.."

: "${KEYSTORE:?falta KEYSTORE (ruta al .jks de subida)}"
: "${KEYSTORE_PASS:?falta KEYSTORE_PASS}"
GODOT="${GODOT:-godot}"
SIN_ANUNCIOS="${SIN_ANUNCIOS:-0}"
VERSION=$(sed -n 's/^config\/version="\(.*\)"/\1/p' project.godot)
OUT="build/CoronadosDeGloria-${VERSION}.aab"
mkdir -p build

if [ "$SIN_ANUNCIOS" = 1 ]; then
  # El plugin lee admob/general/android/enabled al exportar (override.cfg no se
  # aplica en la exportación): se agrega a la sección [admob] y se restaura.
  cp project.godot build/project.godot.bak
  trap 'cp build/project.godot.bak project.godot' EXIT
  python - <<'EOF'
p = "project.godot"
s = open(p, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in s else "\n"
s = s.replace("[admob]" + nl, "[admob]" + nl + nl + "general/android/enabled=false" + nl, 1) if "[admob]" in s \
    else s + nl + "[admob]" + nl + nl + "general/android/enabled=false" + nl
open(p, "w", encoding="utf-8", newline="").write(s)
EOF
fi

rm -f "$OUT"
GODOT_ANDROID_KEYSTORE_RELEASE_PATH="$KEYSTORE" \
GODOT_ANDROID_KEYSTORE_RELEASE_USER="${KEYSTORE_ALIAS:-coronados-upload}" \
GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD="$KEYSTORE_PASS" \
"$GODOT" --headless --path . --export-release "Android Play Store" "$OUT" || true
# (Godot a veces queda colgado después de escribir el AAB por el daemon de Gradle:
# si pasa, cerrarlo a mano; lo que importa es que el archivo exista y pase el control.)
[ -f "$OUT" ] || { echo "ERROR: no se generó $OUT (ver la salida de Godot)"; exit 1; }

python - "$OUT" "$SIN_ANUNCIOS" <<'EOF'
import json, re, sys, zipfile
z = zipfile.ZipFile(sys.argv[1])
sin = sys.argv[2] == "1"
m = z.read("base/manifest/AndroidManifest.xml")
dex = b"".join(z.read(n) for n in z.namelist() if n.endswith(".dex"))
test = b"ca-app-pub-3940256099942544"
if sin:
    bad = [s for s in (b"AD_ID", b"gms.ads") if s in m] + ([b"MobileAds"] if b"com/google/android/gms/ads/MobileAds" in dex else [])
    sys.exit("ERROR: el AAB tiene AdMob: %s" % bad if bad else 0)
prod = json.load(open("data/ads.json", encoding="utf-8"))["environments"]["production"]
app = prod["app_id"].encode()
errs = []
if not app or test in app or test in prod["rewarded_unit"].encode():
    errs.append("data/ads.json no tiene IDs de producción reales")
if app not in m:
    errs.append("el manifest no lleva el App ID de producción")
if test in m:
    errs.append("el manifest lleva el App ID de PRUEBA")
if b"com/google/android/gms/ads/MobileAds" not in dex:
    errs.append("falta el SDK de AdMob")
sys.exit("ERROR: " + "; ".join(errs) if errs else 0)
EOF
echo "OK: $OUT ($([ "$SIN_ANUNCIOS" = 1 ] && echo 'sin anuncios' || echo 'con anuncios de AdMob'))"
