#!/usr/bin/env bash
# Capturas automáticas de la UI real (abre una ventana unos segundos).
# Uso: tools/screenshots.sh [ancho] [alto] [carpeta]
cd "$(dirname "$0")/.."
W="${1:-360}"; H="${2:-740}"; OUTDIR="${3:-$PWD/build/shots_${W}x${H}}"
mkdir -p "$OUTDIR"
"${GODOT:-godot}" --path . --resolution "${W}x${H}" --position 0,0 -- --shots="$OUTDIR" --dev-save=user://devshots_save.json 2>&1 | grep -E "captura|ERROR|SCRIPT" | head -60
echo "Capturas en $OUTDIR"
