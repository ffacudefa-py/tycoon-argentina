#!/usr/bin/env bash
# Compila el plugin a bin/coronados-notif.aar con javac (sin Gradle).
# Necesita ~/Android/Sdk (android.jar) y la plantilla android/build de Godot (godot-lib).
set -euo pipefail
cd "$(dirname "$0")"
SDK="${ANDROID_HOME:-$HOME/Android/Sdk}"
ANDROID_JAR="$(ls -d "$SDK"/platforms/android-3*/android.jar | sort -V | tail -1)"
GODOT_AAR="../../../android/build/libs/release/godot-lib.template_release.aar"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
unzip -q -o "$GODOT_AAR" classes.jar -d "$TMP/godot"
mkdir -p "$TMP/classes" "$TMP/aar" ../bin
javac -source 8 -target 8 -Xlint:-options -nowarn -bootclasspath "$ANDROID_JAR" -cp "$TMP/godot/classes.jar" \
  -d "$TMP/classes" $(find src -name '*.java')
(cd "$TMP/classes" && jar cf "$TMP/aar/classes.jar" .)
cp AndroidManifest.xml "$TMP/aar/"
: > "$TMP/aar/R.txt"
(cd "$TMP/aar" && zip -q -r "$OLDPWD/../bin/coronados-notif.aar" .)
echo "listo: addons/coronados_notif/bin/coronados-notif.aar"
