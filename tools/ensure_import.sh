#!/usr/bin/env bash
# Reimporta si .godot/ (fuera de git) quedó viejo: después de un clon o de un
# pull que trae scripts con class_name nuevos, Godot no los encuentra
# ("Identifier X not declared") hasta regenerar la caché de clases.
cd "$(dirname "$0")/.."
GODOT="${GODOT:-godot}"
CACHE=.godot/global_script_class_cache.cfg
stale=0
if [ ! -f "$CACHE" ]; then
  stale=1
else
  while IFS= read -r f; do
    name=$(sed -n 's/^class_name[[:space:]]\+\([A-Za-z0-9_]\+\).*/\1/p' "$f" | head -1)
    if ! grep -q "&\"$name\"" "$CACHE"; then stale=1; break; fi
  done < <(grep -rl --include='*.gd' '^class_name' scripts tests tools 2>/dev/null)
fi
if [ $stale -eq 1 ]; then
  echo "Reimportando el proyecto (caché de clases desactualizada)…"
  "$GODOT" --headless --path . --import >/dev/null 2>&1
fi
exit 0
