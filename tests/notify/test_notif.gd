extends TestCase
## 15.0: notificaciones para volver (NotifPlan, sin red ni plugin).

const TZ := -180       ## Argentina


func _rng() -> RandomNumberGenerator:
	var r := RandomNumberGenerator.new()
	r.seed = 5
	return r


## 2026-11-06 14:00 hora argentina.
## Partida con un negocio que vende solo (si no, no hay ganancias sin conexión)
## y dos negocios (los eventos piden un mínimo).
func _model(restock := true) -> GameModel:
	var m := make_model()
	m.economy.reset_run(1_000_000_000)
	conquer_first(m, 1)
	m.buy_business(B1)
	var roles := ["vendedor", "repositor"] if restock else ["vendedor"]
	for r in roles:
		m.employees["t_" + r] = {"id": "t_" + r, "name": "T", "role": r, "eff": 1.0, "salary": 0.0, "business": B0, "xp": 0.0, "variant": 0, "hired_at": 0.0}
	for p in m.data.business_by_id[B0]["products"]:
		m.biz[B0]["stock"][p["id"]] = 50.0
	m.invalidate()
	return m


func _afternoon() -> float:
	return float(Time.get_unix_time_from_datetime_string("2026-11-06T17:00:00"))


func test_caja_llena_al_tope_offline() -> void:
	var m := _model()
	var now := _afternoon()
	var plan := NotifPlan.plan(m, now, TZ, {}, _rng())
	var idle: Array = plan.filter(func(n: Dictionary) -> bool: return n["id"] == NotifPlan.ID_IDLE)
	eq(idle.size(), 1, "hay aviso de caja llena")
	near(float(idle[0]["at"]) - now, OfflineCalculator.cap_seconds(m), 1.0, "justo cuando se llena el tope")


func test_sin_repositor_avisa_cuando_se_acaba_el_stock() -> void:
	var m := _model(false)
	var plan := NotifPlan.plan(m, _afternoon(), TZ, {}, _rng())
	var idle: Array = plan.filter(func(n: Dictionary) -> bool: return n["id"] == NotifPlan.ID_IDLE)
	eq(idle.size(), 1, "hay aviso")
	eq(idle[0]["title"], "Te quedaste sin mercadería", "avisa del stock")
	check(float(idle[0]["at"]) - _afternoon() < OfflineCalculator.cap_seconds(m), "antes del tope")
	# Sin nadie que venda solo no hay nada que avisar.
	var m2 := make_model()
	eq(NotifPlan.idle_stop(m2)["seconds"], 0.0, "sin automatización no hay aviso")


func test_eventos_maximo_dos_por_dia_y_de_dia() -> void:
	var m := _model()
	var now := _afternoon()
	var state := {}
	var plan := NotifPlan.plan(m, now, TZ, state, _rng())
	var evs: Array = plan.filter(func(n: Dictionary) -> bool: return n.has("event"))
	check(evs.size() >= 1 and evs.size() <= 2, "uno o dos avisos de evento (%d)" % evs.size())
	for n in evs:
		var h := NotifPlan.local_hour(float(n["at"]), TZ)
		check(h >= NotifPlan.DAY_START and h < NotifPlan.DAY_END, "de día (%.1f h)" % h)
		check(m.data.event_by_id.has(n["event"]), "con un evento real")
	# Si hoy ya salieron dos, hoy no hay más.
	var today := NotifPlan.day_key(now + NotifPlan.EVENT_DELAYS[0], TZ)
	state = {"delivered": {today: 2}}
	for n in NotifPlan.plan(m, now, TZ, state, _rng()):
		if n.has("event"):
			check(NotifPlan.day_key(float(n["at"]), TZ) != today, "no pasa de dos por día")


func test_de_noche_se_corre_a_la_manana() -> void:
	var night := float(Time.get_unix_time_from_datetime_string("2026-11-07T05:00:00"))  # 02:00 local
	var at := NotifPlan.into_daytime(night, TZ)
	var h := NotifPlan.local_hour(at, TZ)
	check(h >= NotifPlan.DAY_START and h < NotifPlan.DAY_START + 1, "se corre a las 10 y algo (%.2f)" % h)


func test_al_volver_se_dispara_el_evento_anunciado() -> void:
	var now := _afternoon()
	var sched := [{"id": 2, "at": now - 60.0, "event": "e1"}, {"id": 3, "at": now + 3600.0, "event": "e2"}, {"id": 1, "at": now - 10.0}]
	var state := {}
	eq(NotifPlan.on_return(now, TZ, sched, state), "e1", "el que ya salió")
	eq(int(state["delivered"][NotifPlan.day_key(now - 60.0, TZ)]), 1, "cuenta para el día")
	eq(NotifPlan.on_return(now, TZ, [], state), "", "sin avisos no se dispara nada")
