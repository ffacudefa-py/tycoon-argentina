class_name TheftGame
extends RefCounted
## Lógica del minijuego "¡Asalto!" (sin interfaz: la dibuja TheftView).
##
## Coordenadas en píxeles de un campo de w × h. Arriba (shelf_y) está la
## mercadería en la estantería; abajo a la izquierda (bag) la bolsa que sostiene
## la mano izquierda; la pistola va abajo a la derecha. Los ladrones entran por
## los costados a rachas muy rápidas con pausas cortas (el momento justo para
## dispararles), agarran una caja y huyen por el costado más cercano.
##  - tap(pos): disparo. Un ladrón con casco aguanta dos tiros. Si cae con una
##    caja, la caja queda en el piso: hay que arrastrarla a la bolsa antes de
##    que otro ladrón la levante o se la lleve un cómplice (floor_life).
##  - Pistola de AMMO balas: con el cargador vacío hay que recargar (reload()).
##  - Pasan clientes: dispararles deja la pistola trabada un rato.
## Resultado: recovered() = cajas en la bolsa ÷ cajas que salieron del estante.
## events guarda lo que pasó en el último paso para efectos y sonidos.

const DURATION := 24.0
const AMMO := 6
const RELOAD_TIME := 0.6
const HIT_RADIUS := 44.0
const GRAB_RADIUS := 44.0
## Los ladrones van a x3: pos son los pies; el cuerpo está BODY_OFFSET más arriba
## y la caja robada viaja CARRY_OFFSET arriba de los pies (sobre la cabeza).
const BODY_OFFSET := 62.0
const CARRY_OFFSET := -128.0
const REACH := 72.0
const CIVILIAN_STUN := 1.2
const GRAB_TIME := 0.35

var w := 360.0
var h := 560.0
var diff := 0.3
var rng := RandomNumberGenerator.new()

var thieves: Array = []     ## {id, pos, vel, state, hp, helmet, carry, target, dash_t, pause_t, dir, weave, spawn_at, side, flash}
var loot: Array = []        ## {id, pos, home, state, floor_t, product}
var civilians: Array = []   ## {pos, vel, spawn_at, state, kind}
var events: Array = []      ## [{type, pos, ...}] pendientes: la vista los toma con take_events()

var t := 0.0
var ammo := AMMO
var reload_t := 0.0
var stun_t := 0.0
var combo := 0
var best_combo := 0
var shots := 0
var hits := 0
var civilian_hits := 0
var finished := false
var bag := Rect2()
var shelf_y := 0.0
var floor_top := 0.0
var floor_bottom := 0.0
var products := 4


func _init(seed_value: int, difficulty: float, width := 360.0, height := 560.0, product_count := 4) -> void:
	rng.seed = seed_value
	diff = clampf(difficulty, 0.0, 1.0)
	w = width
	h = height
	products = maxi(1, product_count)
	shelf_y = h * 0.27
	floor_top = shelf_y + REACH + 20.0
	floor_bottom = h - 140.0
	bag = bag_rect(h)
	var n := thief_count()
	# Cajas en la estantería: una por ladrón y un par de más.
	var crates := n + 2
	for i in crates:
		var x := lerpf(w * 0.12, w * 0.88, (float(i) + 0.5) / float(crates))
		loot.append({"id": i, "pos": Vector2(x, shelf_y), "home": Vector2(x, shelf_y), "state": "shelf",
			"floor_t": 0.0, "product": i % products})
	var spread := lerpf(6.5, 5.0, diff)
	for i in n:
		var side := -1 if rng.randf() < 0.5 else 1
		var hp := 2 if rng.randf() < diff * 0.55 else 1
		thieves.append({"id": i, "pos": Vector2(-30.0 if side < 0 else w + 30.0, rng.randf_range(floor_top, floor_bottom)),
			"state": "wait", "hp": hp, "helmet": hp > 1, "carry": -1, "target": -1,
			"dash_t": 0.0, "pause_t": 0.0, "dir": Vector2.ZERO, "vel": Vector2.ZERO, "bias": 0.0, "bias_to": 0.0,
			"weave": rng.randf() * TAU, "weave_f": rng.randf_range(5.0, 8.0),
			"spawn_at": 0.8 + spread * float(i) / maxf(1.0, float(n - 1)) + rng.randf_range(-0.4, 0.4),
			"side": side, "flash": 0.0, "exit_y": 0.0})
	var nciv := 0 if diff < 0.25 else (1 if diff < 0.55 else 2) + rng.randi_range(0, 1)
	for i in nciv:
		var left := rng.randf() < 0.5
		civilians.append({"pos": Vector2(-24.0 if left else w + 24.0, rng.randf_range(floor_top + 20.0, floor_bottom)),
			"vel": Vector2((1.0 if left else -1.0) * w * rng.randf_range(0.22, 0.32), 0.0),
			"spawn_at": rng.randf_range(2.0, DURATION - 8.0), "state": "wait", "kind": rng.randi_range(0, 3)})


func thief_count() -> int:
	return 4 + int(round(diff * 4.0))


func dash_speed() -> float:
	return w * lerpf(1.2, 1.85, diff)


func floor_life() -> float:
	return lerpf(5.5, 3.8, diff)


func time_left() -> float:
	return maxf(0.0, DURATION - t)


# ------------------------------------------------------------------ jugador

## Disparo en pos. Devuelve el tipo: "hit", "armor", "miss", "civilian",
## "empty" (sin balas), "reloading", "stunned" u "over".
func tap(pos: Vector2) -> String:
	if finished:
		return "over"
	if stun_t > 0.0:
		_event("stunned", pos)
		return "stunned"
	if reload_t > 0.0:
		return "reloading"
	if ammo <= 0:
		_event("empty", pos)
		return "empty"
	ammo -= 1
	shots += 1
	var best := -1
	var best_d := HIT_RADIUS
	for i in thieves.size():
		var th: Dictionary = thieves[i]
		if not _active(th):
			continue
		var d := ((th["pos"] as Vector2) - Vector2(0, BODY_OFFSET)).distance_to(pos)
		if d < best_d:
			best_d = d
			best = i
	if best >= 0:
		var th: Dictionary = thieves[best]
		th["hp"] = int(th["hp"]) - 1
		hits += 1
		combo += 1
		best_combo = maxi(best_combo, combo)
		if int(th["hp"]) > 0:
			th["helmet"] = false
			th["pause_t"] = 0.45
			th["dash_t"] = 0.0
			th["flash"] = 0.2
			# Trastabilla: el tiro lo empuja hacia atrás (se frena con la aceleración).
			th["vel"] = (th["vel"] as Vector2) * -0.4 + Vector2(0, -dash_speed() * 0.15)
			_event("armor", th["pos"], {"thief": best})
			return "armor"
		th["state"] = "down"
		th["flash"] = 0.25
		if int(th["carry"]) >= 0:
			var l: Dictionary = loot[int(th["carry"])]
			l["state"] = "floor"
			l["floor_t"] = 0.0
			l["pos"] = (th["pos"] as Vector2) + Vector2(rng.randf_range(-10, 10), 6)
			th["carry"] = -1
			_event("drop", l["pos"], {"loot": l["id"]})
		_event("hit", th["pos"], {"thief": best, "combo": combo})
		return "hit"
	for c in civilians:
		if c["state"] == "walk" and ((c["pos"] as Vector2) - Vector2(0, BODY_OFFSET)).distance_to(pos) < HIT_RADIUS:
			c["state"] = "scared"
			civilian_hits += 1
			combo = 0
			stun_t = CIVILIAN_STUN
			_event("civilian", c["pos"])
			return "civilian"
	combo = 0
	_event("miss", pos)
	return "miss"


func reload() -> bool:
	if finished or reload_t > 0.0 or ammo >= AMMO:
		return false
	reload_t = RELOAD_TIME
	_event("reload", Vector2.ZERO)
	return true


## Empieza a arrastrar la caja del piso más cercana a pos (-1 si no hay).
func drag_start(pos: Vector2) -> int:
	if finished:
		return -1
	var best := -1
	var best_d := GRAB_RADIUS
	for l in loot:
		if l["state"] != "floor":
			continue
		var d := (l["pos"] as Vector2).distance_to(pos)
		if d < best_d:
			best_d = d
			best = int(l["id"])
	if best >= 0:
		loot[best]["state"] = "drag"
		_event("pick", loot[best]["pos"], {"loot": best})
	return best


func drag_move(id: int, pos: Vector2) -> void:
	if id >= 0 and id < loot.size() and loot[id]["state"] == "drag":
		loot[id]["pos"] = Vector2(clampf(pos.x, 0.0, w), clampf(pos.y, 0.0, h))


## Suelta la caja: en la bolsa (con un margen que "atrae") queda guardada.
func drag_end(id: int, pos: Vector2) -> bool:
	if id < 0 or id >= loot.size() or loot[id]["state"] != "drag":
		return false
	var l: Dictionary = loot[id]
	pos = Vector2(clampf(pos.x, 24.0, w - 24.0), clampf(pos.y, floor_top, h - 24.0))
	l["pos"] = pos
	if bag.grow(22.0).has_point(pos):
		l["state"] = "bagged"
		l["pos"] = bag.get_center()
		_event("bagged", bag.get_center(), {"loot": id})
		return true
	l["state"] = "floor"
	return false


# --------------------------------------------------------------- simulación

func step(dt: float) -> void:
	if finished:
		return
	t += dt
	stun_t = maxf(0.0, stun_t - dt)
	if reload_t > 0.0:
		reload_t -= dt
		if reload_t <= 0.0:
			reload_t = 0.0
			ammo = AMMO
			_event("reloaded", Vector2.ZERO)
	for th in thieves:
		th["flash"] = maxf(0.0, float(th["flash"]) - dt)
		_step_thief(th, dt)
	for c in civilians:
		_step_civilian(c, dt)
	for l in loot:
		if l["state"] == "floor":
			l["floor_t"] = float(l["floor_t"]) + dt
			if float(l["floor_t"]) >= floor_life():
				l["state"] = "lost"
				_event("snatched", l["pos"], {"loot": l["id"]})
	if t >= DURATION or _all_done():
		_finish()


func _active(th: Dictionary) -> bool:
	return th["state"] in ["enter", "grab", "flee"]


func _all_done() -> bool:
	for th in thieves:
		if th["state"] in ["wait", "enter", "grab", "flee"]:
			return false
	for l in loot:
		if l["state"] in ["floor", "drag", "carried"]:
			return false
	return true


func _finish() -> void:
	finished = true
	for l in loot:
		if l["state"] in ["floor", "drag", "carried"]:
			l["state"] = "lost"
	_event("end", Vector2.ZERO, {"recovered": recovered()})


func _step_thief(th: Dictionary, dt: float) -> void:
	match th["state"]:
		"wait":
			if t >= float(th["spawn_at"]):
				th["state"] = "enter"
				th["target"] = _pick_target(th)
				_event("enter", th["pos"], {"thief": th["id"]})
		"enter":
			if int(th["target"]) < 0 or not (loot[int(th["target"])]["state"] in ["shelf", "floor"]):
				th["target"] = _pick_target(th)
				if int(th["target"]) < 0:
					th["state"] = "flee"
					return
			var goal: Vector2 = loot[int(th["target"])]["pos"]
			if _move(th, goal + Vector2(0, REACH), dt):
				th["state"] = "grab"
				th["pause_t"] = GRAB_TIME
		"grab":
			th["pause_t"] = float(th["pause_t"]) - dt
			if float(th["pause_t"]) <= 0.0:
				var l: Dictionary = loot[int(th["target"])]
				if l["state"] in ["shelf", "floor"]:
					l["state"] = "carried"
					th["carry"] = l["id"]
					_event("grab", th["pos"], {"thief": th["id"], "loot": l["id"]})
					th["state"] = "flee"
					th["side"] = -1 if (th["pos"] as Vector2).x < w * 0.5 else 1
					# Huye en diagonal hacia abajo: cruza el local y da tiempo a reaccionar.
					th["exit_y"] = rng.randf_range(lerpf(floor_top, floor_bottom, 0.45), floor_bottom)
				else:
					th["state"] = "enter"
		"flee":
			var ey := float(th["exit_y"]) if float(th["exit_y"]) > 0.0 else clampf((th["pos"] as Vector2).y, floor_top, floor_bottom)
			var exit := Vector2(-50.0 if int(th["side"]) < 0 else w + 50.0, ey)
			# Un ladrón con las manos vacías levanta una caja del piso al pasar.
			if int(th["carry"]) < 0:
				for l in loot:
					if l["state"] == "floor" and (l["pos"] as Vector2).distance_to(th["pos"]) < 40.0:
						l["state"] = "carried"
						th["carry"] = l["id"]
						_event("grab", th["pos"], {"thief": th["id"], "loot": l["id"]})
						break
			if _move(th, exit, dt):
				th["state"] = "gone"
				if int(th["carry"]) >= 0:
					loot[int(th["carry"])]["state"] = "lost"
					_event("escaped", th["pos"], {"thief": th["id"], "loot": th["carry"]})
				th["carry"] = -1
	if int(th["carry"]) >= 0:
		loot[int(th["carry"])]["pos"] = (th["pos"] as Vector2) + Vector2(0, CARRY_OFFSET)


## 12.1: movimiento con inercia (antes cambiaba de rumbo y de velocidad de golpe y
## se veía robótico). Mantiene el ritmo de rachas y pausas cortas (el momento de
## disparar), pero con un "steering" simple: la velocidad se acerca a la deseada
## con aceleración limitada, el rumbo serpentea con una onda suave más un desvío
## por racha que cambia de a poco, en las pausas casi se detiene (mira, duda) y
## frena al llegar. dir = hacia dónde mira. Devuelve true al llegar.
func _move(th: Dictionary, goal: Vector2, dt: float) -> bool:
	var pos: Vector2 = th["pos"]
	var vel: Vector2 = th["vel"]
	var to_goal := goal - pos
	var dist := to_goal.length()
	if dist < 8.0:
		th["vel"] = vel * 0.5
		return true
	var top := dash_speed()
	var want := top
	if float(th["pause_t"]) > 0.0:
		th["pause_t"] = float(th["pause_t"]) - dt
		want = top * 0.03                        # duda: se planta (casi quieto), el momento de disparar
	else:
		if float(th["dash_t"]) <= 0.0:
			th["dash_t"] = rng.randf_range(0.22, 0.4)
			th["bias_to"] = rng.randf_range(-0.75, 0.75)
		th["dash_t"] = float(th["dash_t"]) - dt
		if float(th["dash_t"]) <= 0.0:
			th["pause_t"] = rng.randf_range(lerpf(0.16, 0.07, diff), lerpf(0.42, 0.22, diff))
	# Rumbo: hacia la meta + desvío de la racha (suavizado) + serpenteo.
	th["bias"] = lerpf(float(th["bias"]), float(th["bias_to"]), minf(1.0, dt * 7.0))
	th["weave"] = float(th["weave"]) + dt * float(th["weave_f"])
	var fwd := to_goal / dist
	var lat := Vector2(-fwd.y, fwd.x)
	var near := clampf((dist - 30.0) / 90.0, 0.0, 1.0)     # cerca de la meta va derecho
	var heading := (fwd + lat * (float(th["bias"]) + sin(float(th["weave"])) * 0.3) * near).normalized()
	want *= clampf(dist / 60.0, 0.25, 1.0)                    # llegada: frena
	var accel := top * (9.0 if want > vel.length() else 16.0)   # arranca en ~0,1 s, frena en ~0,06 s
	vel = vel.move_toward(heading * want, accel * dt)
	pos += vel * dt
	pos.y = clampf(pos.y, shelf_y + REACH - 4.0, floor_bottom)
	th["pos"] = pos
	th["vel"] = vel
	if vel.length() > top * 0.05:
		th["dir"] = vel.normalized()
	return pos.distance_to(goal) < 8.0


func _pick_target(th: Dictionary) -> int:
	var best := -1
	var best_d := INF
	var taken := {}
	for o in thieves:
		if o != th and _active(o) and int(o["target"]) >= 0 and int(o["carry"]) < 0:
			taken[int(o["target"])] = true
	for l in loot:
		if not (l["state"] in ["shelf", "floor"]) or taken.has(int(l["id"])):
			continue
		var d := (l["pos"] as Vector2).distance_to(th["pos"]) + rng.randf_range(0.0, 60.0)
		if d < best_d:
			best_d = d
			best = int(l["id"])
	return best


func _step_civilian(c: Dictionary, dt: float) -> void:
	match c["state"]:
		"wait":
			if t >= float(c["spawn_at"]):
				c["state"] = "walk"
		"walk", "scared":
			var v: Vector2 = (c["vel"] as Vector2) * (2.2 if c["state"] == "scared" else 1.0)
			c["pos"] = (c["pos"] as Vector2) + v * dt
			var x: float = (c["pos"] as Vector2).x
			if x < -40.0 or x > w + 40.0:
				c["state"] = "gone"


func _event(type: String, pos: Vector2, extra := {}) -> void:
	var e := {"type": type, "pos": pos}
	e.merge(extra)
	events.append(e)


# ---------------------------------------------------------------- resultado

func taken_count() -> int:
	var n := 0
	for l in loot:
		if l["state"] != "shelf":
			n += 1
	return n


func bagged_count() -> int:
	var n := 0
	for l in loot:
		if l["state"] == "bagged":
			n += 1
	return n


func lost_count() -> int:
	var n := 0
	for l in loot:
		if l["state"] == "lost":
			n += 1
	return n


## Parte recuperada de lo que salió del estante (1 si no se llevaron nada).
func recovered() -> float:
	var taken := taken_count()
	return 1.0 if taken == 0 else float(bagged_count()) / float(taken)


## Parte de la mercadería que se salvó (todo el estante cuenta): es lo que se
## usa para la pérdida, así frenar a casi toda la banda también sirve.
func saved() -> float:
	return 1.0 - float(lost_count()) / float(maxi(1, loot.size()))


## 12.1: la bolsa la sostiene la mano izquierda en la esquina inferior izquierda
## (la boca y el cuerpo de la bolsa, como se dibuja en TheftView).
static func bag_rect(height: float) -> Rect2:
	return Rect2(16.0, height - 180.0, 150.0, 176.0)


## La pantalla cambió de tamaño en pleno juego: todo se reescala.
func rescale(nw: float, nh: float) -> void:
	if nw <= 0.0 or nh <= 0.0 or (is_equal_approx(nw, w) and is_equal_approx(nh, h)):
		return
	var k := Vector2(nw / w, nh / h)
	for th in thieves:
		th["pos"] = (th["pos"] as Vector2) * k
		th["exit_y"] = float(th["exit_y"]) * k.y
	for l in loot:
		l["pos"] = (l["pos"] as Vector2) * k
		l["home"] = (l["home"] as Vector2) * k
	for c in civilians:
		c["pos"] = (c["pos"] as Vector2) * k
		c["vel"] = (c["vel"] as Vector2) * k.x
	w = nw
	h = nh
	shelf_y = h * 0.27
	floor_top = shelf_y + REACH + 20.0
	floor_bottom = h - 140.0
	bag = bag_rect(h)


func escaped_count() -> int:
	var n := 0
	for th in thieves:
		if th["state"] == "gone":
			n += 1
	return n


## Sin pérdidas y sin ningún ladrón escapado.
func perfect() -> bool:
	return finished and lost_count() == 0 and escaped_count() == 0


## Devuelve y vacía los eventos pendientes (efectos y sonidos de la vista).
func take_events() -> Array:
	var e := events
	events = []
	return e
