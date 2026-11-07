class_name MenuGuide
extends RefCounted
## Guías cortas de cada menú (textos en data/menu_guides.json), con Tito.
##
## - La primera vez que se entra a un menú se abre sola (después del tutorial
##   guiado y sin otra ventana encima).
## - Se vuelve a ver cuando se quiera con el botón de información: en la barra
##   de arriba explica la sección actual y en las ventanas va junto a la cruz
##   (ModalWindow.with_help).
## Las vistas se guardan en la partida (m.tutorial["guides"]).

const PATH := "res://data/menu_guides.json"
## Guía de cada sección de la barra de abajo, en el orden de Main.SECTIONS.
const SECTION_KEYS := ["imperio", "negocios", "mapa", "objetivos", "perfil"]

static var _data := {}


static func guides() -> Dictionary:
	if _data.is_empty():
		var f := FileAccess.open(PATH, FileAccess.READ)
		if f:
			var d = JSON.parse_string(f.get_as_text())
			if d is Dictionary:
				_data = d
	return _data


static func has_guide(key: String) -> bool:
	return guides().has(key)


static func seen(key: String) -> bool:
	return (Game.m.tutorial.get("guides", {}) as Dictionary).has(key)


static func _mark_seen(key: String) -> void:
	var g: Dictionary = Game.m.tutorial.get("guides", {})
	g[key] = true
	Game.m.tutorial["guides"] = g


## Abre la guía si nunca se vio. `over_modal`: la guía es de una ventana (se
## abre encima de ella); las de sección esperan a que no haya ventanas.
static func maybe_show(key: String, over_modal := false) -> void:
	var main := Main.instance
	if main == null or not has_guide(key) or seen(key) or _dev_mode():
		return
	if TutorialSteps.active(Game.m) or main.start.is_open():
		return
	if not over_modal and main.modal_host.has_open():
		return
	open(key)


## Al mostrar una sección: su guía si nunca se vio.
static func open_first_time(index: int) -> void:
	if index >= 0 and index < SECTION_KEYS.size():
		maybe_show(SECTION_KEYS[index])


static func open_section(index: int) -> void:
	if index >= 0 and index < SECTION_KEYS.size():
		open(SECTION_KEYS[index])


static func open(key: String) -> void:
	if not has_guide(key):
		return
	_mark_seen(key)
	var g: Dictionary = guides()[key]
	var pages: Array = g.get("pages", [])
	if pages.is_empty():
		return
	var body := U.vbox(8)
	var row := U.hbox(8)
	var mascot := U.avatar(TutorialOverlay.MASCOT)
	mascot.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	row.add_child(mascot)
	var col := U.vbox(4)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var counter := U.label("", U.SIZE_SMALL, U.TEXT_SOFT, true)
	col.add_child(counter)
	var text := U.para("", U.SIZE_BODY, U.TEXT)
	col.add_child(text)
	row.add_child(col)
	body.add_child(row)
	var buttons := U.hbox(8)
	var prev := U.button("ANTERIOR", "crema", "izquierda", 40, U.SIZE_SMALL)
	prev.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var next := U.button("SIGUIENTE", "verde", "derecha", 40, U.SIZE_SMALL)
	next.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	buttons.add_child(prev)
	buttons.add_child(next)
	body.add_child(buttons)
	var page := [0]
	var w_ref := []
	var show := func() -> void:
		var i: int = page[0]
		counter.text = "Tito te explica · %d de %d" % [i + 1, pages.size()]
		text.text = str(pages[i])
		prev.visible = i > 0
		next.text = "¡ENTENDIDO!" if i == pages.size() - 1 else "SIGUIENTE"
		next.icon = U.icon_tex("check" if i == pages.size() - 1 else "derecha")
	U.on_press(prev, func() -> void:
		page[0] = maxi(0, page[0] - 1)
		show.call())
	U.on_press(next, func() -> void:
		if page[0] >= pages.size() - 1:
			w_ref[0].close()
			return
		page[0] += 1
		show.call())
	show.call()
	w_ref.append(Main.instance.modal_host.open(str(g.get("title", "Ayuda")), body, true, 320))


## Las capturas automáticas y las pruebas no abren guías solas (taparían los toques).
static func _dev_mode() -> bool:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--shots=") or a.begins_with("--dev-save="):
			return true
	return false
