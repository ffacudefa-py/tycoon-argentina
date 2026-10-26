#!/usr/bin/env bash
# Corre todas las pruebas headless. Falla si alguna prueba falla o si hubo
# cualquier error de script (Godot no aborta ante errores en tiempo de ejecución).
cd "$(dirname "$0")/.."
GODOT="${GODOT:-godot}"
OUT=$("$GODOT" --headless --path . -s res://tests/run_tests.gd -- "$@" 2>&1)
STATUS=$?
echo "$OUT" | grep -v -E "^\s*$"
if echo "$OUT" | grep -q -E "SCRIPT ERROR|Parse Error|Compile Error"; then
  echo "✗ Hubo errores de script durante las pruebas."
  exit 1
fi
[ $STATUS -ne 0 ] && exit $STATUS
# Prueba de humo de la interfaz: abre todas las secciones y modales sin ventana.
if [ -z "$1" ]; then
  UI=$("$GODOT" --headless --path . -- --shots=/tmp/tycoon_smoke --dev-save=user://smoke_save.json 2>&1)
  N=$(echo "$UI" | grep -c "visitado:")
  for T in ENTRAR_JUEGO TOQUE_ABRIR TOQUE_VENDER FOTO_GUARDADA SALDO_NEGATIVO MISION_RECLAMABLE RECLAMAR_TODO RECLAMAR_TODO_COBRO; do if ! echo "$UI" | grep -q "$T OK"; then echo "✗ Falló el toque real: $T"; exit 1; fi; done
  if echo "$UI" | grep -q -E "SCRIPT ERROR|Parse Error"; then
    echo "$UI" | grep -A3 "SCRIPT ERROR" | head -30
    echo "✗ Prueba de humo de UI: errores de script ($N pantallas visitadas)."
    exit 1
  fi
  echo "✓ Prueba de humo de UI: $N pantallas/modales sin errores."
fi
exit 0
