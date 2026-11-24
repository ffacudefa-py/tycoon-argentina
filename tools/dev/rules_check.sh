#!/usr/bin/env bash
# Prueba firestore.rules en los emuladores con tools/dev/social_check.gd.
# Corre con el interruptor compat151() en false (como va a quedar desde la 15.2)
# y lo restaura al terminar, así se prueba también el tope de solicitudes.
# Variables: GODOT, FIREBASE (cli), y Java/Node en el PATH (ver docs/AMIGOS.md).
set -euo pipefail
cd "$(dirname "$0")/../.."
GODOT="${GODOT:-godot}"
FIREBASE="${FIREBASE:-firebase}"
cp firestore.rules build/firestore.rules.bak 2>/dev/null || { mkdir -p build; cp firestore.rules build/firestore.rules.bak; }
trap 'cp build/firestore.rules.bak firestore.rules' EXIT
python - <<'PY'
p = "firestore.rules"
s = open(p, encoding="utf-8", newline="").read()
old = "function compat151() {\n      return true;"
assert old in s, "no encuentro compat151()"
open(p, "w", encoding="utf-8", newline="").write(s.replace(old, "function compat151() {\n      return false;"))
PY
TYCOON_EMULATOR=127.0.0.1 "$FIREBASE" emulators:exec --only auth,firestore --project coronadosdegloria \
  "$GODOT --headless --path . -s res://tools/dev/social_check.gd -- --dev-save=user://social_check_save.json"
