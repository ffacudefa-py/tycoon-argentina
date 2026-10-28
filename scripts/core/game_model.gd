class_name GameModel
extends RefCounted
## Estado completo de una partida + todas las acciones del jugador.
##
## No depende de nodos, escenas ni de la interfaz: la UI llama acciones
## (buy_levels, restock, hire...) y escucha señales. Los tests crean un
## GameModel con un reloj falso y lo simulan sin abrir ninguna ventana.
##
## Los subsistemas (empleados, eventos, rivales, misiones, prestigio, offline)
## son módulos de funciones estáticas que operan sobre este estado, para que
## todo lo que se guarda viva en un solo lugar serializable.

signal money_changed(money: int, delta: int)
signal business_changed(id: String)
signal businesses_changed
signal sale(id: String, revenue: int)
signal notify(text: String, kind: String)            ## info / good / bad / reward
signal celebrate(kind: String, info: Dictionary)     ## para efectos visuales y sonido
signal progress_changed                              ## misiones, logros, diarias
signal events_changed
signal stage_changed(stage: int)
signal world_changed                                  ## zonas y rivales
signal profile_changed

const SAVE_VERSION := 1

var data: GameData
var clock: Callable
var rng := RandomNumberGenerator.new()
var economy := Economy.new()

var biz := {}                 ## id -> estado del negocio (Dictionary)
var employees := {}           ## emp_id -> empleado
var zones := {}               ## provincia abierta -> {"paid", "share", "conquered", "at"}
var counters := {}            ## métricas acumuladas (ventas, reposiciones...)
var stats := {}               ## tiempo de juego, récords
var profile := {}
var missions := {}
var daily_missions := {}
var achievements := {}        ## id -> unix time de desbloqueo
var daily_reward := {}
var ads := {}                 ## registro de recompensas por anuncio (ver AdRewards)
var social := {}              ## regalos de amigos abiertos hoy (ver FriendLogic)
var events := {}
var inflation := {}
var rivals := {}
var rival_log: Array = []
var prestige := {}
var boosts: Array = []
var tutorial := {}
var time_state := {}
var salary_due := 0.0
var salary_debt := 0
var next_employee_id := 1
var stage := 1
var hard := HardMode.default_state()  ## modo bien argentino (ver HardMode)
var engage := Engagement.default_state()  ## combo, cofres e hitos (ver Engagement)
var tz_bias_minutes := 0           ## zona horaria local, para saber cuándo cambia el día

var _derived := {}
var _dirty := true
var _progress_timer := 0.0


func _init(p_data: GameData = null, p_clock: Callable = Callable()) -> void:
	data = p_data if p_data != null else GameData.load_default()
	clock = p_clock if p_clock.is_valid() else func() -> float: return Time.get_unix_time_from_system()
	economy.clock = clock
	economy.max_money = int(data.balance["max_money"])
	economy.changed.connect(_on_money_changed)
	rng.randomize()
	tz_bias_minutes = int(Time.get_time_zone_from_system().get("bias", 0))
	new_game()


func _on_money_changed(money: int, delta: int) -> void:
	money_changed.emit(money, delta)


func now() -> float:
	return clock.call()


# ---------------------------------------------------------------------------
# Partida nueva / prestigio
# ---------------------------------------------------------------------------

func new_game() -> void:
	prestige = {"points": 0, "spent": 0, "count": 0, "perks": {}}
	achievements = {}
	profile = {"company": "Mi Emprendimiento", "avatar": "emprendedor", "avatars": _default_avatars(), "milestones": [],
		"photo": false, "banner": false}
	counters = {}
	stats = {"play_time": 0.0, "best_income": 0.0, "created": now()}
	daily_reward = {"last_day": -1, "index": 0}
	ads = {"granted": [], "day": -1, "today": 0, "cooldowns": {}}
	social = {"day": -1, "gifts_claimed": 0}
	tutorial = {"step": 0, "done": false}
	hard = HardMode.default_state()
	engage = Engagement.default_state()
	missions = {"main_index": 0, "completed": {}, "claimed": {}}
	daily_missions = {"day": -1, "list": [], "baseline": {}, "completed": {}, "claimed": {}}
	time_state = {"last_active": now(), "max_seen": now()}
	economy.lifetime_earned = 0
	_reset_run()
	# Primera partida: el primer negocio arranca cerrado y sin mercadería; la
	# misión guiada enseña abrir → comprar mercadería → vender.
	var first := first_business()
	biz[first]["closed"] = true
	for pid in biz[first]["stock"]:
		biz[first]["stock"][pid] = 0.0


func first_business() -> String:
	return data.first_business()


## Reinicia lo que se pierde al fundar un nuevo grupo (y al empezar).
func _reset_run() -> void:
	biz = {}
	for def in data.businesses:
		biz[def["id"]] = _new_business_state(def["id"])
	employees = {}
	zones = {}
	boosts = []
	hard["protected"] = {}
	hard["debt_time"] = 0.0
	salary_due = 0.0
	salary_debt = 0
	stage = 1
	events = {"active": [], "next_in": float(data.events_cfg["first_event_delay"]), "last_id": ""}
	inflation = {"cost_index": 1.0, "price_index": 1.0, "next_in": float(data.events_cfg["inflation"]["period"]), "announced": false, "price_in": -1.0}
	rivals = {}
	for r in data.rivals:
		rivals[r["id"]] = {"power": int(r["start_power"]), "trend": 0, "last": "", "timer": 0.0}
	rival_log = []
	var start_money := int(data.balance["start_money"])
	var seed_lvl := perk_level("capital_semilla")
	if seed_lvl > 0:
		start_money = maxi(start_money, int(data.perk_by_id["capital_semilla"]["effects"]["start_money"][seed_lvl - 1]))
	economy.reset_run(start_money)
	_own_business(first_business(), float(data.balance["start_stock_fraction"]))
	var fr := perk_level("franquicia")
	if fr > 0:
		for extra in data.perk_by_id["franquicia"]["effects"]["start_businesses"][fr - 1]:
			if biz.has(extra):
				_own_business(extra, 1.0)
	invalidate()


func _new_business_state(id: String) -> Dictionary:
	var def: Dictionary = data.business_by_id[id]
	var stock := {}
	for p in def["products"]:
		stock[p["id"]] = 0.0
	return {
		"id": id, "owned": false, "level": 0, "zone": data.zone_for_business(id),
		"upgrades": {}, "stock": stock, "orders": {},
		"progress": 0.0, "running": false, "carry": 0.0,
		"invested": 0, "earned": 0, "sales": 0,
		"candidates": [], "cand_timer": 0.0, "reroll_cd": 0.0,
		"stockout": false, "closed": false,
	}


## Cada negocio vive en su provincia: abrirlo abre la provincia (cuota 0 %).
func _own_business(id: String, stock_fraction: float) -> void:
	var s: Dictionary = biz[id]
	s["owned"] = true
	s["level"] = 1
	s["zone"] = data.zone_for_business(id)
	if not zones.has(s["zone"]):
		zones[s["zone"]] = {"paid": 0, "share": 0.0, "conquered": false}
	invalidate()
	var d := derive(id)
	for p in d["products"]:
		s["stock"][p["id"]] = float(p["cap"]) * stock_fraction


func _default_avatars() -> Array:
	var out := []
	for a in data.avatars:
		if a.get("unlocked", false):
			out.append(a["id"])
	return out


# ---------------------------------------------------------------------------
# Valores derivados (con caché)
# ---------------------------------------------------------------------------

func invalidate() -> void:
	_dirty = true


func derive(id: String) -> Dictionary:
	if _dirty:
		_derived.clear()
		_dirty = false
	if not _derived.has(id):
		_derived[id] = _compute(id)
	return _derived[id]


func _compute(id: String) -> Dictionary:
	var def: Dictionary = data.business_by_id[id]
	var s: Dictionary = biz[id]
	var bal: Dictionary = data.balance
	var level := maxi(1, int(s["level"]))
	var mods := {"capacity": 0.0, "cost_reduction": 0.0, "speed": 0.0, "units": 0.0, "revenue": 0.0, "slots": 0.0, "employee_eff": 0.0, "salary_reduction": 0.0}
	for uid in s["upgrades"]:
		var u = data.upgrade_by_id.get(uid)
		if u == null:
			continue
		for e in u["effects"]:
			mods[e["stat"]] += float(e["value"]) * int(s["upgrades"][uid])

	var ms_speed := 1.0
	var ms_slots := 0
	var next_ms := 0
	for ms in bal["milestones"]:
		if level >= int(ms["level"]):
			ms_speed *= float(ms["speed"])
			ms_slots += int(ms["slots"])
		elif next_ms == 0:
			next_ms = int(ms["level"])
	var slots := mini(int(bal["max_slots"]), int(bal["base_slots"]) + ms_slots + int(mods["slots"]))

	# Empleados
	var team := employees_of(id)
	var debt_mult := float(bal["salary_debt_efficiency"]) if salary_debt > 0 else 1.0
	var perk_eff := float(data.perk_by_id["reclutadora"]["effects"]["employee_eff"]) * perk_level("reclutadora")
	var team_eff_total := 0.0
	for e in team:
		team_eff_total += float(data.role_by_id[e["role"]]["effects"].get("team_eff", 0.0)) * float(e["eff"])
	var auto_sell := false
	var auto_restock := false
	var manager := false
	var speed_emp := 0.0
	var revenue_emp := 0.0
	var restock_emp := 0.0
	var salary := 0.0
	for e in team:
		var role: Dictionary = data.role_by_id[e["role"]]
		var own_team := float(role["effects"].get("team_eff", 0.0)) * float(e["eff"])
		var eff: float = employee_efficiency(e) * (1.0 + mods["employee_eff"] + perk_eff + team_eff_total - own_team) * debt_mult
		auto_sell = auto_sell or role.get("auto_sell", false)
		auto_restock = auto_restock or role.get("auto_restock", false)
		manager = manager or role.get("manager", false)
		speed_emp += float(role["effects"].get("speed", 0.0)) * eff
		revenue_emp += float(role["effects"].get("revenue", 0.0)) * eff
		restock_emp += float(role["effects"].get("restock_speed", 0.0)) * eff
		salary += float(e["salary"])
	salary *= maxf(0.0, 1.0 - mods["salary_reduction"])

	# Directores regionales de la misma región (de cualquier negocio)
	var director_bonus := 0.0
	var region: String = data.zone_by_id[s["zone"]]["region"]
	for e in employees.values():
		if e["role"] == "director" and biz.has(e["business"]) and data.zone_by_id[biz[e["business"]]["zone"]]["region"] == region:
			director_bonus += float(data.role_by_id["director"]["effects"]["zone_revenue"]) * employee_efficiency(e) * debt_mult

	# Zona y competencia
	var zone: Dictionary = data.zone_by_id.get(s["zone"], data.zones[0])
	var zone_demand := 0.0
	for t in def["tags"]:
		zone_demand = maxf(zone_demand, float(zone["demand"].get(t, 0.0)))
	var competition := RivalSystem.competition_for(self, id)
	var zone_mult: float = (1.0 + zone_demand) * (1.0 - competition)

	var ev := EventSystem.modifiers_for(self, id)
	# income_rate (0,8) achica precios y costo de mercadería por igual: el margen
	# se mantiene y la ganancia neta baja 20 %.
	var rate := income_rate()
	var income_mult := prestige_multiplier() * boost_multiplier() * rate * ConquestSystem.income_mult(self, id) * HardMode.income_mult(self)
	var price_index := float(inflation["price_index"]) if inflation_active() else 1.0
	var cost_index := float(inflation["cost_index"]) if inflation_active() else 1.0

	var units: float = float(level) * (1.0 + mods["units"])
	var speed_mult: float = ms_speed * (1.0 + mods["speed"] + speed_emp)
	var base_cycle: float = float(def["cycle"]) / speed_mult
	var cycle := maxf(float(bal["min_cycle"]), base_cycle / float(ev["speed"]))
	var price_mult: float = (1.0 + mods["revenue"] + revenue_emp + director_bonus) * zone_mult * float(ev["revenue"]) * income_mult * price_index
	var cost_mult: float = maxf(0.5, 1.0 - mods["cost_reduction"]) * float(ev["cost"]) * cost_index * rate
	var stock_span: float = maxf(float(bal["stock_cycles"]), float(bal["stock_seconds"]) / maxf(base_cycle, float(bal["min_cycle"]))) * (1.0 + mods["capacity"])

	var products := []
	var revenue_cycle := 0.0
	var cost_cycle := 0.0
	for p in def["products"]:
		var dem: float = float(ev["demand"].get(p["id"], 1.0))
		var u: float = units * float(p["share"]) * dem
		var item := {
			"id": p["id"], "name": p["name"], "icon": p["icon"],
			"u": u,
			"cap": ceilf(units * float(p["share"]) * stock_span),
			"price": float(p["price"]) * price_mult,
			"cost": float(p["cost"]) * cost_mult,
			"base_cost": float(p["cost"]),
			"demand_mult": dem,
		}
		revenue_cycle += u * item["price"]
		cost_cycle += u * item["cost"]
		products.append(item)

	var automation := 0
	if auto_sell:
		automation = 2 if auto_restock else 1
		if manager:
			automation = 3
	var tier := 0
	var tiers: Array = bal["visual_tiers"]
	for i in tiers.size():
		if level >= int(tiers[i]):
			tier = i
	return {
		"units": units, "cycle": cycle, "price_mult": price_mult, "cost_mult": cost_mult,
		"products": products, "revenue_cycle": revenue_cycle, "cost_cycle": cost_cycle,
		"revenue_sec": revenue_cycle / cycle, "profit_sec": (revenue_cycle - cost_cycle) / cycle,
		"restock_time": float(def["restock_time"]) / (1.0 + restock_emp),
		"auto_sell": auto_sell, "auto_restock": auto_restock, "manager": manager,
		"automation": automation, "slots": slots, "salary_sec": salary,
		"next_milestone": next_ms, "tier": tier, "zone_mult": zone_mult,
		"zone_demand": zone_demand, "competition": competition,
		"event_revenue": ev["revenue"], "event_speed": ev["speed"], "event_cost": ev["cost"],
		"mods": mods, "team_size": team.size(),
	}


## La inflación sólo existe en el modo bien argentino.
func inflation_active() -> bool:
	return HardMode.on(self)


## Ritmo global de ganancias (balance.income_rate, 0,8 desde la 0.7.0).
func income_rate() -> float:
	return float(data.balance.get("income_rate", 1.0))


## Saldo neto: efectivo menos sueldos atrasados. Es lo que muestra la barra
## superior; queda negativo mientras se deben sueldos.
func net_balance() -> int:
	return economy.money - salary_debt


func employee_efficiency(e: Dictionary) -> float:
	return float(e["eff"]) * (1.0 + float(data.employees_cfg["xp_level_bonus"]) * (EmployeeSystem.xp_level(self, e) - 1))


func employees_of(id: String) -> Array:
	var out := []
	for e in employees.values():
		if e["business"] == id:
			out.append(e)
	return out


func perk_level(id: String) -> int:
	return int(prestige.get("perks", {}).get(id, 0))


func prestige_multiplier() -> float:
	var per_point := float(data.prestige_cfg["bonus_per_point"])
	var inv := float(data.perk_by_id["inversores"]["effects"]["income"]) * perk_level("inversores")
	return (1.0 + per_point * float(prestige.get("points", 0))) * (1.0 + inv)


## Los turbos no se apilan: rige el mayor (y uno nuevo extiende la duración).
func boost_multiplier() -> float:
	var best := 1.0
	for bo in boosts:
		best = maxf(best, float(bo["mult"]))
	return minf(float(data.balance["max_boost_multiplier"]), best)


func level_cost_multiplier() -> float:
	return maxf(0.5, 1.0 - float(data.perk_by_id["contactos"]["effects"]["level_cost"]) * perk_level("contactos"))


# ---------------------------------------------------------------------------
# Agregados de la economía
# ---------------------------------------------------------------------------

func owned_ids() -> Array:
	var out := []
	for def in data.businesses:
		if biz[def["id"]]["owned"]:
			out.append(def["id"])
	return out


## Ganancia neta estimada por segundo de lo que funciona solo (ventas
## automáticas - mercadería - sueldos). Es la que usan las recompensas.
func income_per_sec() -> float:
	return maxf(0.0, net_per_sec())


## Como income_per_sec pero puede ser negativo (sueldos mayores que la ganancia).
## Sólo para mostrar; los premios y costos se basan en income_per_sec.
func net_per_sec() -> float:
	return gross_profit_per_sec() - salaries_per_sec()


func gross_profit_per_sec() -> float:
	var total := 0.0
	for id in owned_ids():
		var d := derive(id)
		if d["auto_sell"] and (d["auto_restock"] or has_stock(id)):
			total += d["profit_sec"]
	return total


func revenue_per_sec() -> float:
	var total := 0.0
	for id in owned_ids():
		var d := derive(id)
		if d["auto_sell"] and (d["auto_restock"] or has_stock(id)):
			total += d["revenue_sec"]
	return total


func stock_cost_per_sec() -> float:
	var total := 0.0
	for id in owned_ids():
		var d := derive(id)
		if d["auto_sell"] and (d["auto_restock"] or has_stock(id)):
			total += d["cost_cycle"] / d["cycle"]
	return total


func salaries_per_sec() -> float:
	var total := 0.0
	for id in owned_ids():
		total += derive(id)["salary_sec"]
	return total


func has_stock(id: String) -> bool:
	for v in biz[id]["stock"].values():
		if float(v) >= 0.0001:
			return true
	return false


func stock_ratio(id: String) -> float:
	var d := derive(id)
	var have := 0.0
	var cap := 0.0
	for p in d["products"]:
		have += float(biz[id]["stock"].get(p["id"], 0.0))
		cap += float(p["cap"])
	return clampf(have / cap, 0.0, 1.0) if cap > 0.0 else 0.0


## Patrimonio = efectivo + valor de los negocios + valor de las zonas.
## Valor de un negocio = 50 % de lo invertido en él (compra, niveles y mejoras)
## + mercadería en stock a precio de costo base. Cada activo se cuenta una vez.
func net_worth() -> float:
	var total := float(economy.money)
	for id in owned_ids():
		var s: Dictionary = biz[id]
		total += 0.5 * float(s["invested"])
		var def: Dictionary = data.business_by_id[id]
		for p in def["products"]:
			total += float(s["stock"].get(p["id"], 0.0)) * float(p["cost"])
	for z in zones.values():
		total += 0.5 * float(z["paid"])
	return total


func most_profitable() -> String:
	var best := ""
	var best_v := -1.0
	for id in owned_ids():
		var v: float = derive(id)["profit_sec"]
		if v > best_v:
			best_v = v
			best = id
	return best


func total_upgrades() -> int:
	var n := 0
	for id in owned_ids():
		for v in biz[id]["upgrades"].values():
			n += int(v)
	return n


# ---------------------------------------------------------------------------
# Acciones: negocios
# ---------------------------------------------------------------------------

static func ok(msg := "") -> Dictionary:
	return {"ok": true, "msg": msg}


static func fail(msg: String) -> Dictionary:
	return {"ok": false, "msg": msg}


## Abre el negocio (sólo el primero empieza cerrado en la primera partida).
func open_business(id: String) -> Dictionary:
	var s: Dictionary = biz[id]
	if not s.get("closed", false):
		return fail("Ya está abierto.")
	s["closed"] = false
	add_milestone("Abriste %s en %s." % [data.business_by_id[id]["name"], data.zone_by_id[s["zone"]]["name"]])
	celebrate.emit("unlock", {"business": id})
	business_changed.emit(id)
	return ok()


## Premio de un paso del tutorial guiado: se entrega una sola vez.
func grant_tutorial_reward(step: int, reward: Dictionary) -> bool:
	var given: Dictionary = tutorial.get("rewarded", {})
	if given.has(str(step)) or reward.is_empty():
		return false
	given[str(step)] = true
	tutorial["rewarded"] = given
	ProgressionSystem.grant(self, reward, "tutorial")
	return true


## Vender a mano: arranca un ciclo si el negocio no está automatizado.
func tap_sell(id: String) -> Dictionary:
	var s: Dictionary = biz[id]
	if not s["owned"]:
		return fail("No tenés este negocio.")
	if s.get("closed", false):
		return fail("Está cerrado: tocá ABRIR.")
	if s["running"]:
		return fail("Ya estás atendiendo.")
	if not has_stock(id):
		return fail("¡Sin mercadería! Reponé para seguir vendiendo.")
	s["running"] = true
	s["progress"] = 0.0
	business_changed.emit(id)
	return ok()


func level_cost(id: String, n: int) -> int:
	var def: Dictionary = data.business_by_id[id]
	var level := int(biz[id]["level"])
	if n <= 0:
		return 0
	var g := float(def["level_cost_growth"])
	var first := float(def["level_cost_base"]) * pow(g, level - 1) * level_cost_multiplier()
	return Economy.to_int_ceil(first * (pow(g, n) - 1.0) / (g - 1.0))


func max_affordable_levels(id: String) -> int:
	var def: Dictionary = data.business_by_id[id]
	var level := int(biz[id]["level"])
	var room := int(def["max_level"]) - level
	if room <= 0:
		return 0
	var g := float(def["level_cost_growth"])
	var first := float(def["level_cost_base"]) * pow(g, level - 1) * level_cost_multiplier()
	var n := int(floor(log(float(economy.money) * (g - 1.0) / first + 1.0) / log(g)))
	n = clampi(n, 0, room)
	while n > 0 and level_cost(id, n) > economy.money:
		n -= 1
	return n


func buy_levels(id: String, n: int) -> Dictionary:
	var s: Dictionary = biz[id]
	var def: Dictionary = data.business_by_id[id]
	if not s["owned"]:
		return fail("No tenés este negocio.")
	n = mini(n, int(def["max_level"]) - int(s["level"]))
	if n <= 0:
		return fail("Nivel máximo alcanzado.")
	var cost := level_cost(id, n)
	if not economy.spend(cost, "niveles"):
		return fail("No te alcanza la plata.")
	var before_tier: int = derive(id)["tier"]
	s["level"] = int(s["level"]) + n
	s["invested"] = Economy.sat_add(int(s["invested"]), cost)
	_count("levels_bought", n)
	_count("purchases", n)
	invalidate()
	var d := derive(id)
	if d["tier"] > before_tier:
		celebrate.emit("tier", {"business": id, "tier": d["tier"]})
		notify.emit("¡%s creció! Nuevo aspecto y más velocidad." % def["name"], "good")
		add_milestone("%s llegó a nivel %d." % [def["name"], s["level"]])
	else:
		celebrate.emit("level", {"business": id})
	EmployeeSystem.ensure_candidates(self, id)
	business_changed.emit(id)
	return ok()


func upgrade_cost(id: String, uid: String) -> int:
	var def: Dictionary = data.business_by_id[id]
	var u: Dictionary = data.upgrade_by_id[uid]
	var lvl := int(biz[id]["upgrades"].get(uid, 0))
	return Economy.to_int_ceil(float(def["level_cost_base"]) * float(u["cost_factor"]) * pow(float(u["cost_growth"]), lvl) * level_cost_multiplier())


func upgrade_name(id: String, uid: String) -> String:
	return data.business_by_id[id].get("upgrade_names", {}).get(uid, uid.capitalize())


## Estado completo de una mejora para la interfaz.
func upgrade_status(id: String, uid: String) -> Dictionary:
	var s: Dictionary = biz[id]
	var u: Dictionary = data.upgrade_by_id[uid]
	var lvl := int(s["upgrades"].get(uid, 0))
	var maxl := int(u["max_level"])
	var reasons := []
	if int(s["level"]) < int(u["requires_level"]):
		reasons.append("Requiere nivel %d del negocio" % int(u["requires_level"]))
	for req in u["requires"]:
		if int(s["upgrades"].get(req, 0)) < int(u["requires"][req]):
			reasons.append("Requiere %s (nivel %d)" % [upgrade_name(id, req), int(u["requires"][req])])
	var cost := upgrade_cost(id, uid) if lvl < maxl else 0
	return {
		"level": lvl, "max": maxl, "maxed": lvl >= maxl, "cost": cost,
		"locked": not reasons.is_empty(), "reasons": reasons,
		"affordable": economy.can_afford(cost),
	}


func buy_upgrade(id: String, uid: String) -> Dictionary:
	if not biz[id]["owned"]:
		return fail("No tenés este negocio.")
	var st := upgrade_status(id, uid)
	if st["maxed"]:
		return fail("Esta mejora ya está al máximo.")
	if st["locked"]:
		return fail(st["reasons"][0])
	if not economy.spend(st["cost"], "mejoras"):
		return fail("No te alcanza la plata.")
	var s: Dictionary = biz[id]
	s["upgrades"][uid] = int(st["level"]) + 1
	s["invested"] = Economy.sat_add(int(s["invested"]), st["cost"])
	_count("upgrades_bought", 1)
	_count("purchases", 1)
	invalidate()
	celebrate.emit("upgrade", {"business": id, "upgrade": uid})
	if uid == "sucursal":
		add_milestone("Abriste una sucursal de %s." % data.business_by_id[id]["name"])
	business_changed.emit(id)
	return ok("%s nivel %d" % [upgrade_name(id, uid), int(st["level"]) + 1])


## Presupuesto para llenar el depósito: {"total": int, "items": {pid: unidades}}.
func restock_quote(id: String) -> Dictionary:
	var s: Dictionary = biz[id]
	var d := derive(id)
	var total := 0.0
	var items := {}
	for p in d["products"]:
		var pending := float(s["orders"].get(p["id"], {}).get("units", 0.0))
		var missing := float(p["cap"]) - float(s["stock"].get(p["id"], 0.0)) - pending
		if missing > 0.01:
			items[p["id"]] = missing
			total += missing * float(p["cost"])
	return {"total": Economy.to_int_ceil(total), "items": items, "exact": total}


## Compra mercadería. Si no alcanza para todo, compra la parte proporcional.
func restock(id: String, automatic := false) -> Dictionary:
	var s: Dictionary = biz[id]
	if not s["owned"]:
		return fail("No tenés este negocio.")
	var q := restock_quote(id)
	if q["items"].is_empty() or q["total"] <= 0:
		return fail("El depósito ya está lleno.")
	var fraction := 1.0
	var pay: int = q["total"]
	var d := derive(id)
	if economy.money < pay:
		pay = economy.money
		fraction = float(pay) / float(q["exact"])
		if pay <= 0:
			return _emergency_stock(id, d)
	if not economy.spend(pay, "mercadería"):
		return fail("No te alcanza para reponer.")
	for pid in q["items"]:
		var units: float = q["items"][pid] * minf(fraction, 1.0)
		if s["orders"].has(pid):
			s["orders"][pid]["units"] = float(s["orders"][pid]["units"]) + units
		else:
			s["orders"][pid] = {"units": units, "eta": d["restock_time"]}
	s["invested"] = int(s["invested"])  # la mercadería se valúa aparte (stock)
	_count("restock_count", 1)
	if EventSystem.has_effect(self, id, "cost", true):
		_count("discount_restocks", 1)
	if not automatic:
		celebrate.emit("restock", {"business": id})
	business_changed.emit(id)
	return ok()


## Red de seguridad contra atascos: sin plata y sin mercadería en el puesto,
## el mayorista fía un poco de stock para volver a arrancar.
func _emergency_stock(id: String, d: Dictionary) -> Dictionary:
	var s: Dictionary = biz[id]
	if id != first_business() or has_stock(id) or not s["orders"].is_empty():
		return fail("No te alcanza para reponer.")
	for p in d["products"]:
		s["orders"][p["id"]] = {"units": maxf(1.0, float(p["cap"]) * 0.1), "eta": d["restock_time"]}
	_count("restock_count", 1)
	notify.emit("El mayorista te fió un poco de mercadería. ¡A vender!", "info")
	business_changed.emit(id)
	return ok("fiado")


func pending_order_eta(id: String) -> float:
	var eta := 0.0
	for o in biz[id]["orders"].values():
		eta = maxf(eta, float(o["eta"]))
	return eta


## Requisitos con progreso, para mostrar barras ("Conquistá Jujuy: 42 %").
## Cada uno: {text, current, target, met, money (si se muestra como plata)}.
func requirements_for_business(id: String) -> Array:
	var u: Dictionary = data.business_by_id[id]["unlock"]
	var out := []
	if stage < int(u["stage"]):
		out.append(_stage_requirement(int(u["stage"])))
	var req = u.get("requires")
	if req != null and req.get("conquer", false):
		var zid := data.zone_for_business(req["business"])
		var sh := ConquestSystem.share(self, zid)
		out.append({"text": "Conquistá %s" % data.zone_by_id[zid]["name"],
			"current": floorf(sh * 100.0), "target": 100.0, "met": ConquestSystem.is_conquered(self, zid), "money": false, "percent": true})
	elif req != null:
		var rs: Dictionary = biz[req["business"]]
		var lvl := int(rs["level"]) if rs["owned"] else 0
		out.append({"text": "%s nivel %d" % [data.business_by_id[req["business"]]["name"], int(req["level"])],
			"current": float(lvl), "target": float(req["level"]), "met": lvl >= int(req["level"]), "money": false})
	return out


func requirements_for_zone(zid: String) -> Array:
	var z: Dictionary = data.zone_by_id[zid]
	return [_stage_requirement(int(z["stage"]))] if stage < int(z["stage"]) else []


func _stage_requirement(target_stage: int) -> Dictionary:
	return {"text": "Etapa %d: %s" % [target_stage, data.stage_name(target_stage)],
		"current": float(stage), "target": float(target_stage), "met": false, "money": false}


## Requisitos para comprar un negocio.
func unlock_status(id: String) -> Dictionary:
	var def: Dictionary = data.business_by_id[id]
	var u: Dictionary = def["unlock"]
	var reasons := []
	if stage < int(u["stage"]):
		reasons.append("Etapa %d: %s" % [int(u["stage"]), data.stage_name(int(u["stage"]))])
	var req = u.get("requires")
	if req != null and req.get("conquer", false):
		if not ConquestSystem.business_conquered(self, req["business"]):
			reasons.append("Conquistá %s" % data.zone_by_id[data.zone_for_business(req["business"])]["name"])
	elif req != null:
		var rs: Dictionary = biz[req["business"]]
		if not rs["owned"] or int(rs["level"]) < int(req["level"]):
			reasons.append("%s nivel %d" % [data.business_by_id[req["business"]]["name"], int(req["level"])])
	var cost := Economy.to_int_ceil(float(u["cost"]))
	return {"cost": cost, "reasons": reasons, "available": reasons.is_empty(), "affordable": economy.can_afford(cost)}


## Abre el negocio en su provincia (zone_id se ignora: queda por compatibilidad).
func buy_business(id: String, _zone_id: String = "") -> Dictionary:
	if biz[id]["owned"]:
		return fail("Ya tenés este negocio.")
	var zone_id := data.zone_for_business(id)
	var st := unlock_status(id)
	if not st["available"]:
		return fail("Falta: " + ", ".join(st["reasons"]))
	if not economy.spend(st["cost"], "negocios"):
		return fail("No te alcanza la plata.")
	_own_business(id, 1.0)
	zones[zone_id]["paid"] = st["cost"]
	biz[id]["invested"] = st["cost"]
	var name: String = data.business_by_id[id]["name"]
	add_milestone("Abriste %s en %s." % [name, data.zone_by_id[zone_id]["name"]])
	celebrate.emit("unlock", {"business": id, "bought": true})
	notify.emit("¡Abriste %s!" % name, "good")
	EmployeeSystem.ensure_candidates(self, id)
	businesses_changed.emit()
	business_changed.emit(id)
	world_changed.emit()
	return ok()


func relocate_cost(id: String) -> int:
	var c := float(data.business_by_id[id]["unlock"]["cost"]) * float(data.world["relocate_cost_factor"])
	return maxi(100, Economy.to_int_ceil(c))


## 10.0: cada negocio pertenece a su provincia; no hay mudanzas.
func relocate(id: String, zone_id: String) -> Dictionary:
	if zone_id != data.zone_for_business(id):
		return fail("Cada negocio pertenece a su provincia.")
	var s: Dictionary = biz[id]
	if not s["owned"]:
		return fail("No tenés este negocio.")
	if not zones.has(zone_id):
		return fail("Zona bloqueada.")
	if s["zone"] == zone_id:
		return fail("Ya está en esa zona.")
	var cost := relocate_cost(id)
	if not economy.spend(cost, "mudanzas"):
		return fail("No te alcanza la plata.")
	s["zone"] = zone_id
	invalidate()
	notify.emit("%s se mudó a %s." % [data.business_by_id[id]["name"], data.zone_by_id[zone_id]["name"]], "info")
	business_changed.emit(id)
	world_changed.emit()
	return ok()


## Cuánto cambiaría la ganancia por segundo del negocio con un cambio
## hipotético (para mostrar "+$X/s" antes de comprar). No modifica nada.
func preview_profit_gain(id: String, mutator: Callable) -> float:
	var snap: Dictionary = biz[id].duplicate(true)
	var before: float = derive(id)["profit_sec"]
	mutator.call(biz[id])
	invalidate()
	var after: float = derive(id)["profit_sec"]
	biz[id] = snap
	invalidate()
	return after - before


# ---------------------------------------------------------------------------
# Acciones: mapa
# ---------------------------------------------------------------------------

## Estado de una provincia: abierta = tenés su negocio. Abrirla = comprar el negocio.
func zone_status(zid: String) -> Dictionary:
	var bid: String = data.zone_by_id[zid]["business"]
	var st := unlock_status(bid)
	st["unlocked"] = zones.has(zid)
	st["conquered"] = ConquestSystem.is_conquered(self, zid)
	st["share"] = ConquestSystem.share(self, zid)
	return st


func unlock_zone(zid: String) -> Dictionary:
	if zones.has(zid):
		return fail("Ya tenés esa provincia.")
	return buy_business(data.zone_by_id[zid]["business"])


func businesses_in_zone(zid: String) -> Array:
	var out := []
	for id in owned_ids():
		if biz[id]["zone"] == zid:
			out.append(id)
	return out


# ---------------------------------------------------------------------------
# Perfil
# ---------------------------------------------------------------------------

## Largo máximo del nombre de la empresa (se muestra completo en Perfil, en
## hasta dos líneas, y recortado con "…" en la barra superior).
const COMPANY_MAX := 32


func set_company_name(text: String) -> Dictionary:
	var clean := text.strip_edges().replace("\n", " ")
	if clean.length() < 2:
		return fail("El nombre es muy corto.")
	if clean.length() > COMPANY_MAX:
		clean = clean.substr(0, COMPANY_MAX).strip_edges()
	profile["company"] = clean
	profile_changed.emit()
	return ok()


func set_avatar(aid: String) -> Dictionary:
	if not profile["avatars"].has(aid):
		return fail("Avatar bloqueado.")
	profile["avatar"] = aid
	profile_changed.emit()
	return ok()


## Marca si el jugador tiene foto/banner propios (los archivos los maneja
## ProfileImages en user://profile/).
func set_profile_image(kind: String, on: bool) -> void:
	if kind in ["photo", "banner"]:
		profile[kind] = on
		profile_changed.emit()


func unlock_avatar(aid: String) -> bool:
	if profile["avatars"].has(aid) or not data.avatar_by_id.has(aid):
		return false
	profile["avatars"].append(aid)
	notify.emit("Nuevo avatar: %s" % data.avatar_by_id[aid]["name"], "reward")
	profile_changed.emit()
	return true


func add_milestone(text: String) -> void:
	var list: Array = profile.get("milestones", [])
	list.append({"t": now(), "text": text})
	while list.size() > 60:
		list.pop_front()
	profile["milestones"] = list


# ---------------------------------------------------------------------------
# Métricas (las usan misiones y logros)
# ---------------------------------------------------------------------------

func _count(key: String, n: float) -> void:
	counters[key] = float(counters.get(key, 0.0)) + n


func counter(key: String) -> float:
	return float(counters.get(key, 0.0))


func metric(name: String) -> float:
	if name.begins_with("level:"):
		var bid := name.substr(6)
		return float(biz[bid]["level"]) if biz.has(bid) and biz[bid]["owned"] else 0.0
	if name.begins_with("sold:") or name.begins_with("sold_tag:"):
		return floorf(counter(name))
	match name:
		"money": return float(economy.money)
		"businesses_owned": return float(owned_ids().size())
		"employees_current": return float(employees.size())
		"automated":
			var n := 0
			for id in owned_ids():
				if derive(id)["auto_sell"]:
					n += 1
			return float(n)
		"auto_restock":
			var n2 := 0
			for id in owned_ids():
				if derive(id)["auto_restock"]:
					n2 += 1
			return float(n2)
		"max_level":
			var mx := 0
			for id in owned_ids():
				mx = maxi(mx, int(biz[id]["level"]))
			return float(mx)
		"zones_unlocked": return float(zones.size())
		"conquered": return float(ConquestSystem.conquered_count(self))
		"regions_conquered": return float(ConquestSystem.regions_conquered(self))
		"branches":
			var br := 0
			for id in owned_ids():
				br += int(biz[id]["upgrades"].get("sucursal", 0))
			return float(br)
		"stage": return float(stage)
		"net_worth": return net_worth()
		"run_earnings": return float(economy.run_earned)
		"lifetime_earnings": return float(economy.lifetime_earned)
		"prestige_count": return float(prestige.get("count", 0))
		"play_time": return float(stats.get("play_time", 0.0))
	return counter(name)


# ---------------------------------------------------------------------------
# Simulación
# ---------------------------------------------------------------------------

## Avanza el juego dt segundos. Se usa igual online (pasos de 0,1 s) y
## offline (pasos de 5 s): la misma lógica produce los mismos resultados.
func simulate(dt: float, offline := false) -> void:
	if dt <= 0.0:
		return
	_advance_boosts(dt)
	EventSystem.advance(self, dt, offline)
	if not offline:
		RivalSystem.advance(self, dt)
	for id in owned_ids():
		BusinessSim.advance(self, id, dt)
	ConquestSystem.advance(self, dt)
	EmployeeSystem.advance(self, dt, offline)
	HardMode.advance(self, dt, offline)
	if not offline:
		Engagement.advance(self, dt)
	if not offline:
		stats["play_time"] = float(stats.get("play_time", 0.0)) + dt
		_progress_timer += dt
		if _progress_timer >= 1.0:
			_progress_timer = 0.0
			update_progress()


func _advance_boosts(dt: float) -> void:
	if boosts.is_empty():
		return
	var changed := false
	for bo in boosts:
		bo["remaining"] = float(bo["remaining"]) - dt
	for i in range(boosts.size() - 1, -1, -1):
		if float(boosts[i]["remaining"]) <= 0.0:
			boosts.remove_at(i)
			changed = true
	if changed:
		invalidate()
		notify.emit("Terminó el turbo de ingresos.", "info")


func add_boost(mult: float, seconds: float) -> void:
	for bo in boosts:
		if is_equal_approx(float(bo["mult"]), mult):
			bo["remaining"] = float(bo["remaining"]) + seconds
			bo["total"] = float(bo["total"]) + seconds
			invalidate()
			return
	boosts.append({"mult": mult, "remaining": seconds, "total": seconds})
	invalidate()


## 10.0: la etapa es 1 + regiones conquistadas por completo (7 = toda la Argentina).
func conquest_stage() -> int:
	return mini(1 + ConquestSystem.regions_conquered(self), data.stages.size())


## Se llama una vez por segundo: etapas, misiones, logros, récords.
func update_progress() -> void:
	var new_stage := conquest_stage()
	if new_stage > stage:
		stage = new_stage
		invalidate()
		add_milestone("Llegaste a la etapa %d: %s." % [stage, data.stage_name(stage)])
		notify.emit("¡Nueva etapa! %s" % data.stage_name(stage), "good")
		celebrate.emit("stage", {"stage": stage})
		stage_changed.emit(stage)
		for id in owned_ids():
			EmployeeSystem.ensure_candidates(self, id)
	stats["best_income"] = maxf(float(stats.get("best_income", 0.0)), income_per_sec())
	Engagement.check_level_marks(self)
	Engagement.check_event_goals(self)
	ProgressionSystem.update(self)
	var t := now()
	time_state["last_active"] = t
	time_state["max_seen"] = maxf(float(time_state.get("max_seen", 0.0)), t)


# ---------------------------------------------------------------------------
# Guardado
# ---------------------------------------------------------------------------

func to_dict() -> Dictionary:
	var bdict := {}
	for id in biz:
		var s: Dictionary = biz[id].duplicate(true)
		s["invested"] = str(s["invested"])
		s["earned"] = str(s["earned"])
		bdict[id] = s
	var zdict := {}
	for z in zones:
		zdict[z] = {"paid": str(zones[z]["paid"]), "share": float(zones[z].get("share", 0.0)),
			"conquered": bool(zones[z].get("conquered", false)), "at": float(zones[z].get("at", 0.0))}
	return {
		"economy": economy.to_dict(),
		"businesses": bdict,
		"employees": employees.duplicate(true),
		"zones": zdict,
		"counters": counters.duplicate(true),
		"stats": stats.duplicate(true),
		"profile": profile.duplicate(true),
		"missions": missions.duplicate(true),
		"daily_missions": daily_missions.duplicate(true),
		"achievements": achievements.duplicate(true),
		"daily_reward": daily_reward.duplicate(true),
		"ads": ads.duplicate(true),
		"social": social.duplicate(true),
		"events": events.duplicate(true),
		"inflation": inflation.duplicate(true),
		"rivals": rivals.duplicate(true),
		"rival_log": rival_log.duplicate(true),
		"prestige": prestige.duplicate(true),
		"boosts": boosts.duplicate(true),
		"tutorial": tutorial.duplicate(true),
		"time": {"last_active": now(), "max_seen": maxf(float(time_state.get("max_seen", 0.0)), now())},
		"salary_due": salary_due,
		"salary_debt": str(salary_debt),
		"next_employee_id": next_employee_id,
		"stage": stage,
		"hard": hard.duplicate(true),
		"engage": engage.duplicate(true),
	}


## Carga tolerante: cualquier campo faltante o inválido toma un valor seguro.
func from_dict(d: Dictionary) -> void:
	new_game()
	if d.get("fresh_start", false):
		_load_fresh_start(d)
		return
	economy.from_dict(d.get("economy", {}))
	var bdict: Dictionary = d.get("businesses", {})
	for id in biz:
		if bdict.has(id) and bdict[id] is Dictionary:
			biz[id] = _sanitize_business(id, bdict[id])
	var first := first_business()
	if not biz[first]["owned"]:
		biz[first]["owned"] = true
		biz[first]["level"] = maxi(1, int(biz[first]["level"]))
	employees = {}
	var edict = d.get("employees", {})
	if edict is Dictionary:
		for eid in edict:
			var e = edict[eid]
			if e is Dictionary and data.role_by_id.has(e.get("role", "")) and biz.has(e.get("business", "")) and biz[e["business"]]["owned"]:
				e["eff"] = clampf(float(e.get("eff", 1.0)), 0.1, 3.0)
				e["salary"] = maxf(0.0, float(e.get("salary", 0.0)))
				e["xp"] = maxf(0.0, float(e.get("xp", 0.0)))
				e["variant"] = int(e.get("variant", 0))
				e["name"] = str(e.get("name", "Empleado"))
				e["id"] = str(eid)
				employees[str(eid)] = e
	zones = {}
	var zd = d.get("zones", {})
	if zd is Dictionary:
		for z in zd:
			if data.zone_by_id.has(z) and zd[z] is Dictionary:
				zones[z] = {"paid": maxi(0, Economy.s2i(zd[z].get("paid", 0))),
					"share": clampf(float(zd[z].get("share", 0.0)), 0.0, 1.0),
					"conquered": bool(zd[z].get("conquered", false)), "at": float(zd[z].get("at", 0.0))}
	for id in owned_ids():
		if not zones.has(biz[id]["zone"]):
			zones[biz[id]["zone"]] = {"paid": 0, "share": 0.0, "conquered": false}
	counters = _dict_or(d.get("counters"), {})
	stats = _merge(stats, d.get("stats"))
	profile = _merge(profile, d.get("profile"))
	if not profile["avatars"] is Array:
		profile["avatars"] = _default_avatars()
	missions = _merge(missions, d.get("missions"))
	daily_missions = _merge(daily_missions, d.get("daily_missions"))
	achievements = _dict_or(d.get("achievements"), {})
	daily_reward = _merge(daily_reward, d.get("daily_reward"))
	ads = _merge(ads, d.get("ads"))
	social = _merge(social, d.get("social"))
	if not ads["granted"] is Array:
		ads["granted"] = []
	if not ads["cooldowns"] is Dictionary:
		ads["cooldowns"] = {}
	events = _merge(events, d.get("events"))
	var valid_events := []
	for ev in events.get("active", []):
		if ev is Dictionary and data.event_by_id.has(ev.get("id", "")):
			valid_events.append(ev)
	events["active"] = valid_events
	inflation = _merge(inflation, d.get("inflation"))
	var rv = d.get("rivals", {})
	if rv is Dictionary:
		for r in rivals:
			if rv.has(r) and rv[r] is Dictionary:
				rivals[r] = _merge(rivals[r], rv[r])
				rivals[r]["power"] = clampi(int(rivals[r]["power"]), 1, 10)
	rival_log = d.get("rival_log", []) if d.get("rival_log") is Array else []
	prestige = _merge(prestige, d.get("prestige"))
	boosts = d.get("boosts", []) if d.get("boosts") is Array else []
	tutorial = _merge(tutorial, d.get("tutorial"))
	time_state = _merge(time_state, d.get("time"))
	salary_due = maxf(0.0, float(d.get("salary_due", 0.0)))
	salary_debt = maxi(0, Economy.s2i(d.get("salary_debt", 0)))
	next_employee_id = maxi(int(d.get("next_employee_id", 1)), employees.size() + 1)
	stage = conquest_stage()
	hard = _merge(HardMode.default_state(), d.get("hard"))
	if not hard["protected"] is Dictionary:
		hard["protected"] = {}
	engage = _merge(Engagement.default_state(), d.get("engage"))
	if not engage["marks"] is Dictionary:
		engage["marks"] = {}
	engage["chests"] = maxi(0, int(engage["chests"]))
	invalidate()


## 10.0: las partidas 0.7 empiezan de cero (Migrations._v3_to_v4); sólo se
## conservan perfil, recompensa diaria, anuncios, amigos y fecha de creación.
func _load_fresh_start(d: Dictionary) -> void:
	profile = _merge(profile, d.get("profile"))
	if not profile["avatars"] is Array:
		profile["avatars"] = _default_avatars()
	profile["milestones"] = []
	daily_reward = _merge(daily_reward, d.get("daily_reward"))
	ads = _merge(ads, d.get("ads"))
	social = _merge(social, d.get("social"))
	if not ads["granted"] is Array:
		ads["granted"] = []
	if not ads["cooldowns"] is Dictionary:
		ads["cooldowns"] = {}
	var created = d.get("stats", {}).get("created") if d.get("stats") is Dictionary else null
	if created != null:
		stats["created"] = float(created)
	add_milestone("Arrancó la 10.0 Sigma Deza: a conquistar la Argentina desde el NOA.")
	invalidate()


func _sanitize_business(id: String, src: Dictionary) -> Dictionary:
	var def: Dictionary = data.business_by_id[id]
	var s := _new_business_state(id)
	s["owned"] = bool(src.get("owned", false))
	s["level"] = clampi(int(src.get("level", 0)), 1 if s["owned"] else 0, int(def["max_level"]))
	s["zone"] = data.zone_for_business(id)
	var up = src.get("upgrades", {})
	if up is Dictionary:
		for uid in up:
			if data.upgrade_by_id.has(uid):
				s["upgrades"][uid] = clampi(int(up[uid]), 0, int(data.upgrade_by_id[uid]["max_level"]))
	var st = src.get("stock", {})
	if st is Dictionary:
		for pid in s["stock"]:
			s["stock"][pid] = maxf(0.0, float(st.get(pid, 0.0)))
	var od = src.get("orders", {})
	if od is Dictionary:
		for pid in od:
			if s["stock"].has(pid) and od[pid] is Dictionary:
				s["orders"][pid] = {"units": maxf(0.0, float(od[pid].get("units", 0.0))), "eta": maxf(0.0, float(od[pid].get("eta", 0.0)))}
	s["progress"] = maxf(0.0, float(src.get("progress", 0.0)))
	s["running"] = bool(src.get("running", false)) and s["owned"]
	s["carry"] = clampf(float(src.get("carry", 0.0)), 0.0, 1.0)
	s["invested"] = maxi(0, Economy.s2i(src.get("invested", 0)))
	s["earned"] = maxi(0, Economy.s2i(src.get("earned", 0)))
	s["sales"] = maxi(0, int(src.get("sales", 0)))
	s["candidates"] = src.get("candidates", []) if src.get("candidates") is Array else []
	s["cand_timer"] = float(src.get("cand_timer", 0.0))
	s["reroll_cd"] = maxf(0.0, float(src.get("reroll_cd", 0.0)))
	s["closed"] = bool(src.get("closed", false)) and s["owned"]
	return s


static func _dict_or(v: Variant, fallback: Dictionary) -> Dictionary:
	return v if v is Dictionary else fallback


## Toma los valores por defecto y pisa sólo las claves presentes con el mismo tipo.
static func _merge(base: Dictionary, src: Variant) -> Dictionary:
	var out := base.duplicate(true)
	if not src is Dictionary:
		return out
	for k in src:
		if not out.has(k):
			out[k] = src[k]
		elif typeof(out[k]) == typeof(src[k]) or (out[k] is float and src[k] is int) or (out[k] is int and src[k] is float):
			out[k] = src[k]
	return out
