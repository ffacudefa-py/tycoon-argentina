class_name TheftView
extends Control
## 11.2: pantalla del minijuego "¡Asalto!" (la lógica está en TheftGame).
##
## Fases: intro (alarma, cartel, la banda que cruza, instrucciones y 3-2-1),
## juego y resultado. Se dibuja todo en _draw() con las hojas de
## assets/pixel_art/minigames (x2), sin crear nodos por cuadro.
## Sensación: chancleta que vuela girando, sacudón de pantalla, congelado de
## 50 ms al acertar, chispas, estela de los ladrones a la carrera, aro de
## tiempo en las cajas del piso, imán de la bolsa y textos flotantes.
## 12.1: en primera persona. Abajo a la izquierda la otra mano sostiene la bolsa.
## 15.2: la pistola se reemplazó por la chancleta de la abuela (clasificación
## por edades para Play): la mano la revolea hacia el toque y agarra otra; sin
## chancletas, tocar la mano trae más. Los ladrones quedan mareados. Piso de baldosas calcáreas con alfombra, luces de techo,
## viñeta tramada, balizas de alarma y polvo en el aire.

signal finished(saved: float, perfect: bool)    ## al terminar el juego (se aplica en el modelo)
signal dismissed                                ## al tocar SEGUIR (cierra la pantalla)

const INTRO := 3.4
const SPR := 2.0                     ## escala de cajas, bolsa y efectos
const CHAR := 3.0                    ## escala de ladrones y clientes
const GUN := 2.5                     ## escala de la mano con la chancleta (cuadros de 96x96)
const FLY := 0.16                    ## 15.2: segundos que vuela la chancleta
const OUTLINE := Color("3d1b0b")
const GOLD := Color("f2d173")
const CREAM := Color("fff6e6")
const RED := Color("d5576e")
const GREEN := Color("67d08e")

var m: GameModel
var game: TheftGame
var bid := ""
var biz_name := ""
var company := ""
var practice := false                ## práctica (Ajustes): el resultado no se aplica
var seed_value := 1
var diff := 0.3
var fraction := 0.2

var phase := "intro"
var pt := 0.0                        ## tiempo dentro de la fase
var _hitstop := 0.0
var _shake := 0.0
var _recoil := 0.0
var _bag_squash := 0.0
var _dragging := -1
var _drag_off := Vector2.ZERO
var _fx: Array = []                  ## {kind, pos, t, dur, ...}
var _trails := {}                    ## id ladrón -> [Vector2]
var _down_t := {}                    ## id ladrón -> segundos en el piso
var _drop_t := {}                    ## id caja -> segundos desde que cayó
var _throws: Array = []              ## 15.2: chancletas en vuelo {from, to, t, dur, spin}
var _aim := Vector2.ZERO             ## hacia dónde mira la mano (suavizado)
var _aim_target := Vector2.ZERO
var _drag_last := Vector2.ZERO
var _motes: Array = []               ## polvo en el aire {pos, vel, ph}
var _run := {}                       ## id ladrón -> {ph: fase del paso, spd: velocidad suavizada, flip, land}
var _sh := Vector2.ZERO               ## sacudón actual (se suma a todas las transformaciones del mundo)
var _result_btn: Button
var _counted := false
var _dismissed := false
var _room: Texture2D                 ## fondo estático horneado (piso, pared, alfombra)
var _room_size := Vector2.ZERO
var _shadow_tex: Texture2D
var _text_w := {}                    ## "tamaño|texto" -> ancho, para no medir cada cuadro
var _rm := false                     ## ajuste "reducir movimiento": sin sacudón, congelado ni temblores
var _first_time := false             ## primera vez: la explicación espera un toque
var _waiting := false
var _font: Font
var _rng := RandomNumberGenerator.new()

var _tex_thief: Array = []
var _tex_casco: Array = []
var _tex_civ: Array = []
var _tex := {}
var _icons: Array = []


func setup(model: GameModel, pending: Dictionary) -> void:
	m = model
	bid = pending.get("business", m.first_business())
	seed_value = int(pending.get("seed", 1))
	diff = float(pending.get("difficulty", 0.3))
	fraction = float(pending.get("fraction", 0.2))
	biz_name = m.data.business_by_id[bid]["name"]
	company = m.profile["company"]


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	clip_contents = true
	_rng.seed = seed_value
	_font = get_theme_default_font()
	_rm = bool(Settings.get_value("reduce_motion"))
	_shadow_tex = _make_shadow()
	_first_time = not bool(m.hard.get("seen_theft", false))
	for i in 3:
		_tex_thief.append(U.tex("minigames/thief_%d.png" % i))
		_tex_casco.append(U.tex("minigames/thief_casco_%d.png" % i))
	for i in 4:
		_tex_civ.append(U.tex("characters/customer_%d.png" % i))
	for k in ["crate", "siren", "chancla_hand", "chancla", "chancla_icon", "bag_hand", "impact",
			"floor_tiles", "rug", "shelf", "beacon", "plant", "boxes"]:
		_tex[k] = U.tex("minigames/%s.png" % k)
	for i in 14:
		_motes.append({"pos": Vector2(_rng.randf(), _rng.randf()), "vel": Vector2(_rng.randf_range(-6, 6), _rng.randf_range(-4, 2)), "ph": _rng.randf() * TAU})
	var tier := int(m.derive(bid)["tier"]) if m.biz[bid]["owned"] else 0
	# 12.2: la pared sin ventana ni cosas colgadas (no quedan debajo del HUD)
	_tex["back"] = U.tex("interiors/%s_%d_wall.png" % [bid, tier])
	if _tex["back"] == null:
		_tex["back"] = U.tex("interiors/%s_%d_back.png" % [bid, tier])
	for p in m.data.business_by_id[bid]["products"]:
		var t := U.icon32_tex(p["icon"])
		_icons.append(t if t else U.icon_tex(p["icon"]))


func _start_game() -> void:
	m.hard["seen_theft"] = true
	game = TheftGame.new(seed_value, diff, size.x, size.y, maxi(1, _icons.size()))
	phase = "play"
	pt = 0.0
	Sfx.play("event")


# ------------------------------------------------------------------- ciclo

func _process(dt: float) -> void:
	dt = minf(dt, 0.1)          # al volver de segundo plano no se "adelanta" el juego
	pt += dt
	_shake = maxf(0.0, _shake - dt * 30.0)
	_recoil = maxf(0.0, _recoil - dt)
	_bag_squash = maxf(0.0, _bag_squash - dt * 3.0)
	if _aim_target == Vector2.ZERO:
		_aim_target = Vector2(size.x * 0.5, size.y * 0.45)
		_aim = _aim_target
	_aim = _aim.lerp(_aim_target, minf(1.0, dt * 14.0))
	for mo in _motes:
		mo["pos"] = Vector2(fposmod((mo["pos"] as Vector2).x + (mo["vel"] as Vector2).x * dt / maxf(1.0, size.x), 1.0),
			fposmod((mo["pos"] as Vector2).y + (mo["vel"] as Vector2).y * dt / maxf(1.0, size.y), 1.0))
	match phase:
		"intro":
			# La primera vez la explicación espera un toque.
			if _first_time and pt >= INTRO - 1.5 and not _waiting and pt - dt < INTRO - 1.5:
				_waiting = true
			if _waiting:
				pt = INTRO - 1.5
			var beats := [INTRO - 1.4, INTRO - 1.05, INTRO - 0.7]
			for b in beats:
				if pt - dt < b and pt >= b:
					Sfx.play("tick", 1.0 + 0.1 * beats.find(b))
			if pt >= INTRO:
				_start_game()
		"play":
			if game.w != size.x or game.h != size.y:
				game.rescale(size.x, size.y)
				_trails.clear()
			if _hitstop > 0.0:
				_hitstop -= dt
			else:
				game.step(dt)
				_handle(game.take_events())
				_track(dt)
		"result":
			if pt > 20.0:
				_dismiss()
	_age(_fx, dt, -1.0)
	_age(_throws, dt, -1.0)
	queue_redraw()


## Envejece efectos y saca los vencidos sin crear arrays nuevos.
static func _age(list: Array, dt: float, life: float) -> void:
	var i := 0
	while i < list.size():
		var f: Dictionary = list[i]
		f["t"] = float(f["t"]) + dt
		if float(f["t"]) >= (life if life > 0.0 else float(f["dur"])):
			list[i] = list[list.size() - 1]
			list.pop_back()
		else:
			i += 1


## Estela de los ladrones que corren, tiempo en el piso y rebote de cajas.
func _track(dt: float) -> void:
	var top := game.dash_speed()
	for th in game.thieves:
		var id: int = th["id"]
		# Ciclo de carrera: avanza con la distancia recorrida (no con el reloj),
		# así acelera y frena con el ladrón en vez de patinar.
		var r: Dictionary = _run.get(id, {"ph": float(id) * 0.7, "spd": 0.0, "flip": false, "land": 0.0})
		var v: Vector2 = th.get("vel", Vector2.ZERO)
		r["spd"] = lerpf(float(r["spd"]), v.length(), minf(1.0, dt * 12.0))
		var before := int(float(r["ph"]))
		r["ph"] = float(r["ph"]) + float(r["spd"]) * dt / 34.0          # un paso cada ~34 px
		if int(float(r["ph"])) != before and float(r["spd"]) > top * 0.5:
			r["land"] = 1.0                                           # pisada: polvito
			if not _rm and _rng.randf() < 0.5:
				_fx.append({"kind": "dust", "pos": (th["pos"] as Vector2) + Vector2(0, 4), "t": 0.0, "dur": 0.3})
		r["land"] = maxf(0.0, float(r["land"]) - dt * 8.0)
		# Mira hacia donde corre, con histéresis (no parpadea al serpentear).
		if absf(v.x) > top * 0.18:
			r["flip"] = v.x < 0.0
		_run[id] = r
		if th["state"] in ["enter", "flee"] and float(r["spd"]) > top * 0.6:
			var tr: Array = _trails.get(id, [])
			tr.push_front(th["pos"])
			if tr.size() > 5:
				tr.pop_back()
			_trails[id] = tr
		else:
			_trails.erase(id)
		if th["state"] == "down":
			_down_t[id] = float(_down_t.get(id, 0.0)) + dt
	for k in _drop_t.keys():
		_drop_t[k] = float(_drop_t[k]) + dt


func _handle(events: Array) -> void:
	for e in events:
		var p: Vector2 = e.get("pos", Vector2.ZERO)
		match e["type"]:
			"hit":
				Sfx.play("slap", 1.0 + _rng.randf_range(-0.08, 0.08))
				Sfx.vibrate(25)
				_kick(7.0, 0.06)
				_sparks(p - Vector2(0, TheftGame.BODY_OFFSET), Color("ffe07a"), 14)
				_fx.append({"kind": "impact", "pos": p - Vector2(0, TheftGame.BODY_OFFSET), "t": 0.0, "dur": 0.22, "s": 3.0})
				_fx.append({"kind": "ring", "pos": p - Vector2(0, TheftGame.BODY_OFFSET), "t": 0.0, "dur": 0.25})
				var c := int(e.get("combo", 1))
				_float_text(p - Vector2(0, 150), "¡PAF!" if c < 2 else "¡COMBO x%d!" % c, GOLD if c < 2 else Color("ffb070"), 22 if c < 2 else 26)
			"armor":
				Sfx.play("bonk")
				_kick(3.0)
				_sparks(p - Vector2(0, 110), Color("c9c7da"), 12)
				_fx.append({"kind": "impact", "pos": p - Vector2(0, 110), "t": 0.0, "dur": 0.18, "s": 2.0})
				_float_text(p - Vector2(0, 150), "¡CASCO!", Color("c9c7da"), 20)
			"miss":
				# La chancleta cae al piso, rebota y se desvanece.
				Sfx.play("flap", 0.8, 0.1)
				_fx.append({"kind": "dust", "pos": p, "t": 0.0, "dur": 0.4})
				_fx.append({"kind": "floor_chancla", "pos": p, "t": 0.0, "dur": 1.1, "rot": _rng.randf_range(-0.6, 0.6)})
			"civilian":
				Sfx.play("error")
				Sfx.vibrate(60)
				_kick(7.0)
				_float_text(p - Vector2(0, 150), "¡ERA UN CLIENTE!", RED, 20)
			"stunned":
				Sfx.play("empty", 0.8, 0.15)
				_float_text(_gun_rect().get_center() - Vector2(0, 50), "¡PERDÓN!", RED, 18)
			"empty":
				Sfx.play("empty", 1.0, 0.1)
				Sfx.vibrate(30)
				_float_text(_gun_rect().get_center() - Vector2(0, 50), "¡SIN CHANCLETAS!", GOLD, 20)
			"reload":
				Sfx.play("flap")
			"reloaded":
				Sfx.play("tap", 1.4)
				Sfx.vibrate(15)
			"drop":
				_drop_t[int(e["loot"])] = 0.0
				Sfx.play("whoosh", 1.3, 0.1)
			"pick":
				Sfx.play("tap", 1.2)
			"bagged":
				Sfx.play("bag")
				Sfx.vibrate(20)
				_bag_squash = 1.0
				var lid := int(e.get("loot", -1))
				if lid >= 0 and lid < game.loot.size():
					_fx.append({"kind": "into_bag", "pos": _drag_last if _drag_last != Vector2.ZERO else game.bag.get_center(),
						"product": int(game.loot[lid]["product"]), "t": 0.0, "dur": 0.16})
				_sparks(_bag_mouth(), GREEN, 12)
				_float_text(_bag_mouth() + Vector2(30, -30), "+1", GREEN, 24)
			"escaped":
				Sfx.play("error", 0.7, 0.2)
				_kick(2.0)
				_float_text(Vector2(clampf(p.x, 70, size.x - 70), p.y - 100), "¡SE ESCAPÓ!", RED, 20)
			"snatched":
				_fx.append({"kind": "dust", "pos": p, "t": 0.0, "dur": 0.4})
				_float_text(p - Vector2(0, 30), "¡PERDIDA!", RED, 18)
			"enter":
				Sfx.play("whoosh", 0.9 + _rng.randf() * 0.3, 0.25)
			"grab":
				Sfx.play("whoosh", 1.5, 0.2)
			"end":
				_to_result()


## Sacudón y congelado de impacto (nada con "reducir movimiento").
func _kick(shake: float, hitstop := 0.0) -> void:
	if _rm:
		return
	_shake = maxf(_shake, shake)
	_hitstop = maxf(_hitstop, hitstop)


func _sparks(p: Vector2, c: Color, n: int) -> void:
	for i in n:
		var a := _rng.randf() * TAU
		_fx.append({"kind": "spark", "pos": p, "vel": Vector2(cos(a), sin(a)) * _rng.randf_range(80, 220),
			"t": 0.0, "dur": _rng.randf_range(0.25, 0.45), "color": c})


func _float_text(p: Vector2, text: String, c: Color, sz: int) -> void:
	_fx.append({"kind": "text", "pos": Vector2(clampf(p.x, 90.0, size.x - 90.0), maxf(p.y, 60.0)), "text": text, "color": c, "size": sz, "t": 0.0, "dur": 0.9})


func _to_result() -> void:
	phase = "result"
	pt = 0.0
	_dragging = -1
	var r := game.saved()
	Sfx.play("tier" if r >= 0.999 else ("mission" if r >= 0.7 else "error"))
	_finish()
	_result_btn = U.button("SEGUIR", "verde", "", 52, U.SIZE_TITLE)
	_result_btn.custom_minimum_size = Vector2(210, 52)
	_result_btn.position = Vector2(size.x / 2 - 105, size.y * 0.78)
	_result_btn.modulate.a = 0.0
	U.on_press(_result_btn, _dismiss)
	add_child(_result_btn)
	var tw := create_tween()
	tw.tween_interval(0.1 if _rm else 0.7)
	tw.tween_property(_result_btn, "modulate:a", 1.0, 0.2)


func _finish() -> void:
	if _counted:
		return
	_counted = true
	finished.emit(game.saved(), game.perfect())


func _dismiss() -> void:
	if _dismissed:
		return
	_dismissed = true
	dismissed.emit()


# ------------------------------------------------------------------ toques

## Zona de la mano con la chancleta (abajo a la derecha): tocarla trae más.
func _gun_rect() -> Rect2:
	return Rect2(size.x - 210, size.y - 180, 210, 180)


## Pose de la mano: [pivote de la muñeca en pantalla, rotación].
## Mira hacia el último toque, respira, revolea hacia adelante y baja a buscar más.
func _gun_pose() -> Array:
	var base := Vector2(size.x - 18, size.y - 16)          # muñeca (cuadro 80,80 a x2)
	var off := Vector2.ZERO
	var rot := 0.0
	if phase == "play" and game:
		off.x = clampf((_aim.x - size.x * 0.55) * 0.07, -18.0, 8.0)
		off.y = clampf((_aim.y - size.y * 0.45) * 0.05, -8.0, 12.0)
		rot = clampf((size.y * 0.45 - _aim.y) / size.y, -0.3, 0.3) * 0.12
		if not _rm:
			off.y += sin(pt * 2.2) * 2.0
		var e := clampf(_recoil / 0.16, 0.0, 1.0)
		if e > 0.0:
			var k := e * e if e < 0.6 else 1.0 - (e - 0.6) * 0.5        # revoleo seco y vuelta suave
			off += Vector2(-26, -16) * k
			rot -= 0.34 * k
		if game.reload_t > 0.0:
			var r := 1.0 - game.reload_t / TheftGame.RELOAD_TIME
			var dip := sin(r * PI)
			off += Vector2(-6, 64) * dip
			rot -= 0.32 * dip
		elif game.stun_t > 0.0 and not _rm:
			off.x += sin(pt * 40.0) * 2.0
	elif phase == "intro":
		off.y = (1.0 - _ease_back(clampf((pt - 0.3) / 0.5, 0.0, 1.0))) * 200.0
	return [(base + off).round(), rot]


## Punto del cuadro de la mano (en píxeles del arte) llevado a la pantalla.
func _gun_point(art: Vector2) -> Vector2:
	var pose := _gun_pose()
	return (pose[0] as Vector2) + ((art - Vector2(80, 80)) * GUN).rotated(float(pose[1]))


## Boca de la bolsa (ahí caen las cajas).
func _bag_mouth() -> Vector2:
	return Vector2(game.bag.position.x + 70, game.bag.position.y + 12)


func _crate_at(p: Vector2) -> bool:
	for l in game.loot:
		if l["state"] == "floor" and (l["pos"] as Vector2).distance_to(p) < TheftGame.GRAB_RADIUS:
			return true
	return false


func _gui_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT:
		var p: Vector2 = ev.position
		if ev.pressed:
			if phase == "intro":
				if _waiting:
					_waiting = false
					_first_time = false
					pt = INTRO - 1.5 + 0.001
				elif pt > 0.9 and pt < INTRO - 1.5:
					pt = INTRO - 1.5          # saltear la explicación
				return
			if phase != "play":
				return
			if _gun_rect().grow(8).has_point(p):
				game.reload()
				_handle(game.take_events())
				return
			# Sin chancletas: cualquier toque trae más (no gasta el tiempo en buscar la mano).
			if game.ammo <= 0 and game.reload_t <= 0.0 and game.stun_t <= 0.0 and not _crate_at(p):
				game.reload()
				_handle(game.take_events())
				return
			var lid := game.drag_start(p)
			if lid >= 0:
				_dragging = lid
				_drag_off = Vector2.ZERO
				_drag_last = p
				_handle(game.take_events())
				return
			_aim_target = p
			var r := game.tap(p)
			if r in ["hit", "armor", "miss", "civilian"]:
				_shoot_fx(p)
			_handle(game.take_events())
		elif _dragging >= 0:
			_drag_last = p
			game.drag_end(_dragging, p)
			_dragging = -1
			_handle(game.take_events())
		accept_event()
	elif ev is InputEventMouseMotion and _dragging >= 0:
		game.drag_move(_dragging, ev.position)
		_drag_last = ev.position
		accept_event()


## 15.2: el revoleo. La mano se va hacia adelante y la chancleta sale girando
## desde donde la tenía agarrada hasta el toque, con una parábola chica.
func _shoot_fx(target: Vector2) -> void:
	Sfx.play("throw", 1.0 + _rng.randf_range(-0.08, 0.08), 0.02)
	_recoil = 0.16
	_kick(1.5)
	_aim = _aim.lerp(_aim_target, 0.85)
	_throws.append({"from": _gun_point(Vector2(44, 34)), "to": target, "t": 0.0, "dur": FLY,
		"spin": (1.0 if _rng.randf() < 0.5 else -1.0) * _rng.randf_range(16.0, 24.0)})


# ------------------------------------------------------------------ dibujo

func _draw() -> void:
	_sh = Vector2(_rng.randf_range(-_shake, _shake), _rng.randf_range(-_shake, _shake)).round() if _shake > 0.5 else Vector2.ZERO
	draw_set_transform(_sh)
	_draw_room()
	if phase == "intro":
		_sh = Vector2.ZERO
		draw_set_transform(_sh)
		_draw_bag()
		_draw_gun()
		_draw_intro()
		return
	_draw_shelf()
	_draw_entities()
	_draw_fx()
	_draw_ambient()
	_sh = Vector2.ZERO
	draw_set_transform(_sh)
	# Las manos van en primer plano (no se sacuden con el mundo: se mueven solas).
	_draw_bag()
	_draw_gun()
	_draw_gun_fx()
	if phase == "result":
		_draw_result()          # el HUD de juego ya no hace falta
	else:
		_draw_hud()


func _draw_room() -> void:
	if _room == null or _room_size != size:
		_bake_room()
	draw_texture(_room, Vector2.ZERO)
	# Balizas de alarma en la pared: se turnan y tiñen el ambiente.
	if phase != "result":
		var bt: Texture2D = _tex["beacon"]
		var on := int(Time.get_ticks_msec() / 260) % 2
		for i in 2:
			var bp := Vector2(10 if i == 0 else size.x - 38, 66)
			var lit := (on == i) and not _rm
			draw_texture_rect_region(bt, Rect2(bp, Vector2(28, 24)), Rect2((0 if lit or _rm else 14), 0, 14, 12))
			if lit:
				draw_texture_rect(_tex["siren"], Rect2(bp + Vector2(14, 12) - Vector2(70, 70), Vector2(140, 140)), false, Color(1, 0.2, 0.25, 0.4))
	# Alarma: borde rojo que late (no toda la pantalla: menos sobre-dibujado y parpadeo suave).
	if not _rm and (phase == "play" or phase == "intro"):
		var pulse := 0.5 + 0.5 * sin(Time.get_ticks_msec() / 320.0)
		var c := Color(0.85, 0.1, 0.15, 0.2 + 0.2 * pulse)
		draw_rect(Rect2(0, 0, size.x, 6), c)
		draw_rect(Rect2(0, size.y - 6, size.x, 6), c)
		draw_rect(Rect2(0, 6, 6, size.y - 12), c)
		draw_rect(Rect2(size.x - 6, 6, 6, size.y - 12), c)


## Hornea en una textura todo lo que no se mueve. 12.1: se pinta a la mitad de
## resolución (1 píxel = 1 píxel del arte) y se agranda x2 sin filtrar, así el
## fondo tiene la misma grilla que los sprites: pared del negocio, zócalo,
## baldosas calcáreas en damero, alfombra con guarda pampa, maceta y cajas,
## sombra de contacto bajo la pared, dos charcos de luz del techo y viñeta,
## todo con tramado ordenado (Bayer 4x4) en vez de degradés.
func _bake_room() -> void:
	_room_size = size
	var w := maxi(2, int(size.x))
	var h := maxi(2, int(size.y))
	var aw := int(ceil(w / 2.0))
	var ah := int(ceil(h / 2.0))
	var img := Image.create(aw, ah, false, Image.FORMAT_RGBA8)
	img.fill(Color("6d432b"))
	var wb := int((h * 0.27 + 20.0) / 2.0)
	# Baldosas: damero crema/terracota con alguna variante (calcárea con rombo, fisura).
	var tiles := _image(_tex["floor_tiles"])
	var trng := RandomNumberGenerator.new()
	trng.seed = 77
	var ty := 0
	var y := wb
	while y < ah:
		var tx := 0
		var x := -((aw / 2) % 16)
		while x < aw:
			var v := (tx + ty) % 2
			var r := trng.randf()
			if v == 0 and r < 0.3:
				v = 2
			elif v == 1 and r < 0.07:
				v = 3
			if tiles:
				img.blit_rect(tiles, Rect2i(v * 16, 0, 16, 16), Vector2i(x, y))
			x += 16
			tx += 1
		y += 16
		ty += 1
	# Alfombra centrada en el piso: compone la pantalla.
	var rug := _image(_tex["rug"])
	var floor_h := ah - wb
	if rug and floor_h > 150:
		img.blend_rect(rug, Rect2i(0, 0, 112, 128), Vector2i(aw / 2 - 56, wb + 16 + (floor_h - 128 - 60) / 2))
	# Pared del negocio: el interior a x1 (= x2 en pantalla), centrado.
	var back: Texture2D = _tex.get("back")
	var bi := _image(back)
	if bi:
		var top := wb - bi.get_height() + 20
		img.blend_rect(bi, Rect2i(0, 0, bi.get_width(), bi.get_height()), Vector2i(int(round((aw - bi.get_width()) / 2.0)), top))
	else:
		img.fill_rect(Rect2i(0, 0, aw, wb), Color("e4ad69"))
	# Zócalo de madera.
	img.fill_rect(Rect2i(0, wb - 1, aw, 1), Color("4a2717"))
	img.fill_rect(Rect2i(0, wb, aw, 1), Color("c2804e"))
	img.fill_rect(Rect2i(0, wb + 1, aw, 2), Color("8e4e2a"))
	img.fill_rect(Rect2i(0, wb + 3, aw, 1), Color("4a2717"))
	# Utilería contra la pared (fuera del camino de la mercadería).
	var plant := _image(_tex["plant"])
	if plant:
		img.blend_rect(plant, Rect2i(0, 0, 22, 34), Vector2i(10, wb + 10 - 34))
	var boxes := _image(_tex["boxes"])
	if boxes:
		img.blend_rect(boxes, Rect2i(0, 0, 30, 30), Vector2i(aw - 40, wb + 9 - 30))
	# Luz: sombra de contacto, charcos de luz del techo y viñeta, cuantizados con Bayer.
	const BAYER := [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5]
	var l1 := Vector2(aw * 0.3, wb + floor_h * 0.32)
	var l2 := Vector2(aw * 0.7, wb + floor_h * 0.32)
	var lr := maxf(30.0, aw * 0.32)
	var cen := Vector2(aw * 0.5, ah * 0.55)
	for py in range(wb + 4, ah):
		for px in aw:
			var th := (float(BAYER[(py % 4) * 4 + px % 4]) + 0.5) / 16.0
			var d := float(py - wb - 4)
			var shade := 0.0
			if d < 12.0:
				shade = 0.32 * (1.0 - d / 12.0)                   # sombra bajo la pared
			var vx := (px - cen.x) / (aw * 0.62)
			var vy := (py - cen.y) / (ah * 0.62)
			shade += clampf((sqrt(vx * vx + vy * vy) - 0.62) / 0.5, 0.0, 1.0) * 0.38
			var pa := Vector2(px, py)
			var lit := 0.0
			for lc in [l1, l2]:
				var q: Vector2 = (pa - lc) / Vector2(lr, lr * 0.55)
				lit = maxf(lit, 1.0 - q.length())
			lit = clampf(lit, 0.0, 1.0) * 0.16
			# Escalones de 0,08 con umbral tramado: se ve pixel art, no un degradé.
			var s_q := floorf(shade / 0.08 + th) * 0.08
			var l_q := floorf(lit / 0.08 + th) * 0.08
			if s_q <= 0.0 and l_q <= 0.0:
				continue
			var c := img.get_pixel(px, py)
			c = c.darkened(s_q).lerp(Color(1.0, 0.95, 0.82), l_q)
			img.set_pixel(px, py, c)
	img.resize(aw * 2, ah * 2, Image.INTERPOLATE_NEAREST)
	_room = ImageTexture.create_from_image(img)


## Imagen RGBA8 sin comprimir de una textura (para hornear).
static func _image(t: Texture2D) -> Image:
	if t == null:
		return null
	var im := t.get_image()
	if im == null:
		return null
	if im.is_compressed():
		im.decompress()
	im.convert(Image.FORMAT_RGBA8)
	return im


func _make_shadow() -> Texture2D:
	var img := Image.create(32, 10, false, Image.FORMAT_RGBA8)
	for x in 32:
		for y in 10:
			var dx := (x - 15.5) / 16.0
			var dy := (y - 4.5) / 5.0
			if dx * dx + dy * dy <= 1.0:
				img.set_pixel(x, y, Color(0.24, 0.1, 0.04, 1.0))
	return ImageTexture.create_from_image(img)


func _draw_shelf() -> void:
	# Estante de madera con ménsulas y etiquetas de precio (tramo de 32x14 a x2).
	var y := game.shelf_y + 2
	draw_rect(Rect2(0, y + 16, size.x, 6), Color(0.24, 0.1, 0.04, 0.3))
	var st: Texture2D = _tex["shelf"]
	var x := 0.0
	while x < size.x:
		draw_texture_rect(st, Rect2(x, y, 64, 28), false)
		x += 64.0
	for l in game.loot:
		if l["state"] == "shelf":
			_crate(l["home"], int(l["product"]), 1.0, 0.0)


func _crate(center: Vector2, product: int, alpha: float, wobble: float, scale_k := 1.0) -> void:
	var tex: Texture2D = _tex["crate"]
	var s := SPR * scale_k
	var sz := Vector2(22, 18) * s
	var tl := (center - Vector2(sz.x / 2.0, sz.y - 6)).round()
	if _rm:
		wobble = 0.0
	if wobble != 0.0:
		draw_set_transform(center + _shake_off(), wobble, Vector2.ONE)
		tl = (-Vector2(sz.x / 2.0, sz.y - 6)).round()
	draw_texture_rect(tex, Rect2(tl, sz), false, Color(1, 1, 1, alpha))
	if product < _icons.size() and _icons[product]:
		var ic: Texture2D = _icons[product]
		var isz := Vector2(20, 20) * scale_k
		draw_texture_rect(ic, Rect2((tl + Vector2(sz.x / 2.0, sz.y / 2.0 + 2) - isz / 2.0).round(), isz), false, Color(1, 1, 1, alpha))
	if wobble != 0.0:
		draw_set_transform(_shake_off())


func _shake_off() -> Vector2:
	return _sh


## Sprite de una hoja horizontal con los pies (abajo-centro) en feet.
## 12.2: el espejado se hace con la transformación (escala -1 en x). Antes se
## pasaba un Rect2 de ancho negativo, que Godot 4.7 NO espeja: lo corría un ancho
## entero a la derecha, y los ladrones que corrían hacia la izquierda quedaban
## lejos de su sombra (o fuera de la pantalla) y parecían invisibles.
func _spr(tex: Texture2D, frame: int, fw: int, fh: int, feet: Vector2, flip: bool, mod := Color.WHITE, s := SPR, sx := 1.0, sy := 1.0) -> void:
	if tex == null:
		return
	var sz := Vector2(fw, fh) * s
	var src := Rect2(frame * fw, 0, fw, fh)
	draw_set_transform(feet.round() + _sh, 0.0, Vector2(-sx if flip else sx, sy))
	draw_texture_rect_region(tex, Rect2(Vector2(-sz.x / 2.0, -sz.y).round(), sz), src, mod)
	draw_set_transform(_sh)


func _shadow(p: Vector2, rx: float, a := 0.3) -> void:
	draw_texture_rect(_shadow_tex, Rect2((p - Vector2(rx, rx * 0.3)).round(), Vector2(rx * 2.0, rx * 0.6)), false, Color(1, 1, 1, a))


func _draw_entities() -> void:
	var items: Array = []
	for th in game.thieves:
		if th["state"] in ["enter", "grab", "flee", "down"]:
			items.append({"y": (th["pos"] as Vector2).y, "th": th})
	for c in game.civilians:
		if c["state"] in ["walk", "scared"]:
			items.append({"y": (c["pos"] as Vector2).y, "civ": c})
	for l in game.loot:
		if l["state"] == "floor":
			items.append({"y": (l["pos"] as Vector2).y, "loot": l})
	items.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return float(a["y"]) < float(b["y"]))
	for it in items:
		if it.has("th"):
			_draw_thief(it["th"])
		elif it.has("civ"):
			_draw_civilian(it["civ"])
		else:
			_draw_floor_loot(it["loot"])
	# Cajas robadas (sobre la cabeza) y la que se arrastra, arriba de todo.
	for l in game.loot:
		if l["state"] == "carried":
			_crate(l["pos"], int(l["product"]), 1.0, sin(pt * 18.0) * 0.12)
	if _dragging >= 0 and game.loot[_dragging]["state"] == "drag":
		var dl: Dictionary = game.loot[_dragging]
		var near := game.bag.grow(22).has_point(dl["pos"])
		_shadow((dl["pos"] as Vector2) + Vector2(0, 20), 20, 0.25)
		_crate(dl["pos"], int(dl["product"]), 1.0, sin(pt * 10.0) * 0.08, 1.25 if near else 1.15)


func _draw_thief(th: Dictionary) -> void:
	var id: int = th["id"]
	var pos: Vector2 = th["pos"]
	var tex: Texture2D = (_tex_casco if th["helmet"] else _tex_thief)[id % 3]
	var r: Dictionary = _run.get(id, {"ph": 0.0, "spd": 0.0, "flip": false, "land": 0.0})
	var flip := bool(r["flip"])
	var spd := float(r["spd"]) / maxf(1.0, game.dash_speed())
	var alpha := 1.0
	var frame := 0
	var bob := 0.0
	var squash := 1.0
	match th["state"]:
		"enter", "flee":
			if spd < 0.2:
				frame = 0                                  # duda: quieto, respira
				bob = 0.0 if _rm else -absf(sin(pt * 5.0 + id)) * 2.0
			else:
				var ph := float(r["ph"])
				frame = int(ph * 2.0) % 4                  # 2 cuadros por paso
				if not _rm:
					bob = -absf(sin(ph * PI)) * 7.0 * minf(1.0, spd)     # salta en cada zancada
					squash = 1.0 - 0.06 * float(r["land"])
		"grab":
			frame = 4
			bob = 0.0 if _rm else sin(pt * 22.0) * 1.5
		"grab":
			frame = 4
		"down":
			var dt_down := float(_down_t.get(id, 0.0))
			frame = 5 if float(th["flash"]) > 0.0 else 6 + int(pt * 4.0) % 2
			alpha = 1.0 - clampf((dt_down - 1.2) / 0.5, 0.0, 1.0)
			if alpha <= 0.0:
				return
	# Estela de velocidad.
	var tr: Array = _trails.get(id, [])
	for i in range(tr.size() - 1, 0, -1):
		_spr(tex, frame, 48, 48, tr[i], flip, Color(1, 0.85, 0.8, 0.16 - i * 0.025), CHAR)
	# La sombra se achica cuando está en el aire.
	_shadow(pos + Vector2(0, 2), 32.0 * (1.0 + bob / 40.0), 0.3 * alpha)
	var mod := Color(1, 1, 1, alpha)
	if float(th["flash"]) > 0.0 and th["state"] != "down":
		mod = Color(2.0, 2.0, 2.0, 1.0)
	if squash != 1.0:
		# Aplastado en la pisada, desde los pies.
		_spr(tex, frame, 48, 48, pos + Vector2(0, 6 + bob * squash), flip, mod, CHAR, 2.0 - squash, squash)
	else:
		_spr(tex, frame, 48, 48, pos + Vector2(0, 6 + bob), flip, mod, CHAR)


func _draw_civilian(c: Dictionary) -> void:
	var tex: Texture2D = _tex_civ[int(c["kind"]) % _tex_civ.size()]
	var pos: Vector2 = c["pos"]
	var hop := 0.0
	if c["state"] == "scared" and not _rm:
		hop = -absf(sin(pt * 14.0)) * 10.0
	_shadow(pos + Vector2(0, 2), 26, 0.25)
	_spr(tex, int(pt * 8.0) % 4, 32, 48, pos + Vector2(0, hop), (c["vel"] as Vector2).x < 0, Color.WHITE, CHAR)
	if c["state"] == "scared":
		_text("!", pos + Vector2(0, -158 + hop), 30, RED)
	else:
		# Etiqueta: se distingue de un ladrón por forma, no sólo por la ropa.
		var tp := pos + Vector2(0, -156)
		draw_rect(Rect2(tp - Vector2(38, 11), Vector2(76, 22)), Color("2e7d4f"))
		draw_rect(Rect2(tp - Vector2(38, 11), Vector2(76, 2)), Color("8ccb6c"))
		_text("CLIENTE", tp, 16, CREAM, 2)


func _draw_floor_loot(l: Dictionary) -> void:
	var id: int = l["id"]
	var pos: Vector2 = l["pos"]
	var life := game.floor_life()
	var left := life - float(l["floor_t"])
	var bounce := 0.0
	var t_drop := float(_drop_t.get(id, 9.0))
	if t_drop < 0.45:
		bounce = -absf(sin(t_drop / 0.45 * PI * 2.0)) * 18.0 * (1.0 - t_drop / 0.45)
	var alpha := 1.0
	if left < 1.5 and int(pt * 4.0) % 2 == 0:
		alpha = 0.6
	_shadow(pos + Vector2(0, 6), 18, 0.3)
	# Aro de tiempo y halo "agarrame".
	var k := clampf(left / life, 0.0, 1.0)
	var ring_c := GREEN.lerp(RED, 1.0 - k)
	draw_arc(pos - Vector2(0, 10), 30, -PI / 2, -PI / 2 + TAU * k, 16, ring_c, 4.0)
	draw_arc(pos - Vector2(0, 10), 35, 0, TAU, 16, Color(1, 0.95, 0.6, 0.35), 2.0)
	_crate(pos + Vector2(0, bounce), int(l["product"]), alpha, 0.0)
	# Guía punteada hacia la bolsa.
	if _dragging < 0:
		var a := pos - Vector2(0, 10)
		var b := _bag_mouth()
		var n := int(a.distance_to(b) / 14.0)
		for i in n:
			var f := fposmod(float(i) / n + pt * 0.8, 1.0)
			draw_rect(Rect2(a.lerp(b, f).round() - Vector2(2, 2), Vector2(4, 4)), Color(1, 0.95, 0.6, 0.45))


## La mano izquierda con la bolsa (abajo a la izquierda, en primer plano).
## La boca del arte (45,11) cae en _bag_mouth(); se aplasta al recibir una caja.
func _draw_bag() -> void:
	var tex: Texture2D = _tex["bag_hand"]
	var bag := TheftGame.bag_rect(size.y) if game == null else game.bag
	var full := game != null and game.bagged_count() > 0
	var mouth := Vector2(bag.position.x + 70, bag.position.y + 12)
	var bob := 0.0 if _rm else sin(pt * 1.7) * 2.0
	if phase == "intro":
		bob += (1.0 - _ease_back(clampf((pt - 0.2) / 0.5, 0.0, 1.0))) * 220.0
	var near := game != null and _dragging >= 0 and game.bag.grow(60).has_point(game.loot[_dragging]["pos"])
	if near:
		var g := 0.5 + 0.5 * sin(pt * 12.0)
		var gr := 70.0 + g * 6.0
		draw_texture_rect(_tex["siren"], Rect2(mouth - Vector2(gr, gr), Vector2(gr, gr) * 2.0), false, Color(1, 0.9, 0.4, 0.45))
	var sq := _bag_squash
	var scl := Vector2(1.0 + 0.12 * sin(sq * PI) * sq, 1.0 - 0.1 * sin(sq * PI) * sq)
	var tl := mouth - Vector2(45, 11) * SPR + Vector2(0, bob)
	var pivot := tl + Vector2(44, 100) * SPR
	draw_set_transform(pivot.round(), 0.0, scl)
	draw_texture_rect_region(tex, Rect2((tl - pivot).round(), Vector2(88, 100) * SPR), Rect2((88 if full else 0), 0, 88, 100))
	draw_set_transform(Vector2.ZERO)
	if game == null or phase != "play":
		return
	var cnt := "%d/%d" % [game.bagged_count(), maxi(game.taken_count(), game.bagged_count())]
	var cp := Vector2(bag.end.x - 4, bag.position.y - 6)
	draw_rect(Rect2(cp, Vector2(56, 30)), Color(0.24, 0.1, 0.04, 0.9))
	draw_rect(Rect2(cp, Vector2(56, 2)), GREEN)
	_text(cnt, cp + Vector2(28, 15), 24, CREAM, 2)


## La mano derecha con la chancleta (abajo a la derecha). Cuadros: 0 con
## chancleta · 1 recién tirada · 2 sin chancletas (o yendo a buscar más).
func _draw_gun() -> void:
	var pose := _gun_pose()
	var piv: Vector2 = pose[0]
	var rot: float = pose[1]
	var frame := 0
	var empty := game != null and game.ammo <= 0 and game.reload_t <= 0.0
	if _recoil > 0.04:
		frame = 1
	elif empty:
		frame = 2
	elif game != null and game.reload_t > 0.0 and game.reload_t > TheftGame.RELOAD_TIME * 0.5:
		frame = 2
	var mod := Color.WHITE
	if game != null and game.stun_t > 0.0:
		mod = Color(0.62, 0.6, 0.66)
	draw_set_transform(piv, rot)
	draw_texture_rect_region(_tex["chancla_hand"], Rect2(-Vector2(80, 80) * GUN, Vector2(96, 96) * GUN), Rect2(frame * 96, 0, 96, 96), mod)
	draw_set_transform(Vector2.ZERO)


## Chancletas en vuelo y cajas que entran a la bolsa (arriba de todo).
func _draw_gun_fx() -> void:
	for f in _throws:
		var k := float(f["t"]) / float(f["dur"])
		var a: Vector2 = f["from"]
		var b: Vector2 = f["to"]
		var p := a.lerp(b, k) - Vector2(0, sin(k * PI) * clampf(a.distance_to(b) * 0.18, 20.0, 80.0))
		var s := lerpf(2.8, 1.8, k)          # se aleja: se achica
		draw_set_transform(p.round(), float(f["t"]) * float(f["spin"]))
		draw_texture_rect(_tex["chancla"], Rect2(-Vector2(17, 9) * s, Vector2(34, 18) * s), false)
		draw_set_transform(Vector2.ZERO)
	for f in _fx:
		var t := float(f["t"])
		if t < 0.0:
			continue
		var k := t / float(f["dur"])
		match f["kind"]:
			"into_bag":
				var a: Vector2 = f["pos"]
				var e := k * k
				var p := a.lerp(_bag_mouth(), e) - Vector2(0, sin(k * PI) * 40.0)
				_crate(p, int(f["product"]), 1.0, k * 2.0, lerpf(1.1, 0.4, e))


## Polvo en el aire en los charcos de luz (sólo decorado).
func _draw_ambient() -> void:
	if _rm:
		return
	var top := game.shelf_y + 40.0
	for mo in _motes:
		var p := Vector2((mo["pos"] as Vector2).x * size.x, top + (mo["pos"] as Vector2).y * (size.y - top - 160.0))
		var a := 0.18 + 0.14 * sin(pt * 2.0 + float(mo["ph"]))
		draw_rect(Rect2(p.round(), Vector2(2, 2)), Color(1, 0.96, 0.85, a))


func _draw_fx() -> void:
	for f in _fx:
		var k := float(f["t"]) / float(f["dur"])
		match f["kind"]:
			"impact":
				var fr := mini(3, int(k * 4.0))
				var s := float(f.get("s", 2.0))
				var sz := Vector2(32, 32) * s
				draw_texture_rect_region(_tex["impact"], Rect2(((f["pos"] as Vector2) - sz / 2.0).round(), sz), Rect2(fr * 32, 0, 32, 32))
			"floor_chancla":
				# La chancleta que no le pegó a nadie: rebota una vez y se desvanece.
				var t := float(f["t"])
				var hop := -absf(sin(minf(t / 0.3, 1.0) * PI)) * 16.0 * maxf(0.0, 1.0 - t / 0.3)
				draw_set_transform(((f["pos"] as Vector2) + Vector2(0, hop)).round(), float(f["rot"]))
				draw_texture_rect(_tex["chancla"], Rect2(-Vector2(17, 9) * 1.7, Vector2(34, 18) * 1.7), false, Color(1, 1, 1, 1.0 - maxf(0.0, k - 0.7) / 0.3))
				draw_set_transform(Vector2.ZERO)
			"ring":
				# Onda de choque: aro que se abre y se afina.
				draw_arc(f["pos"], 18.0 + 60.0 * k, 0, TAU, 24, Color(1, 0.95, 0.7, 0.7 * (1.0 - k)), maxf(1.0, 6.0 * (1.0 - k)))
			"spark":
				var p: Vector2 = (f["pos"] as Vector2) + (f["vel"] as Vector2) * float(f["t"]) + Vector2(0, 260.0 * float(f["t"]) * float(f["t"]))
				var c: Color = f["color"]
				c.a = 1.0 - k
				draw_rect(Rect2(p.round(), Vector2(4, 4)), c)
			"dust":
				for i in 5:
					var a := float(i) / 5.0 * TAU
					var p: Vector2 = (f["pos"] as Vector2) + Vector2(cos(a) * 18.0, sin(a) * 6.0) * k
					draw_circle(p, 5.0 * (1.0 - k) + 1.0, Color(0.95, 0.88, 0.75, 0.6 * (1.0 - k)))
			"text":
				var rise := 40.0 * k
				var pop := 1.0 if _rm else 1.0 + 0.4 * maxf(0.0, 1.0 - k * 6.0)
				var c: Color = f["color"]
				c.a = 1.0 - maxf(0.0, k - 0.6) / 0.4
				_text(f["text"], (f["pos"] as Vector2) - Vector2(0, rise), int(float(f["size"]) * pop), c)


func _draw_hud() -> void:
	var w := size.x
	# Tiempo.
	var k := game.time_left() / TheftGame.DURATION
	draw_rect(Rect2(10, 8, w - 20, 14), OUTLINE)
	var bar_c := GOLD if game.time_left() > 6.0 else (RED if int(pt * 3.0) % 2 == 0 else Color("ffc4c4"))
	draw_rect(Rect2(12, 10, (w - 24) * k, 10), bar_c)
	draw_rect(Rect2(12, 10, (w - 24) * k, 2), Color(1, 1, 1, 0.4))
	draw_rect(Rect2(w - 56, 28, 46, 28), Color(0.24, 0.1, 0.04, 0.85))
	_text("%d" % ceili(game.time_left()), Vector2(w - 33, 42), 24, CREAM if game.time_left() > 6.0 else Color("ffc4c4"))
	# Ladrones que quedan.
	var left := 0
	for th in game.thieves:
		if th["state"] in ["wait", "enter", "grab", "flee"]:
			left += 1
	draw_rect(Rect2(10, 28, 156, 28), Color(0.24, 0.1, 0.04, 0.85))
	_text("LADRONES: %d" % left, Vector2(88, 42), 20, CREAM)
	# Chancletas que quedan: una fila sobre la mano, a la derecha.
	var g := _gun_rect()
	var stunned := game.stun_t > 0.0
	var empty := game.ammo <= 0 and game.reload_t <= 0.0
	var shown := game.ammo
	if game.reload_t > 0.0:
		shown = int((1.0 - game.reload_t / TheftGame.RELOAD_TIME) * TheftGame.AMMO)
	var bt: Texture2D = _tex["chancla_icon"]
	var row := Vector2(w - 14 - TheftGame.AMMO * 16, g.position.y - 30)
	draw_rect(Rect2(row - Vector2(6, 4), Vector2(TheftGame.AMMO * 16 + 8, 30)), Color(0.12, 0.08, 0.1, 0.55))
	for i in TheftGame.AMMO:
		var full := i < shown
		draw_texture_rect_region(bt, Rect2(row + Vector2(i * 16, 0), Vector2(13, 22)), Rect2(0 if full else 9, 0, 9, 15))
	if empty:
		var pulse := 0.5 + 0.5 * sin(pt * 6.0)
		draw_rect(g.grow(-2), Color(0.84, 0.34, 0.43, 0.35 + 0.25 * pulse), false, 3.0)
		var bx := Rect2(Vector2(w - 258, g.position.y - 66), Vector2(250, 26))
		draw_rect(bx, Color(0.24, 0.1, 0.04, 0.9))
		_text("SIN CHANCLETAS: TOCÁ LA MANO", bx.get_center(), 16, GOLD, 2)
	elif stunned:
		_text("¡PERDÓN!", g.get_center() + Vector2(0, -38), 18, RED)
	# Combo (al medio, entre las dos manos).
	if game.combo >= 2:
		_text("COMBO x%d" % game.combo, Vector2(w / 2 + 10, size.y - 34), 24, Color("ffb070"))


func _draw_intro() -> void:
	var w := size.x
	var h := size.y
	var t := pt
	draw_rect(Rect2(0, 0, w, h), Color(0.08, 0.03, 0.05, clampf(t * 2.0, 0.0, 0.62)))
	if t < 0.22:
		draw_rect(Rect2(0, 0, w, h), Color(1, 0.3, 0.3, 0.6 * (1.0 - t / 0.22)))
	# Sirenas que barren la pantalla.
	var glow: Texture2D = _tex["siren"]
	for i in 2:
		var x := w * (0.5 + 0.45 * sin(t * 5.0 + i * PI))
		var c := Color(1, 0.2, 0.25, 0.55) if i == 0 else Color(0.25, 0.45, 1, 0.55)
		draw_texture_rect(glow, Rect2(x - 120, -60, 240, 240), false, c)
	# Cartel.
	var punch := _ease_back(clampf((t - 0.12) / 0.4, 0.0, 1.0))
	if t > 0.12:
		var sz := int(lerpf(110.0, 54.0, punch))
		var rot := 0.0 if _rm else sin(t * 30.0) * 0.04 * maxf(0.0, 1.0 - t)
		draw_set_transform(Vector2(w / 2, h * 0.2) + _sh, rot)
		_text("¡ASALTO!", Vector2.ZERO, sz, RED, 8)
		draw_set_transform(_sh)
	if t > 0.45:
		_text("Una banda entra a %s" % biz_name, Vector2(w / 2, h * 0.2 + 48), 20, CREAM)
	# La banda cruza corriendo.
	for i in 3:
		var tt := t - 0.5 - i * 0.18
		if tt > 0.0 and tt < 0.75:
			var x := lerpf(-60.0, w + 60.0, tt / 0.75)
			var y := h * 0.42 + i * 22.0
			_spr(_tex_thief[i], int(t * 16.0) % 4, 48, 48, Vector2(x, y), false, Color.WHITE, CHAR)
			_spr(_tex["crate"], 0, 22, 18, Vector2(x, y - 120), false)
	# Instrucciones.
	if t > 1.5 and (t < INTRO - 1.45 or _waiting):
		var a := clampf((t - 1.5) * 8.0, 0.0, 1.0)
		var lines := [["TOCÁ a los ladrones", "para revolearles la chancleta"], ["ARRASTRÁ las cajas", "hasta la bolsa"], ["TOCÁ la mano", "para agarrar más chancletas"]]
		for i in 3:
			var y := h * 0.52 + i * 58.0
			draw_rect(Rect2(24, y - 24, w - 48, 50), Color(0.24, 0.1, 0.04, 0.95 * a))
			draw_rect(Rect2(24, y - 24, w - 48, 2), Color(0.95, 0.82, 0.45, a))
			_text(lines[i][0], Vector2(w / 2, y - 4), 20, Color(1, 0.86, 0.45, a))
			_text(lines[i][1], Vector2(w / 2, y + 16), 16, Color(1, 0.96, 0.9, a))
		var hint := "tocá para empezar" if _waiting else "tocá para seguir"
		_text(hint, Vector2(w / 2, h - 34), 18, Color(1, 0.96, 0.9, 0.85 * a))
	# 3, 2, 1, ¡YA!
	var cd := t - (INTRO - 1.4)
	if cd >= 0.0:
		var idx := int(cd / 0.35)
		var local := fmod(cd, 0.35) / 0.35
		var label: String = ["3", "2", "1", "¡YA!"][mini(idx, 3)]
		var s := lerpf(1.7, 1.0, _ease_back(clampf(local * 2.0, 0.0, 1.0)))
		_text(label, Vector2(w / 2, h * 0.6), int(72 * s), GOLD, 8)


func _draw_result() -> void:
	var w := size.x
	var h := size.y
	var r := game.saved()
	var a := clampf(pt * 3.0, 0.0, 1.0)
	draw_rect(Rect2(0, 0, w, h), Color(0.08, 0.03, 0.05, 0.9 * a))
	var title := "¡IMPECABLE!" if game.perfect() else ("¡DEFENDIDO!" if r >= 0.999 else ("¡SALVASTE CASI TODO!" if r >= 0.7 else "¡SE LLEVARON MERCADERÍA!"))
	var tc := GOLD if r >= 0.999 else (Color("ffb070") if r >= 0.7 else RED)
	var punch := _ease_back(clampf(pt / 0.4, 0.0, 1.0))
	_text(title, Vector2(w / 2, h * 0.2), int(lerpf(60.0, 30.0, punch)) if title.length() < 14 else int(lerpf(40.0, 22.0, punch)), tc, 6)
	var stars := 3 if game.perfect() else (2 if r >= 0.8 else (1 if r >= 0.55 else 0))
	for i in 3:
		var st := clampf((pt - 0.3 - i * 0.18) / 0.25, 0.0, 1.0)
		var c := GOLD if i < stars else Color(0.4, 0.3, 0.25)
		var sc := _ease_back(st) * (1.0 if i < stars else 0.8)
		_star(Vector2(w / 2 + (i - 1) * 64, h * 0.33), 24.0 * sc, c)
		if i < stars and st > 0.0 and st < 0.1:
			Sfx.play("coin", 1.0 + i * 0.15, 0.1)
	var lines := ["Salvaste el %d %% de la caja" % int(round(r * 100)), "Chancletazos: %d de %d" % [game.hits, game.shots], "Mejor combo x%d" % maxi(1, game.best_combo)]
	if practice:
		lines.append("Práctica: no perdés nada")
	elif r < 0.999:
		lines.append("Perdés el %d %% de la mercadería" % int(round(fraction * (1.0 - r) * 100)))
	elif game.perfect():
		lines.append("¡Premio: un cofre!")
	for i in lines.size():
		var la := clampf((pt - 0.6 - i * 0.12) * 4.0, 0.0, 1.0)
		var c := CREAM
		if i == 3:
			c = RED if r < 0.999 else GOLD
		c.a = la
		_text(lines[i], Vector2(w / 2, h * 0.44 + i * 34), 22, c)


func _star(c: Vector2, r: float, col: Color) -> void:
	if r <= 0.5:
		return
	var pts := PackedVector2Array()
	for i in 10:
		var a := -PI / 2 + i * PI / 5
		var rr := r if i % 2 == 0 else r * 0.45
		pts.append(c + Vector2(cos(a), sin(a)) * rr)
	var outline := PackedVector2Array(pts)
	outline.append(pts[0])
	draw_colored_polygon(pts, col)
	draw_polyline(outline, OUTLINE, 3.0)


func _text(s: String, center: Vector2, sz: int, c: Color, outline := 4) -> void:
	if _font == null or sz <= 0:
		return
	sz = maxi(2, (sz + 1) / 2 * 2)          # tamaños pares: menos glifos nuevos que rasterizar
	var key := "%d|%s" % [sz, s]
	var tw: float = _text_w.get(key, -1.0)
	if tw < 0.0:
		tw = _font.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, sz).x
		_text_w[key] = tw
	var p := (center + Vector2(-tw / 2.0, sz * 0.35)).round()
	var oc := OUTLINE
	oc.a = c.a
	draw_string_outline(_font, p, s, HORIZONTAL_ALIGNMENT_LEFT, -1, sz, outline, oc)
	draw_string(_font, p, s, HORIZONTAL_ALIGNMENT_LEFT, -1, sz, c)


static func _ease_back(x: float) -> float:
	var c1 := 1.70158
	var c3 := c1 + 1.0
	return 1.0 + c3 * pow(x - 1.0, 3) + c1 * pow(x - 1.0, 2)
