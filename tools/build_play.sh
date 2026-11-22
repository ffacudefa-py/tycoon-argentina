#!/usr/bin/env bash
# Arma el AAB para Google Play (preset "Android Play Store") SIN AdMob:
# mientras no haya cuenta de AdMob propia, la versión de Play sale sin anuncios
# y sin el SDK (así no lleva el permiso AD_ID ni IDs de prueba).
#
# Uso: KEYSTORE=/ruta/coronados-upload.jks KEYSTORE_PASS='…' GODOT=/ruta/godot tools/build_play.sh
# La clave de subida NO va en el repo (ver docs/PLAY_STORE.md).
set -euo pipefail
cd "$(dirname "$0")/.."

: "${KEYSTORE:?falta KEYSTORE (ruta al .jks de subida)}"
: "${KEYSTORE_PASS:?falta KEYSTORE_PASS}"
GODOT="${GODOT:-godot}"
VERSION=$(sed -n 's/^config\/version="\(.*\)"/\1/p' project.godot)
OUT="build/CoronadosDeGloria-${VERSION}.aab"

# El plugin de AdMob lee admob/general/android/enabled al exportar; override.cfg
# no se aplica en la exportación, así que se agrega a project.godot y se restaura.
mkdir -p build
cp project.godot build/project.godot.bak
trap 'cp build/project.godot.bak project.godot' EXIT
printf '\n[admob]\n\ngeneral/android/enabled=false\n' >> project.godot

rm -f "$OUT"
GODOT_ANDROID_KEYSTORE_RELEASE_PATH="$KEYSTORE" \
GODOT_ANDROID_KEYSTORE_RELEASE_USER="${KEYSTORE_ALIAS:-coronados-upload}" \
GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD="$KEYSTORE_PASS" \
"$GODOT" --headless --path . --export-release "Android Play Store" "$OUT" || true
# (Godot a veces queda colgado después de escribir el AAB por el daemon de Gradle:
# si pasa, cerrarlo a mano; lo que importa es que el archivo exista y pase el control.)
[ -f "$OUT" ] || { echo "ERROR: no se generó $OUT (ver la salida de Godot)"; exit 1; }

python - "$OUT" <<'EOF'
import sys, zipfile
z = zipfile.ZipFile(sys.argv[1])
m = z.read("base/manifest/AndroidManifest.xml")
dex = b"".join(z.read(n) for n in z.namelist() if n.endswith(".dex"))
bad = [s for s in (b"AD_ID", b"gms.ads") if s in m] + ([b"MobileAds"] if b"com/google/android/gms/ads/MobileAds" in dex else [])
sys.exit("ERROR: el AAB tiene AdMob: %s" % bad if bad else 0)
EOF
echo "OK: $OUT (sin AdMob)"
