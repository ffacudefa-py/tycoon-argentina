class_name Main
extends Control
## Raíz de la interfaz.
##
## - Las 5 secciones se crean una sola vez y se alternan con visible (la
##   misma idea que el IndexedStack de PassIdle): cambiar de pestaña no
##   reinicia nada ni pierde el scroll.
## - Capas: modales (10), efectos (20), tutorial (30), avisos (40). Los
##   efectos y avisos no capturan toques (MOUSE_FILTER_IGNORE).
## - Respeta el área segura del teléfono (notch, barra de gestos).

static var instance: Main

signal section_changed(index: int)
signal business_selected(id: String)

const SECTIONS := ["Imperio", "Negocios", "Mapa", "Objetivos", "Perfil"]

var m: GameModel
var selected_business := "puesto"
var section := 0
var targets := {}            ## controles que el tutorial puede señalar

var top_bar: TopBar
var bottom_nav: BottomNav
var content: Control
var screens: Array[Control] = []
var modal_host: ModalHost
var toasts: ToastHost
var fx: FxLayer
var tutorial: TutorialOverlay
var _safe: MarginContainer


func _ready() -> void:
	instance = self
	m = Game.m
	theme = ThemeBuilder.build()
	set_anchors_preset(Control.PRESET_FULL_RECT)
	var bg := ColorRect.new()
	bg.color = U.BG
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)

	_safe = MarginContainer.new()
	_safe.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_safe)
	var col := U.vbox(0)
	_safe.add_child(col)
	top_bar = TopBar.new()
	col.add_child(top_bar)
	content = Control.new()
	content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.clip_contents = true
	col.add_child(content)
	bottom_nav = BottomNav.new()
	col.add_child(bottom_nav)
	bottom_nav.selected.connect(go_to)

	for cls in [EmpireScreen, BusinessesScreen, MapScreen, ObjectivesScreen, ProfileScreen]:
		var s: Control = cls.new()
		s.set_anchors_preset(Control.PRESET_FULL_RECT)
		s.visible = false
		content.add_child(s)
		screens.append(s)

	modal_host = ModalHost.new()
	add_child(modal_host)
	fx = FxLayer.new()
	add_child(fx)
	tutorial = TutorialOverlay.new()
	add_child(tutorial)
	toasts = ToastHost.new()
	add_child(toasts)

	m.notify.connect(func(text: String, kind: String) -> void: toasts.show_toast(text, kind))
	m.celebrate.connect(_on_celebrate)
	Game.offline_report.connect(func(r: Dictionary) -> void: OfflineReport.open(r))
	Game.model_reset.connect(_on_model_reset)
	get_viewport().size_changed.connect(_apply_safe_area)
	_apply_safe_area()
	go_to(0)
	if Game.load_warning != "":
		toasts.show_toast(Game.load_warning, "bad")
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--shots="):
			var shots := DevShots.new()
			shots.out_dir = a.substr(8)
			add_child(shots)
	if not Game.pending_offline.is_empty():
		var r := Game.pending_offline
		Game.pending_offline = {}
		OfflineReport.open.call_deferred(r)


func _apply_safe_area() -> void:
	var win := DisplayServer.window_get_size()
	var safe := DisplayServer.get_display_safe_area()
	var vp := get_viewport_rect().size
	if win.x <= 0 or vp.x <= 0 or not OS.has_feature("mobile"):
		for side in ["left", "top", "right", "bottom"]:
			_safe.add_theme_constant_override("margin_" + side, 0)
		return
	var k := vp.x / float(win.x)
	_safe.add_theme_constant_override("margin_left", int(ceil(max(0, safe.position.x) * k)))
	_safe.add_theme_constant_override("margin_top", int(ceil(max(0, safe.position.y) * k)))
	_safe.add_theme_constant_override("margin_right", int(ceil(max(0, win.x - safe.end.x) * k)))
	_safe.add_theme_constant_override("margin_bottom", int(ceil(max(0, win.y - safe.end.y) * k)))


func go_to(index: int) -> void:
	section = index
	for i in screens.size():
		screens[i].visible = i == index
	if screens[index].has_method("on_shown"):
		screens[index].on_shown()
	bottom_nav.set_selected(index)
	section_changed.emit(index)


func select_business(id: String, show_empire := true) -> void:
	if not m.biz[id]["owned"]:
		return
	selected_business = id
	business_selected.emit(id)
	if show_empire:
		go_to(0)


func register_target(key: String, control: Control) -> void:
	targets[key] = control


func toast(text: String, kind := "info") -> void:
	toasts.show_toast(text, kind)


## Muestra el resultado de una acción: si falló, aviso + sonido de error.
func result(r: Dictionary, success_sound := "") -> bool:
	if not r["ok"]:
		toasts.show_toast(r["msg"], "bad")
		Sfx.play("error")
		Sfx.vibrate(40)
		return false
	if success_sound != "":
		Sfx.play(success_sound)
	if r["msg"] != "":
		toasts.show_toast(r["msg"], "good")
	return true


## Confirmación antes de acciones irreversibles. always=true ignora el ajuste
## (prestigio y reinicio SIEMPRE piden confirmación).
func confirm(title: String, text: String, confirm_text: String, on_yes: Callable, danger := true, always := false) -> void:
	if not always and not Settings.get_value("confirm_irreversible"):
		on_yes.call()
		return
	ConfirmDialog.open(title, text, confirm_text, on_yes, danger)


func _on_celebrate(kind: String, info: Dictionary) -> void:
	match kind:
		"level":
			Sfx.play("buy", 1.0 + randf() * 0.1)
		"upgrade":
			Sfx.play("upgrade")
			Sfx.vibrate(20)
		"tier":
			Sfx.play("tier")
			Sfx.vibrate(60)
			fx.confetti_burst(fx_center())
		"unlock", "zone":
			Sfx.play("unlock")
			Sfx.vibrate(60)
			fx.confetti_burst(fx_center())
		"hire":
			Sfx.play("hire")
		"mission", "achievement", "daily":
			Sfx.play("mission")
			fx.sparkle_burst(Vector2(get_viewport_rect().size.x / 2, 80))
		"claim":
			Sfx.play("register")
		"stage", "prestige":
			Sfx.play("tier")
			fx.confetti_burst(fx_center())
		"event":
			Sfx.play("event")
		"restock":
			Sfx.play("whoosh")
		"campaign":
			Sfx.play("buy")


func fx_center() -> Vector2:
	var vp := get_viewport_rect().size
	return Vector2(vp.x / 2, vp.y * 0.3)


func _on_model_reset() -> void:
	selected_business = "puesto"
	for s in screens:
		if s.has_method("rebuild"):
			s.rebuild()
	go_to(0)
	tutorial.restart()


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_GO_BACK_REQUEST:
		if modal_host.close_top():
			return
		if section != 0:
			go_to(0)
