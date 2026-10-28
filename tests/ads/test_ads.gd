extends TestCase
## Anuncios recompensados: la recompensa sólo llega con la confirmación del
## proveedor, una sola vez, y respeta esperas y límites. Usa FakeAdProvider.


func _cfg() -> AdConfig:
	return AdConfig.load_default("test")


## Reproduce el flujo de Monetization.watch con un proveedor falso.
func _watch(m: GameModel, cfg: AdConfig, fake: FakeAdProvider, offer: String, params := {}) -> Dictionary:
	var out := {"calls": 0, "result": {}}
	var b := AdRewards.begin(m, cfg, offer, params)
	if not b["ok"]:
		out["result"] = b
		return out
	var answered := [false]
	fake.show_rewarded(offer, func(earned: bool, _err: String) -> void:
		out["calls"] = int(out["calls"]) + 1
		if answered[0]:
			return
		answered[0] = true
		out["result"] = AdRewards.complete(m, b["token"], earned))
	return out


func test_config_entornos() -> void:
	var t := AdConfig.load_default("test")
	check(t.enabled, "test habilitado con IDs oficiales de prueba")
	eq(t.rewarded_unit, "ca-app-pub-3940256099942544/5224354917")
	var p := AdConfig.load_default("production")
	check(not p.enabled, "producción sin IDs reales queda desactivada")
	check(p.disabled_reason != "", "con motivo claro")
	var d := AdConfig.load_default("development")
	check(not d.enabled, "desarrollo sin anuncios")


func test_produccion_rechaza_ids_de_prueba() -> void:
	var d: Dictionary = AdConfig.load_default("test").data.duplicate(true)
	d["environments"]["production"] = {"enabled": true, "app_id": "ca-app-pub-3940256099942544~3347511713", "rewarded_unit": "ca-app-pub-3940256099942544/5224354917"}
	var c := AdConfig.from_data(d, "production")
	check(not c.enabled, "producción con IDs de prueba queda desactivada")
	check(c.disabled_reason.contains("prueba"), c.disabled_reason)
	d["environments"]["production"] = {"enabled": true, "app_id": "ca-app-pub-1111111111111111~2222222222", "rewarded_unit": "ca-app-pub-1111111111111111/3333333333"}
	check(AdConfig.from_data(d, "production").enabled, "con IDs reales se habilita")


func test_entrega_solo_con_confirmacion() -> void:
	AdRewards.cancel_session()
	var m := make_model()
	var cfg := _cfg()
	var fake := FakeAdProvider.new()
	fake.setup(cfg)
	var before := m.economy.money
	var w := _watch(m, cfg, fake, "cash")
	eq(m.economy.money, before, "mientras se muestra el anuncio no se entrega nada")
	fake.finish(true)
	check(w["result"]["granted"], "entregado al confirmar")
	check(m.economy.money > before, "sumó dinero")
	check(m.economy.money - before >= 500, "monto mínimo 500")
	eq(int(m.ads["today"]), 1)
	eq((m.ads["granted"] as Array).size(), 1, "transacción registrada")


func test_cancelado_no_entrega() -> void:
	AdRewards.cancel_session()
	var m := make_model()
	var cfg := _cfg()
	var fake := FakeAdProvider.new()
	fake.setup(cfg)
	var before := m.economy.money
	var w := _watch(m, cfg, fake, "cash")
	fake.finish(false)
	check(not w["result"]["granted"], "cerrado antes: sin recompensa")
	eq(m.economy.money, before)
	eq(int(m.ads["today"]), 0, "no cuenta para el límite")
	check(AdRewards.session.is_empty(), "sesión liberada")


func test_aviso_duplicado_no_duplica() -> void:
	AdRewards.cancel_session()
	var m := make_model()
	var cfg := _cfg()
	var fake := FakeAdProvider.new()
	fake.setup(cfg)
	var before := m.economy.money
	var w := _watch(m, cfg, fake, "cash")
	fake.finish(true, true)
	eq(int(w["calls"]), 2, "el proveedor avisó dos veces")
	var once := m.economy.money - before
	check(once > 0, "once > 0")
	# Aunque llegue otro complete() con el mismo token, no se paga de nuevo.
	var token: String = (m.ads["granted"] as Array)[0]
	var r := AdRewards.complete(m, token, true)
	check(not r["granted"], "token repetido rechazado")
	eq(m.economy.money - before, once, "se pagó una sola vez")


func test_una_sesion_a_la_vez() -> void:
	AdRewards.cancel_session()
	var m := make_model()
	var cfg := _cfg()
	var a := AdRewards.begin(m, cfg, "cash")
	check(a["ok"], "a['ok']")
	var b := AdRewards.begin(m, cfg, "turbo")
	check(not b["ok"], "doble toque / segunda oferta bloqueada mientras hay una en curso")
	AdRewards.cancel_session()


func test_token_ajeno_no_entrega() -> void:
	AdRewards.cancel_session()
	var m := make_model()
	var before := m.economy.money
	var r := AdRewards.complete(m, "inventado", true)
	check(not r["granted"], "not r['granted']")
	eq(m.economy.money, before)


func test_espera_y_limite_diario() -> void:
	AdRewards.cancel_session()
	var m := make_model()
	var cfg := _cfg()
	var fake := FakeAdProvider.new()
	fake.setup(cfg)
	_watch(m, cfg, fake, "cash")
	fake.finish(true)
	var again := AdRewards.begin(m, cfg, "cash")
	check(not again["ok"], "en espera")
	check(String(again["msg"]).begins_with("Disponible en"), again["msg"])
	advance_clock(301)
	check(AdRewards.begin(m, cfg, "cash")["ok"], "pasada la espera vuelve a estar")
	AdRewards.cancel_session()
	m.ads["today"] = cfg.daily_limit()
	var lim := AdRewards.begin(m, cfg, "turbo")
	check(not lim["ok"], "límite diario")
	advance_clock(86400)
	check(AdRewards.begin(m, cfg, "turbo")["ok"], "al día siguiente se renueva")
	AdRewards.cancel_session()


func test_turbo_y_reposicion() -> void:
	AdRewards.cancel_session()
	var m := make_model()
	var cfg := _cfg()
	var fake := FakeAdProvider.new()
	fake.setup(cfg)
	_watch(m, cfg, fake, "turbo")
	fake.finish(true)
	eq(m.boosts.size(), 1, "turbo activo")
	near(float(m.boosts[0]["remaining"]), 600.0, 0.01)
	fake.load_ad()
	for p in m.derive(B0)["products"]:
		m.biz[B0]["stock"][p["id"]] = 0.0
	var money := m.economy.money
	_watch(m, cfg, fake, "restock", {"business": B0})
	fake.finish(true)
	for p in m.derive(B0)["products"]:
		near(float(m.biz[B0]["stock"][p["id"]]), float(p["cap"]), 0.01, "depósito lleno")
	eq(m.economy.money, money, "gratis")


func test_extra_diario_requiere_haber_reclamado() -> void:
	AdRewards.cancel_session()
	var m := make_model()
	var cfg := _cfg()
	check(not AdRewards.begin(m, cfg, "daily_extra")["ok"], "sin reclamar la diaria no se puede")
	ProgressionSystem.claim_daily_reward(m)
	var fake := FakeAdProvider.new()
	fake.setup(cfg)
	var before := m.economy.money
	_watch(m, cfg, fake, "daily_extra")
	fake.finish(true)
	check(m.economy.money > before, "pagó el extra")
	check(not AdRewards.begin(m, cfg, "daily_extra")["ok"], "una vez por día")


func test_registro_sobrevive_al_guardado() -> void:
	AdRewards.cancel_session()
	var m := make_model()
	var cfg := _cfg()
	var fake := FakeAdProvider.new()
	fake.setup(cfg)
	_watch(m, cfg, fake, "cash")
	fake.finish(true)
	var m2 := make_model()
	m2.from_dict(JSON.parse_string(JSON.stringify(m.to_dict())))
	eq((m2.ads["granted"] as Array).size(), 1, "registro persistido")
	check(not AdRewards.begin(m2, cfg, "cash")["ok"], "la espera también se guarda")
	AdRewards.cancel_session()


func test_proveedor_sin_anuncio_no_entrega() -> void:
	var fake := FakeAdProvider.new()
	fake.fail_load()
	var got := [null]
	fake.show_rewarded("cash", func(earned: bool, err: String) -> void: got[0] = [earned, err])
	check(not got[0][0], "sin anuncio cargado no hay recompensa")
	check(got[0][1] != "", "con mensaje")
	var off := NotConfiguredAdProvider.new("desactivado")
	check(not off.is_available(), "not off.is_available()")
