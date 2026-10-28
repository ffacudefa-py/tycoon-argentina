class_name HardModeModal
extends RefCounted
## Elección del "Modo bien argentino" al empezar la cuenta (una sola vez).
## No se puede cerrar sin elegir; no aparece en las capturas automáticas.


static func should_show() -> bool:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--shots="):
			return false
	return not Game.m.hard.get("chosen", false)


static func open() -> void:
	var m := Game.m
	var c := HardMode.cfg(m)
	var body := U.vbox(8)
	body.add_child(U.para("Antes de arrancar: ¿cómo querés jugar? La elección queda para toda la partida.", U.SIZE_SMALL, U.TEXT))
	var normal := U.panel("Inset")
	var nv := U.vbox(2)
	normal.add_child(nv)
	nv.add_child(U.label("Modo normal", U.SIZE_BODY, U.TEXT, true))
	nv.add_child(U.para("Precios estables, sin inflación ni sobresaltos. Ideal para relajarse.", U.SIZE_SMALL, U.TEXT_SOFT))
	body.add_child(normal)
	var hard := U.panel("Inset")
	var hv := U.vbox(3)
	hard.add_child(hv)
	var top := U.hbox(6)
	top.add_child(U.icon("fuego"))
	var t := U.label("Modo bien argentino", U.SIZE_BODY, U.TEXT, true)
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(t)
	top.add_child(U.label("+%d %% ingresos" % int(round(float(c.get("income_bonus", 0.25)) * 100)), U.SIZE_SMALL, UiColors.GAIN, true))
	hv.add_child(top)
	for line in [
		"Inflación fuerte: remarcaciones cada %s." % Fmt.duration(float(c.get("inflation", {}).get("period", 360))),
		"Si debés sueldos más de %s, te hacen juicio laboral." % Fmt.duration(float(c.get("lawsuit_after", 120))),
		"Cada tanto te roban mercadería.",
		"Podés pagarle a la seguridad (coima) para que no te roben por %d min." % int(c.get("bribe_minutes", 30)),
	]:
		hv.add_child(U.para("• " + line, U.SIZE_SMALL, U.TEXT_SOFT))
	body.add_child(hard)
	var w_ref := []
	var bh := U.button("¡BIEN ARGENTINO!", "rojo", "fuego", 44)
	U.on_press(bh, func() -> void:
		HardMode.choose(m, true)
		w_ref[0].close()
		Main.instance.toast("Modo bien argentino activado. ¡Suerte, la vas a necesitar!", "info"), "coin")
	body.add_child(bh)
	var bn := U.button("Modo normal", "crema", "", 40)
	U.on_press(bn, func() -> void:
		HardMode.choose(m, false)
		w_ref[0].close())
	body.add_child(bn)
	w_ref.append(Main.instance.modal_host.open("¿Cómo querés jugar?", body, false))
