class_name CloudConflictModal
extends RefCounted
## Hay una partida en la nube distinta de la del teléfono (por ejemplo, se
## jugó en otro teléfono): el jugador elige cuál conservar. No se cierra sin
## elegir, así nunca se pisa una partida sin querer.


static func open(local: Dictionary, cloud: Dictionary) -> void:
	var body := U.vbox(8)
	body.add_child(U.para("Tu cuenta tiene una partida guardada en la nube que no coincide con la de este teléfono. ¿Con cuál seguís? La otra se reemplaza.", U.SIZE_SMALL, U.TEXT))
	var w_ref := []
	for side in [["En la nube", cloud, "celeste", true], ["En este teléfono", local, "verde", false]]:
		var s: Dictionary = side[1]
		var card := U.panel("Inset")
		var col := U.vbox(2)
		card.add_child(col)
		col.add_child(U.label(side[0], U.SIZE_BODY, U.TEXT, true))
		col.add_child(U.stat_row("Empresa", str(s.get("company", ""))))
		col.add_child(U.stat_row("Etapa", str(s.get("stage", 1))))
		col.add_child(U.stat_row("Plata", Fmt.money(float(s.get("money", 0)))))
		col.add_child(U.stat_row("Ganado en la historia", Fmt.money(float(s.get("lifetime", 0)))))
		col.add_child(U.stat_row("Tiempo de juego", Fmt.duration(float(s.get("play_time", 0.0)))))
		var when := float(s.get("saved_at", 0.0))
		if when > 0.0:
			col.add_child(U.stat_row("Guardada", Time.get_datetime_string_from_unix_time(int(when), true).substr(0, 16)))
		var use_cloud: bool = side[3]
		var b := U.button("Seguir con esta", side[2], "check", 34, U.SIZE_SMALL)
		U.on_press(b, func() -> void:
			w_ref[0].close()
			Cloud.resolve(use_cloud))
		col.add_child(b)
		body.add_child(card)
	w_ref.append(Main.instance.modal_host.open("Dos partidas distintas", body, false, 320))
