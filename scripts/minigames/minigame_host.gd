class_name MinigameHost
extends CanvasLayer
## 11.2: anfitrión de los minijuegos (asalto y coima).
##
## Ocupa toda la pantalla MENOS la barra superior (que sigue mostrando el
## avatar y el nombre de la empresa): debajo de ella pone una franja con el
## nombre del jugador y el título del minijuego, y abajo la vista del juego
## (TheftView o BribeView), que hace su propia animación de entrada.
## Al terminar resuelve el resultado en el modelo (Security) y se cierra.
##
## Los robos pendientes los arranca Main (poll en _process) cuando no hay
## modales, tutorial ni pantalla de inicio delante.

static var current: MinigameHost

const STRIP_H := 26.0

var kind := ""            ## "theft" o "bribe"
var zid := ""
var _root: Control
var _strip: Control
var _strip_label: Label
var _view: Control
var _fade := 0.0
var _closing := false


static func is_open() -> bool:
	return current != null and is_instance_valid(current)


## El asalto pendiente (Security.pending_theft) como minijuego.
static func play_theft() -> void:
	if is_open() or Main.instance == null or Security.pending_theft(Game.m).is_empty():
		return
	_open("theft", "")


## Cobra la coima (Security.start_bribe) y la juega como minijuego.
static func play_bribe(zone_id: String) -> void:
	if is_open() or Main.instance == null:
		return
	var m := Game.m
	if Security.pending_bribe(m).is_empty():
		if not Main.instance.result(Security.start_bribe(m, zone_id)):
			return
	_open("bribe", zone_id)


static func _open(k: String, zone_id: String) -> void:
	var h := MinigameHost.new()
	h.kind = k
	h.zid = zone_id
	Main.instance.add_child(h)


func _init() -> void:
	layer = 36           # arriba del tutorial (30) y del festejo (35), debajo de los avisos (40)


func _ready() -> void:
	var m := Game.m
	current = self
	Security.minigame_active = true
	_root = Control.new()
	_root.theme = Main.instance.theme
	_root.mouse_filter = Control.MOUSE_FILTER_STOP
	_root.clip_contents = true
	add_child(_root)
	_strip = _make_strip()
	_root.add_child(_strip)
	if kind == "theft":
		var tv := TheftView.new()
		tv.setup(m, Security.pending_theft(m))
		tv.finished.connect(_on_theft_done)
		tv.dismissed.connect(close)
		_view = tv
	else:
		var bv := BribeView.new()
		bv.setup(m, zid)
		bv.finished.connect(_on_bribe_done)
		bv.dismissed.connect(close)
		_view = bv
	_view.position = Vector2(0, STRIP_H)
	_root.add_child(_view)
	_sync_rect()
	_root.modulate.a = 0.0
	# Los avisos esperan a que termine: taparían la bolsa o la trituradora.
	Main.instance.toasts.visible = false
	Sfx.play("alarm" if kind == "theft" else "siren")
	Sfx.vibrate(80)


func _make_strip() -> Control:
	var m := Game.m
	var strip := Control.new()
	strip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var bg := ColorRect.new()
	bg.color = Color("3d1b0b")
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	strip.add_child(bg)
	var line := ColorRect.new()
	line.color = Color("d5576e") if kind == "theft" else Color("4e8fd8")
	line.anchor_right = 1.0
	line.anchor_top = 1.0
	line.anchor_bottom = 1.0
	line.offset_top = -3
	line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	strip.add_child(line)
	_strip_label = U.label("", U.SIZE_SMALL, Color("f7eda4"), true, HORIZONTAL_ALIGNMENT_CENTER)
	_strip_label.set_anchors_preset(Control.PRESET_FULL_RECT)
	_strip_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_strip_label.clip_text = true
	_strip_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	var who: String = m.profile["company"]
	if kind == "theft":
		var bid: String = Security.pending_theft(m).get("business", "")
		_strip_label.text = "%s defiende %s" % [who, m.data.business_by_id[bid]["name"] if m.data.business_by_id.has(bid) else "su negocio"]
	else:
		_strip_label.text = "%s en la comisaría de %s" % [who, m.data.zone_by_id[zid]["name"] if m.data.zone_by_id.has(zid) else ""]
	strip.add_child(_strip_label)
	return strip


## Todo debajo de la barra superior (que queda visible con el nombre).
func _sync_rect() -> void:
	var vp := get_viewport().get_visible_rect().size
	var top := 0.0
	if Main.instance and Main.instance.top_bar:
		top = Main.instance.top_bar.get_global_rect().end.y
	var r := Rect2(0, top, vp.x, vp.y - top)
	if _root.position != r.position or _root.size != r.size:
		_root.position = r.position
		_root.size = r.size
		_strip.size = Vector2(r.size.x, STRIP_H)
		_view.size = Vector2(r.size.x, r.size.y - STRIP_H)


func _process(dt: float) -> void:
	_sync_rect()
	if _closing:
		_fade = maxf(0.0, _fade - dt * 4.0)
		_root.modulate.a = _fade
		if _fade <= 0.0:
			queue_free()
	elif _fade < 1.0:
		_fade = minf(1.0, _fade + dt * 6.0)
		_root.modulate.a = _fade


## El resultado se aplica apenas termina el juego (la pantalla de resultado es
## sólo visual): cerrar la app en el resultado no permite repetirlo.
func _on_theft_done(saved: float, perfect: bool) -> void:
	Security.resolve_theft(Game.m, saved, perfect)
	Game.save()


func _on_bribe_done(success: bool) -> void:
	Security.resolve_bribe(Game.m, success)
	Game.save()


func close() -> void:
	_closing = true
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE


func _exit_tree() -> void:
	Security.minigame_active = false
	if Main.instance and Main.instance.toasts:
		Main.instance.toasts.visible = true
	if current == self:
		current = null


# ------------------------------------------------- pruebas (sólo desarrollo)

## Asalto inmediato en el negocio elegido (llena el depósito si hace falta y
## saltea la seguridad paga). Lo usa el botón de Ajustes del APK de desarrollo.
static func debug_theft(m: GameModel) -> void:
	if not Security.pending_theft(m).is_empty():
		return
	var bid: String = Main.instance.selected_business if Main.instance else m.first_business()
	if not m.biz.has(bid) or not m.biz[bid]["owned"]:
		bid = m.owned_ids()[0]
	for p in m.derive(bid)["products"]:
		m.biz[bid]["stock"][p["id"]] = maxf(float(m.biz[bid]["stock"].get(p["id"], 0.0)), float(p["cap"]))
	m.hard["protected"].erase(m.biz[bid]["zone"])
	Security.start_theft(m, bid)


## Coima inmediata: si no alcanza la plata, la regala; si no quedan del día, repone.
static func debug_bribe(m: GameModel) -> void:
	var bid: String = Main.instance.selected_business if Main.instance else m.first_business()
	var zid: String = m.biz[bid]["zone"]
	if m.economy.money < Security.bribe_cost(m):
		m.economy.earn(Security.bribe_cost(m) * 2, "dev")
	if Security.bribes_left_today(m) <= 0:
		m.hard["bribe_count"] = 0
	MinigameHost.play_bribe(zid)
