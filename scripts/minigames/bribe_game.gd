class_name BribeGame
extends RefCounted
## Lógica del minijuego "La coima" (sin interfaz: la dibuja BribeView).
##
## Una pila de documentos: el de arriba se da vuelta (reveal) y hay que
## deslizarlo antes de que se acabe su tiempo. ROJO → izquierda (trituradora),
## BLANCO → derecha (carpeta del policía). Un error o una demora = multa.
## Para confundir: papeles blancos con sello rojo y papeles rojos con etiqueta
## blanca (manda el color del PAPEL), y el tiempo por documento se achica.

const REVEAL := 0.16

var diff := 0.3
var rng := RandomNumberGenerator.new()
var docs: Array = []        ## {red, decoy, rot, kind}
var idx := 0
var time_left := 0.0
var reveal_t := REVEAL
var state := "play"         ## play / won / lost
var fail_reason := ""       ## timeout / wrong
var streak := 0
var t := 0.0
var events: Array = []      ## pendientes: la vista los toma con take_events()


func _init(seed_value: int, difficulty: float) -> void:
	rng.seed = seed_value
	diff = clampf(difficulty, 0.0, 1.0)
	var n := doc_count()
	var run_color := false
	var run_len := 0
	for i in n:
		var red := rng.randf() < 0.47
		# Como mucho 3 del mismo color seguidos.
		if run_len >= 3 and red == run_color:
			red = not red
		if red == run_color:
			run_len += 1
		else:
			run_color = red
			run_len = 1
		var decoy := rng.randf() < lerpf(0.15, 0.45, diff) and i > 1
		docs.append({"red": red, "decoy": decoy, "rot": rng.randf_range(-0.22, 0.22) * (0.4 + diff), "kind": rng.randi_range(0, 5)})
	time_left = limit_for(0)


func doc_count() -> int:
	return 12 + int(round(diff * 6.0))


## Segundos para el documento i: arranca holgado y se achica hacia el final.
func limit_for(i: int) -> float:
	var k := float(i) / maxf(1.0, float(doc_count() - 1))
	return lerpf(lerpf(1.7, 1.35, diff), lerpf(1.0, 0.7, diff), k)


func current() -> Dictionary:
	return docs[idx] if idx < docs.size() else {}


func progress() -> float:
	return float(idx) / float(docs.size())


## dir < 0: izquierda (desechar). dir > 0: derecha (entregar).
func swipe(dir: int) -> bool:
	if state != "play" or dir == 0:
		return false
	var d := current()
	var ok: bool = (dir < 0) == bool(d["red"])
	if not ok:
		state = "lost"
		fail_reason = "wrong"
		events.append({"type": "wrong", "dir": dir})
		return false
	streak += 1
	idx += 1
	events.append({"type": "ok", "dir": dir, "red": d["red"], "streak": streak})
	if idx >= docs.size():
		state = "won"
		events.append({"type": "won"})
	else:
		time_left = limit_for(idx)
		reveal_t = REVEAL
	return true


func step(dt: float) -> void:
	if state != "play":
		return
	t += dt
	if reveal_t > 0.0:
		reveal_t -= dt
		return
	time_left -= dt
	if time_left <= 0.0:
		time_left = 0.0
		state = "lost"
		fail_reason = "timeout"
		events.append({"type": "timeout"})


## Fracción de tiempo que queda para el documento actual (0..1).
func urgency() -> float:
	return clampf(time_left / limit_for(idx), 0.0, 1.0) if state == "play" else 0.0


## Devuelve y vacía los eventos pendientes (efectos y sonidos de la vista).
func take_events() -> Array:
	var e := events
	events = []
	return e
