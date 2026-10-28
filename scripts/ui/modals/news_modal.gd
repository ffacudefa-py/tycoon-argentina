class_name NewsModal
extends RefCounted
## "Novedades": se muestra una vez por versión al entrar al juego (Ajustes guarda
## la última vista en news_seen). No aparece en las capturas automáticas.

const VERSION := "10.0"
const TITLE := "Novedades 10.0 · Sigma Deza"
const ITEMS := [
	["mapa", "¡A conquistar la Argentina!", "El objetivo ahora es dominar las 24 provincias, región por región: NOA, NEA, Cuyo, Patagonia, Pampeana y Centro."],
	["estrella", "Productos de cada provincia", "Cada provincia tiene su negocio: algodón en Santiago del Estero, papas andinas en Jujuy, Malbec en Mendoza, yerba en Misiones, medialunas en CABA…"],
	["grafico", "Cuota de mercado", "Ganale el mercado al rival local hasta el 100 % y la provincia es tuya: +10 % en la región. Con la región completa, su producto estrella te da +25 % en todo."],
	["bandera", "Mapa nuevo", "Primero ves el país; tocá una región para entrar y ver sus provincias."],
	["reloj", "Empezás de cero", "Con el juego nuevo, todos arrancan desde el NOA. Tu nombre, avatar y amigos siguen intactos."],
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
