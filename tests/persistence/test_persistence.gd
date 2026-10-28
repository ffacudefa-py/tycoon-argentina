extends TestCase

const PATH := "user://test_save.json"


func _cleanup() -> void:
	for p in [PATH, PATH + ".tmp", PATH + ".bak"]:
		if FileAccess.file_exists(p):
			DirAccess.remove_absolute(p)
	var da := DirAccess.open("user://")
	if da:
		for f in da.get_files():
			if f.begins_with("test_save.json.corrupt"):
				da.remove(f)


func _played_model() -> GameModel:
	var m := make_model(11)
	m.economy.reset_run(5_000_000)
	m.biz[B0]["level"] = 30
	m.invalidate()
	m.buy_upgrade(B0, "stock_ampliado")
	conquer(m, B0)
	m.zones[Z0]["share"] = 1.0
	m.buy_business(B1)
	m.zones[Z1]["share"] = 0.42
	EmployeeSystem.ensure_candidates(m, B0)
	EmployeeSystem.hire(m, B0, 0)
	m.set_company_name("Empanadas Galácticas")
	m.economy.earn(5000, "test")
	m.update_progress()
	m.missions["claimed"]["m_ventas"] = true
	return m


func test_roundtrip() -> void:
	_cleanup()
	var m := _played_model()
	var ss := SaveSystem.new(PATH)
	check(ss.save(m), "guarda: " + ss.last_error)
	var payload := ss.load_payload(data())
	check(not payload.is_empty(), "carga")
	eq(ss.last_load_source, "main")
	var m2 := make_model(99)
	m2.from_dict(payload)
	eq(m2.economy.money, m.economy.money, "dinero")
	eq(int(m2.biz[B0]["level"]), 30, "nivel")
	eq(int(m2.biz[B0]["upgrades"].get("stock_ampliado", 0)), 1, "mejoras")
	check(m2.biz[B1]["owned"], "negocios")
	eq(m2.employees.size(), m.employees.size(), "empleados")
	eq(m2.profile["company"], "Empanadas Galácticas", "perfil")
	check(m2.zones.has(Z1), "provincias")
	check(ConquestSystem.is_conquered(m2, Z0), "conquista guardada")
	near(ConquestSystem.share(m2, Z1), 0.42, 0.0001, "cuota guardada")
	check(m2.missions["claimed"].has("m_ventas"), "recompensas reclamadas")
	near(m2.derive(B0)["profit_sec"], m.derive(B0)["profit_sec"], 0.0001, "mismos valores derivados")
	var pid: String = m.data.business_by_id[B0]["products"][0]["id"]
	near(float(m2.biz[B0]["stock"][pid]), float(m.biz[B0]["stock"][pid]), 0.0001, "inventario")
	_cleanup()


func test_huge_money_survives() -> void:
	_cleanup()
	var m := make_model()
	m.economy.reset_run(0)
	m.economy.earn(987_654_321_987_654_321, "test")
	var ss := SaveSystem.new(PATH)
	ss.save(m)
	var m2 := make_model()
	m2.from_dict(ss.load_payload(data()))
	eq(m2.economy.money, 987_654_321_987_654_321, "sin pérdida de precisión")
	_cleanup()


func test_corrupt_main_falls_back_to_backup() -> void:
	_cleanup()
	var ss := SaveSystem.new(PATH)
	var m := _played_model()
	ss.save(m)            # versión A
	m.economy.earn(12345, "test")
	ss.save(m)            # versión B (A queda en .bak)
	var f := FileAccess.open(PATH, FileAccess.WRITE)
	f.store_string("{ basura total")
	f.close()
	var payload := ss.load_payload(data())
	check(not payload.is_empty(), "recupera algo")
	eq(ss.last_load_source, "bak", "desde el respaldo")
	check(not FileAccess.file_exists(PATH), "el dañado se apartó")
	_cleanup()


func test_tampered_checksum_rejected() -> void:
	_cleanup()
	var ss := SaveSystem.new(PATH)
	ss.save(_played_model())
	var f := FileAccess.open(PATH, FileAccess.READ)
	var text := f.get_as_text()
	f.close()
	text = text.replace("Empanadas", "Empanadaz")
	f = FileAccess.open(PATH, FileAccess.WRITE)
	f.store_string(text)
	f.close()
	var payload := ss.load_payload(data())
	check(payload.is_empty(), "checksum inválido y sin respaldo: partida nueva")
	eq(ss.last_load_source, "new")
	_cleanup()


func test_missing_file_is_new_game() -> void:
	_cleanup()
	var ss := SaveSystem.new(PATH)
	check(ss.load_payload(data()).is_empty(), "sin archivo")
	eq(ss.last_load_source, "new")


func test_invalid_state_is_not_saved_over_good_one() -> void:
	_cleanup()
	var ss := SaveSystem.new(PATH)
	var m := _played_model()
	check(ss.save(m), "guardado bueno")
	m.economy.money = -50   # estado imposible (simulando un bug)
	check(not ss.save(m), "no guarda un estado inválido")
	var m2 := make_model()
	m2.from_dict(ss.load_payload(data()))
	check(m2.economy.money >= 0, "el bueno sigue intacto")
	_cleanup()


func test_partial_garbage_fields_get_defaults() -> void:
	var m := make_model()
	var pid: String = m.data.business_by_id[B0]["products"][0]["id"]
	m.from_dict({"economy": {"money": "500"}, "businesses": {B0: {"level": 7, "stock": {pid: -3}, "upgrades": {"inventada": 5}}, "nada": 1}, "profile": {"company": 42}, "time": {}})
	eq(m.economy.money, 500)
	eq(int(m.biz[B0]["level"]), 7)
	eq(float(m.biz[B0]["stock"][pid]), 0.0, "stock negativo corregido")
	check(not m.biz[B0]["upgrades"].has("inventada"), "mejora desconocida descartada")
	check(m.profile["company"] is String, "nombre con tipo correcto")


func test_offline_only_automated() -> void:
	var m := make_model()
	m.update_progress()
	advance_clock(3600.0)
	var r := OfflineCalculator.apply(m)
	eq(int(r["earned"]), 0, "sin automatizar no gana offline")
	near(float(r["credited"]), 3600.0, 1.0, "midió el tiempo")


func test_offline_cap_and_stock() -> void:
	var m := make_model()
	m.economy.reset_run(1_000_000)
	m.biz[B0]["level"] = 10
	m.invalidate()
	EmployeeSystem.generate_candidates(m, B0)
	var cands: Array = m.biz[B0]["candidates"]
	for i in cands.size():
		if cands[i]["role"] == "vendedor":
			EmployeeSystem.hire(m, B0, i)
			break
	m.update_progress()
	advance_clock(20 * 3600.0)
	var r := OfflineCalculator.apply(m)
	check(r["capped"], "tope aplicado")
	near(float(r["credited"]), 8 * 3600.0, 1.0, "8 horas")
	check(int(r["earned"]) > 0, "el vendedor vendió")
	check(not r["stockouts"].is_empty(), "sin repositor se quedó sin stock")
	# Lo ganado no puede superar lo que permitía el stock que había.
	var max_possible := 0.0
	for p in m.derive(B0)["products"]:
		max_possible += float(p["cap"]) * float(p["price"])
	check(float(r["earned"]) <= max_possible * 1.01, "no concede ingresos imposibles")


func test_offline_clock_manipulation() -> void:
	var m := make_model()
	m.economy.reset_run(1_000_000)
	m.biz[B0]["level"] = 10
	m.invalidate()
	EmployeeSystem.generate_candidates(m, B0)
	EmployeeSystem.hire(m, B0, 0)
	m.update_progress()
	advance_clock(4 * 3600.0)
	var r1 := OfflineCalculator.apply(m)
	check(float(r1["credited"]) > 0.0, "primer salto paga")
	advance_clock(-4 * 3600.0)
	var r2 := OfflineCalculator.apply(m)
	eq(float(r2["credited"]), 0.0, "reloj atrás: nada")
	check(r2["clock_issue"], "detecta el problema")
	advance_clock(4 * 3600.0)
	var r3 := OfflineCalculator.apply(m)
	check(float(r3["credited"]) < 2.0, "volver a adelantar no paga dos veces")


func test_settings_persist() -> void:
	var path := "user://test_settings.cfg"
	var s := SettingsData.new(path)
	s.values["sfx_volume"] = 0.3
	s.values["vibration"] = false
	s.save()
	var s2 := SettingsData.new(path)
	s2.load()
	near(float(s2.values["sfx_volume"]), 0.3, 0.001, "volumen")
	eq(s2.values["vibration"], false, "vibración")
	DirAccess.remove_absolute(path)


## 10.0: una partida 0.7 (versión 3) empieza de cero pero conserva el perfil.
func test_migration_v4_fresh_start_keeps_profile() -> void:
	var old := {"economy": {"money": "999999", "lifetime_earned": "123456789"}, "businesses": {"puesto": {"level": 80, "owned": true}},
		"zones": {"barrio": {"paid": 0}, "centro": {"paid": 100}}, "profile": {"company": "Kiosco Pepe", "avatar": "mate", "avatars": ["emprendedor", "mate"], "photo": true, "milestones": ["algo viejo"]},
		"social": {"day": 5, "gifts_claimed": 2}, "stats": {"created": 1700000000.0, "play_time": 99999.0}, "time": {}, "prestige": {"points": 40}}
	var p := Migrations.migrate(old.duplicate(true), 3)
	eq(SaveSystem.validate_payload(p, data()), "", "la partida migrada es válida")
	var m := make_model(1, false)
	m.from_dict(p)
	eq(m.profile["company"], "Kiosco Pepe", "conserva el nombre")
	eq(m.profile["avatar"], "mate", "conserva el avatar")
	check(bool(m.profile["photo"]), "conserva la foto")
	eq(m.economy.money, int(m.data.balance["start_money"]), "plata de arranque")
	eq(m.economy.lifetime_earned, 0, "sin histórico viejo")
	eq(int(m.prestige["points"]), 0, "sin prestigio viejo")
	check(m.biz[B0]["owned"] and m.biz[B0]["closed"], "arranca con el primer negocio cerrado")
	eq(m.zones.keys(), [Z0], "sólo la primera provincia")
	eq(float(m.stats["created"]), 1700000000.0, "conserva la fecha de creación")
	eq(int(m.social["gifts_claimed"]), 2, "conserva los regalos de amigos del día")
