class_name BribeView
extends Control
## 11.2: pantalla del minijuego "La coima" (la lógica está en BribeGame).
##
## Comisaría: arriba la ventana con el patrullero y el policía con la mano
## estirada; abajo el escritorio con la pila de papeles, la trituradora
## (izquierda, ROJOS) y la carpeta del policía (derecha, BLANCOS). El papel de
## arriba se da vuelta y hay que deslizarlo antes de que se acabe su barra.
## Fases: intro (patrullero con sirena, cartel, reglas y 3-2-1), juego y
## resultado (sello APROBADO o la multa).
## 12.1: comisaría pintada en pixel art a la grilla de los sprites (pared de yeso
## con friso azul, placa de bronce, reloj que anda, cuadro con el escudo), ventana
## con persiana y la calle de enfrente. El patrullero llega frenando (ruedas que
## giran, luces de freno, cabeceo de la suspensión), queda en marcha con humo del
## caño de escape y balizas que tiñen el vidrio y la pared; si la coima sale bien
## se va acelerando. Escritorio de madera con carpeta de cuero, lámpara, taza,
## teléfono y sello; papeles con membrete, formularios, tablas y sellos (3 modelos).

signal finished(success: bool)      ## al terminar el juego (se aplica en el modelo)
signal dismissed                    ## al tocar SEGUIR

const INTRO := 3.6
const DOC := 2.0                     ## escala de los documentos
const OUTLINE := Color("3d1b0b")
const GOLD := Color("f2d173")
const CREAM := Color("fff6e6")
const RED := Color("d5576e")
const GREEN := Color("67d08e")
const BLUE := Color("4e8fd8")
const SWIPE_DIST := 60.0
const SWIPE_SPEED := 700.0
const WHITE_TITLES := ["HABILITACIÓN", "FACTURA", "PERMISO", "RECIBO", "PLANILLA", "CERTIFICADO"]
const RED_TITLES := ["LIBRO NEGRO", "FACTURA TRUCHA", "SOBRE", "PAGARÉ", "CONTRABANDO", "DOBLE CAJA"]

var m: GameModel
var game: BribeGame
var zid := ""
var zone_name := ""
var company := ""
var practice := false                ## práctica (Ajustes): el resultado no se aplica

var phase := "intro"
var pt := 0.0
var _shake := 0.0
var _sh := Vector2.ZERO
var _drag_from := Vector2.ZERO
var _drag_x := 0.0
var _dragging := false
var _drag_t := 0.0
var _flying: Array = []              ## {doc, from, to, t, dir}
var _fx: Array = []
var _cop_mood := 0.0                 ## >0 feliz un rato, <0 enojado
var _folder_bump := 0.0
var _shred_bump := 0.0
var _result_btn: Button
var _done := false
var _dismissed := false
var _rm := false
var _first_time := false
var _waiting := false
var _office: Texture2D
var _office_size := Vector2.ZERO
var _text_w := {}
var _press_t := 0
var _last_tick := -1
var _font: Font
var _rng := RandomNumberGenerator.new()
var _tex := {}
var _puff_t := 0.0
var _puffs: Array = []               ## humo del caño de escape {pos, t, dur}


func setup(model: GameModel, zone_id: String) -> void:
	m = model
	zid = zone_id
	zone_name = m.data.zone_by_id[zid]["name"] if m.data.zone_by_id.has(zid) else ""
	company = m.profile["company"]


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	focus_mode = Control.FOCUS_ALL
	clip_contents = true
	_font = get_theme_default_font()
	_rm = bool(Settings.get_value("reduce_motion"))
	_first_time = not bool(m.hard.get("seen_bribe", false))
	for k in ["cop", "stamp", "label", "shredder", "folder", "siren", "office_wall", "street", "window", "patrol_body",
			"wheel", "desk", "blotter", "lamp", "phone", "mug", "stamp_pad", "smoke"]:
		_tex[k] = U.tex("minigames/%s.png" % k)
	for i in 3:
		_tex["doc_white_%d" % i] = U.tex("minigames/doc_white_%d.png" % i)
		_tex["doc_red_%d" % i] = U.tex("minigames/doc_red_%d.png" % i)
	_rng.seed = int(m.now()) ^ hash(zid)
	grab_focus.call_deferred()


func _start_game() -> void:
	m.hard["seen_bribe"] = true
	game = BribeGame.new(_rng.randi(), Security.difficulty(m))
	phase = "play"
	pt = 0.0
	Sfx.play("event")


# ------------------------------------------------------------------- ciclo

func _process(dt: float) -> void:
	dt = minf(dt, 0.1)          # al volver de segundo plano no se "adelanta" el tiempo
	pt += dt
	_shake = maxf(0.0, _shake - dt * 30.0)
	_cop_mood = move_toward(_cop_mood, 0.0, dt) if _cop_mood > 0.0 else _cop_mood
	_folder_bump = maxf(0.0, _folder_bump - dt * 4.0)
	_shred_bump = maxf(0.0, _shred_bump - dt * 4.0)
	if _dragging:
		_drag_t += dt
	match phase:
		"intro":
			if _first_time and not _waiting and pt >= INTRO - 1.5 and pt - dt < INTRO - 1.5:
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
			game.step(dt)
			_handle(game.take_events())
			var u := game.urgency()
			if game.state == "play" and u < 0.4 and game.reveal_t <= 0.0:
				var tick := int(game.time_left * 6.0)
				if tick != _last_tick:
					_last_tick = tick
					Sfx.play("tick", 1.4, 0.12)
		"result":
			if pt > 20.0:
				_dismiss()
	for f in _flying:
		f["t"] = float(f["t"]) + dt
		if float(f["t"]) >= 0.24 and not f.get("landed", false):
			f["landed"] = true
			if int(f["dir"]) < 0:
				Sfx.play("shred")
				_shred_bump = 1.0
				for i in 10:
					_fx.append({"kind": "strip", "pos": _shredder_mouth() + Vector2(_rng.randf_range(-30, 30), 0),
						"vel": Vector2(_rng.randf_range(-40, 40), _rng.randf_range(60, 160)), "t": 0.0, "dur": 0.6,
						"color": Color("d5576e") if f["doc"]["red"] else Color("ede6da")})
			else:
				Sfx.play("stamp")
				_folder_bump = 1.0
	_puff_t -= dt
	if _puff_t <= 0.0 and not _rm:
		_puff_t = 0.3
		_puffs.append({"pos": _car_origin() + Vector2(150, 46), "t": 0.0, "dur": 0.9})
	for pf in _puffs:
		pf["pos"] = (pf["pos"] as Vector2) + Vector2(18, -10) * dt
	TheftView._age(_puffs, dt, -1.0)
	TheftView._age(_flying, 0.0, 0.3)
	TheftView._age(_fx, dt, -1.0)
	queue_redraw()


func _handle(events: Array) -> void:
	for e in events:
		match e["type"]:
			"ok":
				Sfx.play("swipe", 1.0 + 0.04 * mini(int(e["streak"]), 10))
				Sfx.vibrate(15)
				_cop_mood = 0.35
				if int(e["streak"]) % 5 == 0:
					_float_text(Vector2(size.x / 2, _stack_center().y - 150), "¡RACHA x%d!" % int(e["streak"]), GOLD, 24)
			"wrong", "timeout":
				Sfx.play("buzzer")
				Sfx.vibrate(120 if e["type"] == "wrong" else 60)
				if not _rm:
					_shake = 10.0
					_fx.append({"kind": "flash", "t": 0.0, "dur": 0.35, "color": Color(1, 0.2, 0.25)})
				_cop_mood = -1.0
				_to_result(false, "Te equivocaste de lado." if e["type"] == "wrong" else "Tardaste demasiado.")
			"won":
				Sfx.play("tier")
				if not _rm:
					_shake = 8.0
				_cop_mood = 99.0
				_to_result(true, "")


func _float_text(p: Vector2, text: String, c: Color, sz: int) -> void:
	_fx.append({"kind": "text", "pos": p, "text": text, "color": c, "size": sz, "t": 0.0, "dur": 0.9})


func _to_result(ok: bool, reason: String) -> void:
	phase = "result"
	pt = 0.0
	_dragging = false
	set_meta("ok", ok)
	set_meta("reason", reason)
	_finish()
	_result_btn = U.button("SEGUIR", "verde" if ok else "rojo", "", 52, U.SIZE_TITLE)
	_result_btn.custom_minimum_size = Vector2(210, 52)
	_result_btn.position = Vector2(size.x / 2 - 105, size.y * 0.45 + 150)
	_result_btn.modulate.a = 0.0
	U.on_press(_result_btn, _dismiss)
	add_child(_result_btn)
	var tw := create_tween()
	tw.tween_interval(0.1 if _rm else 0.8)
	tw.tween_property(_result_btn, "modulate:a", 1.0, 0.2)


func _finish() -> void:
	if _done:
		return
	_done = true
	finished.emit(bool(get_meta("ok", false)))


func _dismiss() -> void:
	if _dismissed:
		return
	_dismissed = true
	dismissed.emit()


# ------------------------------------------------------------------ toques

func _swipe(dir: int) -> void:
	if phase != "play" or game.state != "play" or game.reveal_t > 0.0:
		return
	var d := game.current()
	var from := _stack_center() + Vector2(_drag_x, 0)
	if game.swipe(dir):
		_flying.append({"doc": d, "from": from, "to": _shredder_mouth() if dir < 0 else _folder_mouth(), "t": 0.0, "dir": dir, "rot": _drag_x * 0.003})
	_drag_x = 0.0
	_handle(game.take_events())


func _gui_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT:
		if ev.pressed:
			if phase == "intro":
				if _waiting:
					_waiting = false
					_first_time = false
					pt = INTRO - 1.5 + 0.001
				elif pt > 0.9 and pt < INTRO - 1.5:
					pt = INTRO - 1.5
			elif phase == "play":
				_press_t = Time.get_ticks_msec()
				_dragging = true
				_drag_from = ev.position
				_drag_x = 0.0
				_drag_t = 0.0
		elif _dragging:
			_dragging = false
			var dx: float = ev.position.x - _drag_from.x
			var speed := absf(dx) / maxf(_drag_t, 0.016)
			if absf(dx) >= SWIPE_DIST or (absf(dx) > 18.0 and speed >= SWIPE_SPEED):
				_swipe(1 if dx > 0.0 else -1)
			elif absf(dx) < 12.0 and Time.get_ticks_msec() - _press_t < 220:
				# Toque corto: mitad izquierda = trituradora, derecha = carpeta.
				_swipe(-1 if ev.position.x < size.x / 2.0 else 1)
			else:
				_drag_x = 0.0
		accept_event()
	elif ev is InputEventMouseMotion and _dragging:
		_drag_x = clampf(ev.position.x - _drag_from.x, -size.x * 0.45, size.x * 0.45)
		accept_event()
	elif ev is InputEventKey and ev.pressed and not ev.echo:
		if ev.keycode == KEY_LEFT:
			_swipe(-1)
		elif ev.keycode == KEY_RIGHT:
			_swipe(1)


# ------------------------------------------------------------------ dibujo

func _stack_center() -> Vector2:
	return Vector2(size.x / 2.0, size.y * 0.53)


func _shredder_mouth() -> Vector2:
	return Vector2(70, size.y - 122)


func _folder_mouth() -> Vector2:
	return Vector2(size.x - 70, size.y - 112)


func _draw() -> void:
	_sh = Vector2(_rng.randf_range(-_shake, _shake), _rng.randf_range(-_shake, _shake)).round() if _shake > 0.5 else Vector2.ZERO
	draw_set_transform(_sh)
	_draw_office()
	if phase == "intro":
		_draw_intro()
		return
	if phase != "result":
		_draw_bins()
	if phase != "result" or pt < 0.25:
		_draw_stack()
	for f in _flying:
		_draw_flying(f)
	_draw_fx()
	_sh = Vector2.ZERO
	draw_set_transform(_sh)
	_draw_hud()
	if phase == "result":
		_draw_result()


const WIN := Rect2(8, 4, 200, 120)          ## ventana (marco) en la pared
const GLASS := Rect2(16, 12, 184, 104)      ## vidrio = la calle (92x52 a x2)


## Patrullero en la calle (en píxeles del arte): llega frenando, queda en marcha
## y, si la coima salió bien, se va acelerando. Devuelve [x, cabeceo, frenando].
func _car_state() -> Array:
	var park := 8.0
	var x := park
	var dy := 0.0
	var braking := false
	if phase == "intro":
		var k := clampf(pt / 1.2, 0.0, 1.0)
		x = lerpf(110.0, park, _ease_out(k))
		braking = k > 0.25 and k < 1.0
		if k > 0.5 and k < 1.0:
			dy = 1.0                                         # trompa abajo al frenar
		var s := pt - 1.2
		if s > 0.0:
			dy = roundf(sin(s * 16.0) * exp(-s * 5.0) * 2.0)  # rebote de la suspensión
	elif phase == "result" and bool(get_meta("ok", false)) and pt > 0.9:
		var g := (pt - 0.9) / 1.4
		x = park - 170.0 * g * g
		dy = -1.0 if g < 0.15 else 0.0                       # arranca y levanta la trompa
	elif not _rm:
		dy = float(int(Time.get_ticks_msec() / 90) % 2) * 0.5   # motor en marcha
	return [x, dy, braking]


## Esquina superior izquierda del auto en pantalla (sin cabeceo).
func _car_origin() -> Vector2:
	return GLASS.position + Vector2(float(_car_state()[0]), 19) * 2.0


## Región de textura a escala s recortada a clip (lo que se ve por la ventana).
func _blit_clip(tex: Texture2D, src: Rect2, pos: Vector2, s: float, clip: Rect2, mod := Color.WHITE) -> void:
	var dst := Rect2(pos.round(), src.size * s)
	var inter := dst.intersection(clip)
	if inter.size.x <= 0.5 or inter.size.y <= 0.5:
		return
	var sub := Rect2(src.position + (inter.position - dst.position) / s, inter.size / s)
	draw_texture_rect_region(tex, inter, sub, mod)


func _draw_office() -> void:
	var w := size.x
	var wall_h := 170.0
	if _office == null or _office_size != size:
		_bake_office()
	draw_texture(_office, Vector2.ZERO)
	# --- La calle por la ventana, con el patrullero.
	draw_texture_rect(_tex["street"], GLASS, false)
	var st := _car_state()
	var cx := float(st[0])
	var o := GLASS.position + Vector2(cx, 19) * 2.0
	var fast := phase == "result" and not bool(get_meta("ok", true))
	var lights := 0 if _rm else int(Time.get_ticks_msec() / (110 if fast else 180)) % 2
	_blit_clip(_tex["patrol_body"], Rect2(lights * 76, 0, 76, 30), o + Vector2(0, float(st[1]) * 2.0), 2.0, GLASS)
	var wf := posmod(int(cx / 6.0 / (TAU / 20.0)), 4)           # la rueda gira lo que avanza
	for wx in [15.0, 61.0]:
		_blit_clip(_tex["wheel"], Rect2(wf * 13, 0, 13, 13), o + Vector2(wx - 6.0, 19.0) * 2.0, 2.0, GLASS)
	if bool(st[2]):                                              # luces de freno
		_blit_clip(_tex["siren"], Rect2(0, 0, 64, 64), o + Vector2(64, 6) * 2.0, 0.5, GLASS, Color(1, 0.15, 0.2, 1))
	for pf in _puffs:
		var k := float(pf["t"]) / float(pf["dur"])
		var p: Vector2 = pf["pos"]
		_blit_clip(_tex["smoke"], Rect2(mini(4, int(k * 5.0)) * 16, 0, 16, 16), p - Vector2(8, 8) * (1.0 + k), 1.0 + k, GLASS, Color(1, 1, 1, 0.75))
	# Balizas: tiñen el vidrio y derraman luz sobre la pared.
	var col := Color(1, 0.2, 0.25) if lights == 0 else Color(0.3, 0.5, 1)
	var bar := o + Vector2(38, 3) * 2.0
	if GLASS.grow(16).has_point(bar):
		draw_rect(GLASS, Color(col, 0.08))
		draw_texture_rect(_tex["siren"], Rect2(bar - Vector2(100, 100), Vector2(200, 200)), false, Color(col, 0.3))
		_blit_clip(_tex["siren"], Rect2(0, 0, 64, 64), bar - Vector2(24, 24), 0.75, GLASS, Color(col, 0.9))
	draw_texture_rect(_tex["window"], WIN, false)
	# --- Placa de bronce y reloj de pared.
	var pl := Rect2(218, 14, maxf(60.0, w - 230), 28)
	draw_rect(pl.grow(2), Color("7a4a12"))
	draw_rect(pl, Color("c99a2e"))
	draw_rect(Rect2(pl.position, Vector2(pl.size.x, 2)), Color("ffe07a"))
	draw_rect(Rect2(pl.position + Vector2(0, pl.size.y - 2), Vector2(pl.size.x, 2)), Color("a8781a"))
	for sx in [pl.position.x + 4, pl.end.x - 6]:
		draw_rect(Rect2(sx, pl.position.y + 13, 2, 2), Color("7a4a12"))
	_text("COMISARÍA", pl.get_center() + Vector2(0, 1), 18, Color("4a2717"), 0)
	_draw_clock(Vector2(230, 74), 14.0)
	# --- Policía con la mano estirada.
	var frame := int(pt * 2.0) % 2
	if _cop_mood < 0.0:
		frame = 3
	elif _cop_mood > 0.0:
		frame = 2
	var cop_y := wall_h + 6.0
	if phase == "intro":
		cop_y += (1.0 - _ease_back(clampf((pt - 0.6) / 0.4, 0.0, 1.0))) * 110.0
	var hop := -absf(sin(pt * 10.0)) * 6.0 if _cop_mood > 0.0 and not _rm else 0.0
	# Se asoma por detrás del mostrador: lo que queda debajo de la línea no se dibuja.
	var top := cop_y - 96.0 + hop
	var vis := clampf(wall_h + 6.0 - top, 0.0, 96.0)
	if vis > 1.0:
		draw_texture_rect_region(_tex["cop"], Rect2(Vector2(w - 110, top).round(), Vector2(64, vis)), Rect2(frame * 32, 0, 32, vis / 2.0))


## Reloj de pared con la hora real.
func _draw_clock(c: Vector2, r: float) -> void:
	draw_circle(c + Vector2(2, 2), r + 2, Color(0.24, 0.1, 0.04, 0.25))
	draw_circle(c, r + 2, Color("6d3a20"))
	draw_circle(c, r, Color("fff6e6"))
	for i in 12:
		var a := i * TAU / 12.0
		var p := c + Vector2(cos(a), sin(a)) * (r - 3)
		draw_rect(Rect2(p.round() - Vector2(1, 1), Vector2(2, 2)), Color("4a2717") if i % 3 == 0 else Color("c9bfb0"))
	var tm := Time.get_time_dict_from_system()
	var mi := float(tm["minute"]) + float(tm["second"]) / 60.0
	var hr := float(int(tm["hour"]) % 12) + mi / 60.0
	draw_line(c, c + Vector2.from_angle(hr / 12.0 * TAU - PI / 2) * (r * 0.5), Color("3d1b0b"), 2.0)
	draw_line(c, c + Vector2.from_angle(mi / 60.0 * TAU - PI / 2) * (r * 0.78), Color("3d1b0b"), 2.0)
	draw_line(c, c + Vector2.from_angle(float(tm["second"]) / 60.0 * TAU - PI / 2) * (r * 0.82), Color("d5576e"), 1.0)
	draw_rect(Rect2(c - Vector2(1, 1), Vector2(2, 2)), Color("c99a2e"))


## Hornea lo que no se mueve, a la mitad de resolución (la grilla del arte) y x2:
## pared, escritorio de madera con su canto, carpeta de cuero bajo los papeles,
## lámpara, taza, teléfono y sello, luz de la lámpara y viñeta tramada (Bayer).
func _bake_office() -> void:
	_office_size = size
	var w := maxi(2, int(size.x))
	var h := maxi(2, int(size.y))
	var aw := int(ceil(w / 2.0))
	var ah := int(ceil(h / 2.0))
	var img := Image.create(aw, ah, false, Image.FORMAT_RGBA8)
	img.fill(Color("6d3a20"))
	var wall := TheftView._image(_tex["office_wall"])
	if wall:
		var x := 0
		while x < aw:
			img.blit_rect(wall, Rect2i(0, 1, 240, 85), Vector2i(x, 0))
			x += 240
	var dy := 85
	# 12.2: la madera mide 256x192 (cubre el ancho sin repetirse en x).
	var desk := TheftView._image(_tex["desk"])
	if desk:
		var dw := desk.get_width()
		var dh := desk.get_height()
		var yy := dy
		while yy < ah:
			var xx := 0
			while xx < aw:
				img.blit_rect(desk, Rect2i(0, 0, dw, dh), Vector2i(xx, yy))
				xx += dw
			yy += dh
	# Canto del escritorio.
	img.fill_rect(Rect2i(0, dy, aw, 1), Color("3d1b0b"))
	img.fill_rect(Rect2i(0, dy + 1, aw, 1), Color("c2804e"))
	img.fill_rect(Rect2i(0, dy + 2, aw, 2), Color("8e4e2a"))
	img.fill_rect(Rect2i(0, dy + 4, aw, 1), Color("4a2717"))
	var c := _stack_center() / 2.0
	# 12.2: objetos más grandes y con sombra de contacto; ninguno se toca entre sí
	# ni con la carpeta ni con los bordes (lámpara y taza a la izquierda, teléfono
	# y sello a la derecha, todos dentro de la pantalla).
	var props := [["blotter", Vector2i(int(c.x) - 58, int(c.y) - 68)], ["lamp", Vector2i(2, dy + 1)],
		["mug", Vector2i(44, dy + 18)], ["phone", Vector2i(aw - 52, dy + 3)], ["stamp_pad", Vector2i(aw - 46, dy + 38)]]
	for pr in props:
		var im := TheftView._image(_tex[pr[0]])
		if im:
			img.blend_rect(im, Rect2i(0, 0, im.get_width(), im.get_height()), pr[1])
	const BAYER := [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5]
	var lamp_c := Vector2(23, dy + 28)
	var cen := Vector2(aw * 0.5, (dy + ah) * 0.5)
	for py in range(dy + 5, ah):
		for px in aw:
			var th := (float(BAYER[(py % 4) * 4 + px % 4]) + 0.5) / 16.0
			var lit := clampf(1.0 - Vector2(px, py).distance_to(lamp_c) / 44.0, 0.0, 1.0) * 0.18
			var vx := (px - cen.x) / (aw * 0.6)
			var vy := (py - cen.y) / ((ah - dy) * 0.6)
			var shade := clampf((sqrt(vx * vx + vy * vy) - 0.7) / 0.5, 0.0, 1.0) * 0.35
			if py - dy < 10:
				shade += 0.25 * (1.0 - float(py - dy) / 10.0)
			var s_q := floorf(shade / 0.08 + th) * 0.08
			var l_q := floorf(lit / 0.06 + th) * 0.06
			if s_q <= 0.0 and l_q <= 0.0:
				continue
			img.set_pixel(px, py, img.get_pixel(px, py).darkened(s_q).lerp(Color(1, 0.86, 0.5), l_q))
	img.resize(aw * 2, ah * 2, Image.INTERPOLATE_NEAREST)
	_office = ImageTexture.create_from_image(img)


func _draw_bins() -> void:
	var h := size.y
	var lean := clampf(_drag_x / 120.0, -1.0, 1.0) if _dragging else 0.0
	# Trituradora (izquierda) y carpeta (derecha) con su halo cuando el papel va hacia ellas.
	var sl := 1.0 + 0.12 * sin(_shred_bump * PI)
	var fl := 1.0 + 0.12 * sin(_folder_bump * PI)
	if lean < -0.1:
		draw_circle(_shredder_mouth() + Vector2(0, 40), 70, Color(0.84, 0.34, 0.43, 0.3 * -lean))
	if lean > 0.1:
		draw_circle(_folder_mouth() + Vector2(0, 30), 70, Color(0.31, 0.56, 0.85, 0.3 * lean))
	# 12.2: más arriba (antes las ruedas quedaban contra el borde de la pantalla)
	draw_set_transform(Vector2(70, h - 18) + _sh, 0.0, Vector2(sl, 2.0 - sl))
	draw_texture_rect(_tex["shredder"], Rect2(-64, -120, 128, 120), false)
	draw_set_transform(Vector2(size.x - 70, h - 18) + _sh, 0.0, Vector2(fl, 2.0 - fl))
	draw_texture_rect(_tex["folder"], Rect2(-64, -112, 128, 112), false)
	draw_set_transform(_sh)
	var ly := h - 152
	draw_rect(Rect2(10, ly - 13, 120, 26), Color(0.24, 0.1, 0.04, 0.85))
	draw_rect(Rect2(size.x - 130, ly - 13, 120, 26), Color(0.24, 0.1, 0.04, 0.85))
	_text("← ROJOS", Vector2(70, ly), 20, Color("ffc4c4"), 2)
	_text("BLANCOS →", Vector2(size.x - 70, ly), 20, Color("d0e8ff"), 2)


func _doc_tex(d: Dictionary) -> Texture2D:
	return _tex[("doc_red_%d" if d["red"] else "doc_white_%d") % (int(d.get("kind", 0)) % 3)]


## Un documento centrado en c (escala k, rotación rot, ancho visible flip 0..1).
func _draw_doc(d: Dictionary, c: Vector2, k: float, rot: float, flip := 1.0, face := true, mod := Color.WHITE) -> void:
	var sz := Vector2(96, 120) * DOC * k
	draw_set_transform(c.round() + _sh, rot, Vector2(maxf(0.02, flip), 1.0))
	draw_rect(Rect2(-sz / 2.0 + Vector2(6, 8), sz), Color(0.24, 0.1, 0.04, 0.25 * mod.a))
	if not face:
		# Dorso: papel madera con renglones que se transparentan y un sello de agua.
		draw_rect(Rect2(-sz / 2.0, sz), Color("e4c89a") * mod)
		draw_rect(Rect2(-sz / 2.0, Vector2(sz.x, 4)), Color("f6e6c4") * mod)
		draw_rect(Rect2(-sz / 2.0 + Vector2(0, sz.y - 4), Vector2(sz.x, 4)), Color("c9a878") * mod)
		var ly := -sz.y / 2.0 + 0.25 * sz.y
		while ly < sz.y / 2.0 - 0.12 * sz.y:
			draw_rect(Rect2(-sz.x / 2.0 + 0.1 * sz.x, ly, sz.x * 0.8, 2), Color(0.79, 0.66, 0.47, 0.5 * mod.a))
			ly += maxf(4.0, 0.06 * sz.y)
		draw_circle(Vector2.ZERO, 0.11 * sz.x, Color(0.79, 0.66, 0.47, 0.45 * mod.a))
		draw_rect(Rect2(-sz / 2.0, sz), OUTLINE * mod, false, 2.0)
		draw_set_transform(_sh)
		return
	draw_texture_rect(_doc_tex(d), Rect2(-sz / 2.0, sz), false, mod)
	_paper_mark(bool(d["red"]), -sz / 2.0 + Vector2(20, 20) * k, k, mod.a)
	var titles: Array = RED_TITLES if d["red"] else WHITE_TITLES
	var title: String = titles[int(d["kind"]) % titles.size()]
	_text(title, Vector2(-sz.x * 0.08, -sz.y * 0.36), int(16 * k), CREAM if d["red"] else OUTLINE, 0)
	if d["decoy"]:
		if d["red"]:
			draw_texture_rect(_tex["label"], Rect2(Vector2(-44, 6) * k, Vector2(88, 28) * k), false, mod)
		else:
			draw_set_transform(c.round() + _sh + Vector2(36, 34).rotated(rot) * k, rot - 0.35, Vector2(maxf(0.02, flip), 1.0))
			draw_texture_rect(_tex["stamp"], Rect2(-40 * k, -24 * k, 80 * k, 48 * k), false, Color(1, 1, 1, 0.9 * mod.a))
			_text("URGENTE", Vector2(0, 0), int(14 * k), Color("d5576e"), 0)
	draw_set_transform(_sh)


## Marca fija en la esquina del papel: una X en un círculo oscuro (rojo =
## desechar) o un tilde en un círculo azul (blanco = entregar). No depende de
## distinguir colores (daltonismo).
func _paper_mark(red: bool, c: Vector2, k: float, a: float) -> void:
	var r := 14.0 * k
	if red:
		draw_circle(c, r, Color(0.24, 0.1, 0.04, a))
		var d := r * 0.5
		draw_line(c + Vector2(-d, -d), c + Vector2(d, d), Color(1, 0.85, 0.85, a), 3.0 * k)
		draw_line(c + Vector2(-d, d), c + Vector2(d, -d), Color(1, 0.85, 0.85, a), 3.0 * k)
	else:
		draw_circle(c, r, Color(0.31, 0.56, 0.85, a))
		draw_polyline(PackedVector2Array([c + Vector2(-r * 0.5, 0), c + Vector2(-r * 0.12, r * 0.4), c + Vector2(r * 0.55, -r * 0.4)]), Color(1, 1, 1, a), 3.0 * k)


func _draw_stack() -> void:
	var c := _stack_center()
	var remaining := game.docs.size() - game.idx
	# Papeles de abajo (de dorso).
	for i in range(mini(3, remaining - 1), 0, -1):
		_draw_doc({}, c + Vector2(i * 3, i * 5), 1.0, (i % 2 * 2 - 1) * 0.03 * i, 1.0, false)
	if game.state != "play" and phase == "result" and not bool(get_meta("ok", false)) and game.idx < game.docs.size():
		_draw_doc(game.current(), c + Vector2(_rng.randf_range(-3, 3), 0), 1.0, 0.0, 1.0, true, Color(1, 0.75, 0.75))
		return
	if game.idx >= game.docs.size():
		return
	var d := game.current()
	var rev := 1.0 - clampf(game.reveal_t / BribeGame.REVEAL, 0.0, 1.0)
	var u := game.urgency()
	var tremble := Vector2(_rng.randf_range(-2, 2), _rng.randf_range(-1, 1)) if u < 0.35 and rev >= 1.0 and not _rm else Vector2.ZERO
	var rot := float(d["rot"]) + _drag_x * 0.003
	var pos := c + Vector2(_drag_x, -absf(_drag_x) * 0.12) + tremble
	if rev < 0.5:
		_draw_doc(d, pos, 1.0, rot, 1.0 - rev * 2.0, false)
	else:
		_draw_doc(d, pos, 1.0, rot, (rev - 0.5) * 2.0, true)
	# Barra de tiempo del papel.
	var bw := 200.0
	var by := c.y - 150.0
	draw_rect(Rect2(c.x - bw / 2 - 2, by - 2, bw + 4, 18), OUTLINE)
	var col := GREEN.lerp(GOLD, clampf((0.7 - u) / 0.35, 0.0, 1.0)).lerp(RED, clampf((0.35 - u) / 0.35, 0.0, 1.0))
	draw_rect(Rect2(c.x - bw / 2, by, bw * u, 14), col)
	draw_rect(Rect2(c.x - bw / 2, by, bw * u, 2), Color(1, 1, 1, 0.45))


func _draw_flying(f: Dictionary) -> void:
	var k := clampf(float(f["t"]) / 0.24, 0.0, 1.0)
	var e := _ease_in(k)
	var from: Vector2 = f["from"]
	var to: Vector2 = f["to"]
	var p := from.lerp(to, e) + Vector2(0, -sin(k * PI) * 60.0)
	var rot := float(f["rot"]) + float(f["dir"]) * k * 1.2
	_draw_doc(f["doc"], p, lerpf(1.0, 0.25, e), rot, 1.0, true, Color(1, 1, 1, 1.0 - maxf(0.0, k - 0.8) * 5.0))


func _draw_fx() -> void:
	for f in _fx:
		var k := float(f["t"]) / float(f["dur"])
		match f["kind"]:
			"strip":
				var p: Vector2 = (f["pos"] as Vector2) + (f["vel"] as Vector2) * float(f["t"])
				var c: Color = f["color"]
				c.a = 1.0 - k
				draw_rect(Rect2(p.round(), Vector2(3, 10)), c)
			"text":
				var c: Color = f["color"]
				c.a = 1.0 - maxf(0.0, k - 0.6) / 0.4
				_text(f["text"], (f["pos"] as Vector2) - Vector2(0, 40.0 * k), int(float(f["size"]) * (1.0 + 0.4 * maxf(0.0, 1.0 - k * 6.0))), c)
			"flash":
				var c: Color = f["color"]
				c.a = 0.5 * (1.0 - k)
				draw_rect(Rect2(Vector2.ZERO, size), c)
			"confetti":
				var p: Vector2 = (f["pos"] as Vector2) + (f["vel"] as Vector2) * float(f["t"]) + Vector2(0, 300.0 * float(f["t"]) * float(f["t"]))
				var c: Color = f["color"]
				c.a = 1.0 - k
				draw_rect(Rect2(p.round(), Vector2(5, 3) if int(float(f["t"]) * 20.0) % 2 == 0 else Vector2(3, 5)), c)


func _draw_hud() -> void:
	var w := size.x
	draw_rect(Rect2(16, 134, 176, 28), Color(0.24, 0.1, 0.04, 0.85))
	var label := "PAPELES %d/%d" % [mini(game.idx + 1, game.docs.size()), game.docs.size()]
	if game.streak >= 3:
		label += "  ·  x%d" % game.streak
	_text(label, Vector2(104, 148), 20, GOLD, 2)


func _draw_intro() -> void:
	var w := size.x
	var h := size.y
	var t := pt
	draw_rect(Rect2(0, 0, w, h), Color(0.03, 0.05, 0.12, clampf((t - 0.9) * 2.0, 0.0, 0.62)))
	var glow: Texture2D = _tex["siren"]
	for i in 2:
		var x := w * (0.5 + 0.45 * sin(t * 6.0 + i * PI))
		var c := Color(1, 0.2, 0.25, 0.45) if i == 0 else Color(0.25, 0.45, 1, 0.45)
		draw_texture_rect(glow, Rect2(x - 120, 120, 240, 240), false, c)
	if t > 1.0:
		var punch := _ease_back(clampf((t - 1.0) / 0.4, 0.0, 1.0))
		_text("LA COIMA", Vector2(w / 2, h * 0.36), int(lerpf(100.0, 52.0, punch)), BLUE.lerp(CREAM, 0.3), 8)
		_text("Arreglá con la comisaría de %s" % zone_name, Vector2(w / 2, h * 0.36 + 42), 18, CREAM)
	if t > 1.4 and (t < INTRO - 1.45 or _waiting):
		var a := clampf((t - 1.4) * 5.0, 0.0, 1.0)
		var y := h * 0.56
		_draw_doc({"red": true, "decoy": false, "kind": 0}, Vector2(w * 0.28, y), 0.42, -0.1, 1.0, true, Color(1, 1, 1, a))
		_draw_doc({"red": false, "decoy": false, "kind": 0}, Vector2(w * 0.72, y), 0.42, 0.1, 1.0, true, Color(1, 1, 1, a))
		var swing := sin(t * 6.0) * 8.0
		_text("← ROJOS", Vector2(w * 0.28 - swing, y + 66), 20, Color(1, 0.77, 0.77, a))
		_text("a la trituradora", Vector2(w * 0.28, y + 86), 16, Color(1, 1, 1, a))
		_text("BLANCOS →", Vector2(w * 0.72 + swing, y + 66), 20, Color(0.82, 0.91, 1, a))
		_text("a la carpeta", Vector2(w * 0.72, y + 86), 16, Color(1, 1, 1, a))
		_text("Manda el color del PAPEL (no el sello).", Vector2(w / 2, y + 118), 18, Color(1, 0.86, 0.45, a))
		_text("¡Si tardás o le errás, multa!", Vector2(w / 2, y + 140), 18, Color(1, 0.86, 0.45, a))
		_text("También podés tocar a la izquierda o a la derecha.", Vector2(w / 2, y + 164), 16, Color(1, 1, 1, 0.8 * a))
		_text("tocá para empezar" if _waiting else "tocá para seguir", Vector2(w / 2, h - 34), 18, Color(1, 0.96, 0.9, 0.85 * a))
	var cd := t - (INTRO - 1.4)
	if cd >= 0.0:
		var idx := int(cd / 0.35)
		var local := fmod(cd, 0.35) / 0.35
		var label: String = ["3", "2", "1", "¡YA!"][mini(idx, 3)]
		var s := lerpf(1.7, 1.0, _ease_back(clampf(local * 2.0, 0.0, 1.0)))
		_text(label, Vector2(w / 2, h * 0.62), int(72 * s), GOLD, 8)


func _draw_result() -> void:
	var w := size.x
	var h := size.y
	var ok := bool(get_meta("ok", false))
	var a := clampf((pt - 0.25) * 3.0, 0.0, 1.0)
	draw_rect(Rect2(0, 0, w, h), Color(0.05, 0.03, 0.08, 0.68 * a))
	if pt > 0.25:
		var punch := _ease_back(clampf((pt - 0.25) / 0.35, 0.0, 1.0))
		var s := lerpf(3.0, 1.0, punch)
		draw_set_transform(Vector2(w / 2, h * 0.33), -0.08 if ok else 0.06, Vector2(s, s))
		var col := GREEN if ok else RED
		draw_rect(Rect2(-120, -34, 240, 68), Color(col, 0.18))
		draw_rect(Rect2(-120, -34, 240, 68), col, false, 5.0)
		draw_rect(Rect2(-112, -26, 224, 52), col, false, 2.0)
		_text("APROBADO" if ok else "MULTA", Vector2.ZERO, 44, col, 4)
		draw_set_transform(Vector2.ZERO)
		if pt - get_process_delta_time() < 0.6 and pt >= 0.6:
			_shake = 6.0
			Sfx.play("stamp", 0.8)
			if ok:
				for i in (0 if _rm else 24):
					var ang := _rng.randf() * TAU
					_fx.append({"kind": "confetti", "pos": Vector2(w / 2, h * 0.33), "vel": Vector2(cos(ang), sin(ang) - 0.6) * _rng.randf_range(120, 320),
						"t": 0.0, "dur": 1.2, "color": [GOLD, GREEN, BLUE, RED, CREAM][i % 5]})
	var lines: Array = []
	if ok:
		lines = ["Nadie te roba en %s" % zone_name, "por %d minutos." % int(Security.cfg(m).get("bribe_minutes", 30)), "Papeles en regla: %d" % game.docs.size()]
	else:
		lines = [String(get_meta("reason", "")), "Tus ingresos bajan %d %%" % int(round(Security.fine_income(m) * 100)), "por %d minutos." % int(Security.cfg(m).get("fine_minutes", 5))]
	if practice:
		lines = [String(get_meta("reason", "")) if not ok else "¡Le ganaste a la comisaría!", "Papeles: %d de %d" % [mini(game.idx, game.docs.size()), game.docs.size()], "Práctica: no se cobra ni se aplica nada."]
	var pa := clampf((pt - 0.6) * 4.0, 0.0, 1.0)
	var panel := Rect2(24, h * 0.45 - 26, w - 48, 150)
	draw_rect(panel, Color(0.24, 0.1, 0.04, 0.9 * pa))
	draw_rect(Rect2(panel.position, Vector2(panel.size.x, 3)), Color(GREEN if ok else RED, pa))
	draw_rect(panel, Color(0.95, 0.82, 0.45, 0.6 * pa), false, 2.0)
	for i in lines.size():
		var la := clampf((pt - 0.8 - i * 0.12) * 4.0, 0.0, 1.0)
		var c := CREAM
		c.a = la
		_text(lines[i], Vector2(w / 2, h * 0.45 + i * 30), 22, c)
	if not practice:
		_text("Te quedan %d de %d coimas hoy" % [Security.bribes_left_today(m), Security.bribe_daily(m)], Vector2(w / 2, h * 0.45 + 108), 16, Color(1, 0.86, 0.45, clampf((pt - 1.2) * 4.0, 0.0, 1.0)))


func _text(s: String, center: Vector2, sz: int, c: Color, outline := 4) -> void:
	if _font == null or sz <= 0 or s == "":
		return
	sz = maxi(2, (sz + 1) / 2 * 2)
	var key := "%d|%s" % [sz, s]
	var tw: float = _text_w.get(key, -1.0)
	if tw < 0.0:
		tw = _font.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, sz).x
		_text_w[key] = tw
	var p := (center + Vector2(-tw / 2.0, sz * 0.35)).round()
	if outline > 0:
		var oc := OUTLINE
		oc.a = c.a
		draw_string_outline(_font, p, s, HORIZONTAL_ALIGNMENT_LEFT, -1, sz, outline, oc)
	draw_string(_font, p, s, HORIZONTAL_ALIGNMENT_LEFT, -1, sz, c)


static func _ease_back(x: float) -> float:
	var c1 := 1.70158
	var c3 := c1 + 1.0
	return 1.0 + c3 * pow(x - 1.0, 3) + c1 * pow(x - 1.0, 2)


static func _ease_out(x: float) -> float:
	return 1.0 - pow(1.0 - x, 3)


static func _ease_in(x: float) -> float:
	return x * x
