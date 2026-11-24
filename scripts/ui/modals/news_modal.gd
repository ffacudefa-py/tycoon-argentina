class_name NewsModal
extends RefCounted
## "Novedades": se muestra una vez por versión al entrar al juego (Ajustes guarda
## la última vista en news_seen). No aparece en las capturas automáticas.

const VERSION := "15.2"
const TITLE := "Novedades 15.2"
const ITEMS := [
	["alerta", "Asalto a chancletazos", "Ahora defendés el local con la chancleta de la abuela: revoleásela a los ladrones y quedan mareados."],
	["corona", "Insignias en tu perfil", "Elegí hasta 3 insignias para mostrarle a tus amigos. Los que juegan la prueba cerrada ganan la de Pionero."],
	["candado", "Bloquear y denunciar", "Desde Amigos podés bloquear o denunciar a un jugador. Tu perfil sólo lo ven tus amigos y quien te mandó una solicitud."],
	["persona", "Solicitudes con límite", "Hasta 20 solicitudes de amistad por día, para que nadie llene de spam a los demás."],
	["estrella", "Sonidos y música propios", "Toques, subir de nivel, mejoras, fanfarrias y el tema de Coronados de Gloria, hechos especialmente para el juego."],
	["persona", "Empleados nuevos", "Seis roles nuevos (del pasante al contador) y sueldos que siguen a la ganancia del local. Los sueldos de tu partida se ajustaron solos."],
	["corona", "62 logros", "Seis categorías y cuatro rangos, con insignias nuevas."],
	["reloj", "Notificaciones", "Caja llena, eventos, versión nueva y solicitudes de amistad. Ahora siguen funcionando aunque reinicies el teléfono."],
	["candado", "Tu foto es privada", "La foto de perfil ya no se comparte sola: activala en Configuración si querés que la vean tus amigos."],
	["engranaje", "Partida más segura", "La nube guarda tu progreso cada 5 minutos mientras jugás, y \"Sincronizar ahora\" sube la copia en el momento."],
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
