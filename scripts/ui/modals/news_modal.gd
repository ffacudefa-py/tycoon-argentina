class_name NewsModal
extends RefCounted
## "Novedades": se muestra una vez por versión al entrar al juego (Ajustes guarda
## la última vista en news_seen). No aparece en las capturas automáticas.

const VERSION := "15.3"
const TITLE := "Novedades 15.3"
const ITEMS := [
	["persona", "Iniciá sesión de entrada", "INICIAR SESIÓN es ahora el botón principal del inicio: con cuenta tu partida va a la nube y conservás la insignia Pionero. Jugar como invitado sigue estando, al lado de Configuración."],
	["regalo", "Cofres rebalanceados", "Los cofres dan premios más chicos (plata y turbos x1,5 más cortos) para que no te salteen la progresión. Con 2 o más, ABRIR TODOS los abre de una."],
	["rayo", "Combo nuevo", "El contador de combo ahora es un cartel con una barrita que muestra cuánto te queda para seguir sumando."],
	["estrella", "Tutorial más claro", "En todos los pasos del tutorial se oscurece un poco lo demás, así se ve enseguida qué hay que tocar."],
]


static func should_show() -> bool:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--shots="):
			return false
	return str(Settings.get_value("news_seen")) != VERSION


static func open() -> void:
	Settings.set_value("news_seen", VERSION)
	var body := U.vbox(8)
	for it in ITEMS:
		var row := U.hbox(8)
		var ic := U.icon32(it[0])
		ic.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		row.add_child(ic)
		var col := U.vbox(1)
		col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		col.add_child(U.label(it[1], U.SIZE_BODY, U.TEXT, true))
		col.add_child(U.para(it[2], U.SIZE_SMALL, U.TEXT_SOFT))
		row.add_child(col)
		body.add_child(row)
	var w_ref := []
	var ok := U.button("¡VAMOS!", "verde", "check", 44)
	U.on_press(ok, func() -> void: w_ref[0].close(), "coin")
	body.add_child(ok)
	w_ref.append(Main.instance.modal_host.open(TITLE, body))
