class_name ZoneModal
extends RefCounted


static func open(zid: String) -> void:
	var m := Game.m
	var z: Dictionary = m.data.zone_by_id[zid]
	var st := m.zone_status(zid)
	var body := U.vbox(5)
	body.add_child(_preview(z["map"]))
	body.add_child(U.para(z["description"], U.SIZE_SMALL, U.TEXT))
	# Lo importante en una ficha corta: qué se vende, cuánta competencia
	# hay y qué conviene abrir.
	var card := U.panel("Inset")
	var info := U.vbox(4)
	card.add_child(info)
	var dem := []
	for t in z["demand"]:
		dem.append("%s +%d %%" % [MapScreen.TAG_NAMES.get(t, t), int(round(float(z["demand"][t]) * 100))])
	info.add_child(_row("estrella", "Se vende más", ", ".join(dem), UiColors.GAIN))
	var comp := float(z["competition"])
	var level := "Baja" if comp < 0.06 else ("Media" if comp < 0.1 else "Alta")
	info.add_child(_row("alerta", "Competencia", "%s (%d %%)" % [level, int(round(comp * 100))], UiColors.GAIN if level == "Baja" else (UiColors.WARN if level == "Media" else UiColors.LOSS)))
	var rec := []
	for bid in z["recommended"]:
		rec.append(m.data.business_by_id[bid]["name"] if m.data.business_by_id.has(bid) else bid)
	info.add_child(_row("tienda", "Ideal para", ", ".join(rec), U.TEXT))
	var mine := m.businesses_in_zone(zid)
	if not mine.is_empty():
		var names := []
		for bid in mine:
			names.append(m.data.business_by_id[bid]["name"])
		info.add_child(_row("corona", "Tus negocios", ", ".join(names), U.TEXT))
	var rivals_here := []
	for r in m.data.rivals:
		if (r["zones"] as Array).has(zid):
			rivals_here.append("%s (%d/10)" % [r["name"], int(m.rivals[r["id"]]["power"])])
	if not rivals_here.is_empty():
		info.add_child(_row("persona", "Rivales", ", ".join(rivals_here), UiColors.LOSS))
	body.add_child(card)
	var w_ref := []
	if st["unlocked"]:
		body.add_child(U.para("Zona abierta: podés abrir o mudar negocios acá.", U.SIZE_SMALL, U.GREEN))
	else:
		for req in m.requirements_for_zone(zid):
			body.add_child(UiColors.requirement_row(req))
		var b := UiColors.buy_button("DESBLOQUEAR", st["cost"], func() -> void:
			if Main.instance.result(m.unlock_zone(zid)):
				w_ref[0].close(), 44)
		UiColors.set_cost(b, st["cost"], "" if st["available"] else "Falta cumplir lo de arriba")
		body.add_child(b)
	w_ref.append(Main.instance.modal_host.open(z["name"], body))


## Fila "ícono  Título: valor" con salto de línea si el valor es largo.
static func _row(icon: String, title: String, value: String, color: Color) -> Control:
	var h := U.hbox(6)
	var ic := U.icon(icon)
	ic.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	h.add_child(ic)
	var col := U.vbox(0)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	col.add_child(U.label(title, U.SIZE_SMALL, U.TEXT_SOFT))
	col.add_child(U.para(value, U.SIZE_SMALL, color))
	h.add_child(col)
	return h


## Vista de la zona: su recorte del mapa de la ciudad, ampliado a escala
## entera (x2 si entra en el modal) para que el pixel art se vea nítido.
static func _preview(r: Dictionary) -> Control:
	var at := AtlasTexture.new()
	at.atlas = U.tex("map/city_map.png")
	at.region = Rect2(r["x"], r["y"], r["w"], r["h"])
	var k := 2 if int(r["w"]) * 2 <= 280 and int(r["h"]) * 2 <= 220 else 1
	var tr := TextureRect.new()
	tr.texture = at
	tr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	tr.custom_minimum_size = Vector2(r["w"], r["h"]) * k
	tr.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return tr
