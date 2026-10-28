class_name PrestigeModal
extends RefCounted


static func open() -> void:
	var m := Game.m
	var gain := PrestigeSystem.pending_points(m)
	var body := U.vbox(5)
	body.add_child(U.para("Vendés tus negocios actuales para fundar un nuevo grupo empresarial. Ganás %d puntos de prestigio (+%d %% de ingresos para siempre y ventajas para comprar)." % [gain, int(gain * float(m.data.prestige_cfg["bonus_per_point"]) * 100)], U.SIZE_SMALL, U.TEXT))
	body.add_child(U.label("Se pierde:", U.SIZE_SMALL, U.RED, true))
	body.add_child(U.para("dinero, negocios, niveles, mejoras, mercadería, empleados, zonas, turbos, eventos y la etapa empresarial.", U.SIZE_SMALL, U.TEXT))
	body.add_child(U.label("Se conserva:", U.SIZE_SMALL, U.GREEN, true))
	body.add_child(U.para("puntos y ventajas de prestigio, logros, avatares, nombre, estadísticas históricas, misiones ya cumplidas, recompensa diaria y ajustes.", U.SIZE_SMALL, U.TEXT))
	var b := U.button("Fundar nuevo grupo", "violeta", "corona", 32)
	body.add_child(b)
	var w := Main.instance.modal_host.open("Nuevo grupo empresarial", body, true, 300)
	U.on_press(b, func() -> void:
		w.close()
		Main.instance.confirm("¿Seguro?", "Esta acción reinicia tu partida actual a cambio de %d puntos de prestigio. No se puede deshacer." % gain, "Fundar",
			func() -> void:
				if Main.instance.result(PrestigeSystem.perform(m)):
					Main.instance.select_business(Game.m.first_business()), true, true))
