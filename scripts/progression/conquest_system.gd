class_name ConquestSystem
extends RefCounted
## 10.0 "Sigma Deza": conquista de provincias por cuota de mercado.
##
## Cada provincia abierta (m.zones[zid]) guarda {share, conquered}. La cuota
## tiende a la ganancia neta por segundo del negocio de la provincia dividida
## por el tamaño de mercado, que crece con el poder del rival local:
##     objetivo = ganancia_neta / (market_size × (0,5 + 0,1 × poder))
## y se mueve hacia ese objetivo a 1/conquest_minutes por minuto (también offline):
## las provincias más avanzadas tardan más en conquistarse.
## Al llegar al 100 % la provincia queda conquistada para siempre: el rival
## cae a poder 1 y la provincia suma province_bonus a los negocios de su
## región; con la región completa, region_bonus a todos los negocios.


static func state(m: GameModel, zid: String) -> Dictionary:
	return m.zones.get(zid, {})


static func share(m: GameModel, zid: String) -> float:
	return float(state(m, zid).get("share", 0.0))


static func is_conquered(m: GameModel, zid: String) -> bool:
	return bool(state(m, zid).get("conquered", false))


static func business_conquered(m: GameModel, bid: String) -> bool:
	return is_conquered(m, m.data.zone_for_business(bid))


static func conquered_count(m: GameModel) -> int:
	var n := 0
	for zid in m.zones:
		if is_conquered(m, zid):
			n += 1
	return n


static func conquered_in_region(m: GameModel, rid: String) -> int:
	var n := 0
	for z in m.data.zones_in_region(rid):
		if is_conquered(m, z["id"]):
			n += 1
	return n


static func region_complete(m: GameModel, rid: String) -> bool:
	var zs := m.data.zones_in_region(rid)
	return not zs.is_empty() and conquered_in_region(m, rid) == zs.size()


static func regions_conquered(m: GameModel) -> int:
	var n := 0
	for r in m.data.regions:
		if region_complete(m, r["id"]):
			n += 1
	return n


## Multiplicador de ingresos por conquistas para un negocio.
static func income_mult(m: GameModel, bid: String) -> float:
	var w: Dictionary = m.data.world
	var rid: String = m.data.zone_by_id[m.data.zone_for_business(bid)]["region"]
	return (1.0 + float(w.get("province_bonus", 0.0)) * conquered_in_region(m, rid)) \
		* (1.0 + float(w.get("region_bonus", 0.0)) * regions_conquered(m))


## Ganancia por segundo que hace falta para el 100 % (según el rival hoy).
static func market_needed(m: GameModel, zid: String) -> float:
	var z: Dictionary = m.data.zone_by_id[zid]
	var power := 5
	var rid: String = z.get("rival", "")
	if m.rivals.has(rid):
		power = int(m.rivals[rid]["power"])
	return float(z["market_size"]) * (0.5 + 0.1 * power)


## Cuota a la que tiende la provincia con la ganancia actual (0..1).
static func target_share(m: GameModel, zid: String) -> float:
	var bid: String = m.data.zone_by_id[zid]["business"]
	if not m.biz.has(bid) or not m.biz[bid]["owned"]:
		return 0.0
	var d := m.derive(bid)
	var net := float(d["profit_sec"]) - float(d["salary_sec"])
	return clampf(net / maxf(market_needed(m, zid), 0.001), 0.0, 1.0)


## Cuota por segundo a la que puede subir la provincia (conquest_minutes = de 0 a 100 %).
static func share_speed(m: GameModel, zid: String) -> float:
	var mins := float(m.data.zone_by_id[zid].get("conquest_minutes", 0.0))
	return 1.0 / (mins * 60.0) if mins > 0.0 else float(m.data.world.get("share_speed", 0.01))


static func advance(m: GameModel, dt: float) -> void:
	for zid in m.zones.keys():
		var st: Dictionary = m.zones[zid]
		if st.get("conquered", false):
			continue
		var speed := share_speed(m, zid)
		var cur := float(st.get("share", 0.0))
		var tgt := target_share(m, zid)
		st["share"] = move_toward(cur, tgt, speed * dt)
		if float(st["share"]) >= 1.0:
			conquer(m, zid)


## Campaña de marketing: además de bajar al rival, suma cuota al instante.
static func campaign_push(m: GameModel, zid: String) -> void:
	if not m.zones.has(zid) or is_conquered(m, zid):
		return
	var st: Dictionary = m.zones[zid]
	st["share"] = minf(0.999, float(st.get("share", 0.0)) + float(m.data.world.get("campaign_share", 0.0)))


static func conquer(m: GameModel, zid: String) -> void:
	var st: Dictionary = m.zones[zid]
	if st.get("conquered", false):
		return
	var z: Dictionary = m.data.zone_by_id[zid]
	var region: Dictionary = m.data.region_by_id[z["region"]]
	var was_complete := region_complete(m, z["region"])
	st["share"] = 1.0
	st["conquered"] = true
	st["at"] = m.now()
	var rid: String = z.get("rival", "")
	if m.rivals.has(rid):
		m.rivals[rid]["power"] = 1
		m.rivals[rid]["trend"] = -1
	m._count("conquests", 1)
	m.invalidate()
	m.add_milestone("Conquistaste %s con %s." % [z["name"], m.data.business_by_id[z["business"]]["name"]])
	m.notify.emit("¡%s es tuya! +%d %% en %s." % [z["name"], int(round(float(m.data.world.get("province_bonus", 0.0)) * 100)), region["name"]], "good")
	m.celebrate.emit("conquest", {"zone": zid})
	Engagement.grant_chest(m, "Premio por conquistar %s." % z["name"])
	if not was_complete and region_complete(m, z["region"]):
		m.add_milestone("Conquistaste toda la región %s." % region["name"])
		m.notify.emit("¡Región %s completa! %s: +%d %% en todos tus negocios." % [region["name"], region["star_product"], int(round(float(region.get("bonus", 0.0)) * 100))], "reward")
		m.celebrate.emit("region", {"region": region["id"]})
		Engagement.grant_chest(m, "Premio por completar la región %s." % region["name"], 2)
	m.world_changed.emit()
	m.businesses_changed.emit()
