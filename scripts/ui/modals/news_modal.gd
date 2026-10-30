class_name NewsModal
extends RefCounted
## "Novedades": se muestra una vez por versión al entrar al juego (Ajustes guarda
## la última vista en news_seen). No aparece en las capturas automáticas.

const VERSION := "11.0"
const TITLE := "Novedades 11.0 · Sigma Deza"
const ITEMS := [
	["tienda", "Juego rediseñado", "Paleta cálida nueva, edificios que cambian en cada nivel, interiores, personajes y paisajes propios de cada región."],
	["regalo", "Combo, cofres y eventos", "Vendé a mano para llegar al combo x2, ganá cofres jugando y aprovechá la Vendimia, la Zafra o la Fiesta de la Yerba."],
	["alerta", "Modo bien argentino", "Elegí al empezar: +25 % de ingresos a cambio de inflación, juicios laborales, robos y coimas."],
	["flecha_arriba", "Provincias lejanas más accesibles", "Desde Cuyo en adelante, abrir y mejorar los negocios cuesta menos y los mercados son más chicos: la conquista ya no se estanca al final."],
	["mapa", "Conquistá la Argentina", "Ganale el mercado al rival de cada provincia hasta el 100 %, región por región: NOA, NEA, Cuyo, Patagonia, Pampeana y Centro."],
	["reloj", "Si venís de antes de la 10.0", "Con el juego nuevo arrancás de cero desde el NOA. Tu nombre, avatar y amigos siguen intactos."],
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
