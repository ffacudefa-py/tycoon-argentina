class_name GameData
extends RefCounted
## Carga y valida los archivos de datos (res://data/*.json).
## Todo el balance vive en esos archivos: acá sólo se leen y se precalculan
## valores derivados (escala de cada negocio, participación de productos).

var balance := {}
var businesses: Array = []          ## en orden de progresión
var business_by_id := {}
var upgrades: Array = []
var upgrade_by_id := {}
var roles: Array = []
var role_by_id := {}
var employees_cfg := {}
var zones: Array = []               ## 10.0: las 24 provincias, en orden de conquista
var zone_by_id := {}
var regions: Array = []             ## 6 regiones, en orden de conquista
var region_by_id := {}
var zone_of_business := {}          ## id de negocio -> provincia
var world := {}
var rivals: Array = []
var rival_by_id := {}
var events_cfg := {}
var event_by_id := {}
var stages: Array = []
var prestige_cfg := {}
var friends_cfg := {}
var perk_by_id := {}
var daily_rewards: Array = []
var avatars: Array = []
var avatar_by_id := {}
var missions_main: Array = []
var challenges: Array = []
var daily_cfg := {}
var achievements: Array = []
var achievement_by_id := {}
var mission_by_id := {}
var errors: PackedStringArray = []


static func load_default() -> GameData:
	var d := GameData.new()
	d.load_from("res://data")
	return d


func load_from(dir: String) -> void:
	var biz = _read(dir + "/businesses.json")
	var upg = _read(dir + "/upgrades.json")
	var emp = _read(dir + "/employees.json")
	var wld = _read(dir + "/world.json")
	var evs = _read(dir + "/events.json")
	var prog = _read(dir + "/progression.json")
	var mis = _read(dir + "/missions.json")
	if not errors.is_empty():
		return
	balance = prog["balance"]
	stages = prog["stages"]
	prestige_cfg = prog["prestige"]
	friends_cfg = prog.get("friends", {"max_friends": 50, "gifts_per_day": 5, "gift_reward": {"income_seconds": 120, "min": 200}})
	daily_rewards = prog["daily_rewards"]
	avatars = prog["avatars"]
	for a in avatars:
		avatar_by_id[a["id"]] = a
	for p in prestige_cfg["perks"]:
		perk_by_id[p["id"]] = p

	upgrades = upg["upgrades"]
	for u in upgrades:
		upgrade_by_id[u["id"]] = u

	employees_cfg = emp
	roles = emp["roles"]
	for r in roles:
		role_by_id[r["id"]] = r

	world = wld
	zones = wld["zones"]
	for z in zones:
		zone_by_id[z["id"]] = z
		zone_of_business[z.get("business", "")] = z["id"]
	regions = wld.get("regions", [])
	for r in regions:
		region_by_id[r["id"]] = r
	rivals = wld["rivals"]
	for r in rivals:
		rival_by_id[r["id"]] = r

	events_cfg = evs
	for e in evs["events"]:
		event_by_id[e["id"]] = e

	missions_main = mis["main"]
	challenges = mis["challenges"]
	daily_cfg = mis["daily"]
	achievements = mis["achievements"]
	for m in missions_main + challenges + daily_cfg["pool"]:
		mission_by_id[m["id"]] = m
	for a in achievements:
		achievement_by_id[a["id"]] = a

	businesses = biz["businesses"]
	for i in businesses.size():
		var b: Dictionary = businesses[i]
		b["index"] = i
		_prepare_business(b)
		business_by_id[b["id"]] = b
	_validate()


## Precalcula la participación de cada producto en la demanda y la "escala"
## del negocio (ganancia por segundo a nivel 10) que usan sueldos y contrataciones.
func _prepare_business(b: Dictionary) -> void:
	var total_demand := 0.0
	for p in b["products"]:
		total_demand += float(p["demand"])
	var profit_unit := 0.0
	var revenue_unit := 0.0
	for p in b["products"]:
		p["share"] = float(p["demand"]) / total_demand
		profit_unit += p["share"] * (float(p["price"]) - float(p["cost"]))
		revenue_unit += p["share"] * float(p["price"])
	b["profit_per_unit"] = profit_unit
	b["revenue_per_unit"] = revenue_unit
	b["scale"] = profit_unit / float(b["cycle"]) * 10.0


func _validate() -> void:
	var required_biz := ["id", "name", "cycle", "level_cost_base", "level_cost_growth", "unlock", "products", "restock_time", "tags", "max_level"]
	for b in businesses:
		for k in required_biz:
			if not b.has(k):
				errors.append("negocio %s: falta '%s'" % [b.get("id", "?"), k])
		for p in b.get("products", []):
			if float(p["price"]) <= float(p["cost"]):
				errors.append("producto %s/%s: precio <= costo" % [b["id"], p["id"]])
		var req = b["unlock"].get("requires")
		if req != null and not business_by_id.has(req["business"]) and req["business"] != b["id"]:
			# Puede estar definido después; se revisa al final.
			pass
	for b in businesses:
		var req = b["unlock"].get("requires")
		if req != null and not business_by_id.has(req["business"]):
			errors.append("negocio %s requiere '%s', que no existe" % [b["id"], req["business"]])
	for m in missions_main + challenges + achievements:
		if not m.has("metric") or not m.has("target"):
			errors.append("misión/logro %s incompleto" % m.get("id", "?"))
	if businesses.is_empty():
		errors.append("no hay negocios")
	for b in businesses:
		if not zone_of_business.has(b["id"]):
			errors.append("negocio %s sin provincia" % b["id"])


func _read(path: String) -> Variant:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		errors.append("no se pudo abrir %s" % path)
		return null
	var json := JSON.new()
	var err := json.parse(f.get_as_text())
	if err != OK:
		errors.append("%s línea %d: %s" % [path, json.get_error_line(), json.get_error_message()])
		return null
	return json.data


## Primer negocio (el de la primera provincia): arranca abierto en toda partida.
func first_business() -> String:
	return businesses[0]["id"]


func zone_for_business(bid: String) -> String:
	return zone_of_business.get(bid, zones[0]["id"])


## Provincias de una región, en orden de conquista.
func zones_in_region(rid: String) -> Array:
	var out := []
	for z in zones:
		if z["region"] == rid:
			out.append(z)
	return out


func stage_for(earnings: float) -> int:
	var s := 1
	for st in stages:
		if earnings >= float(st.get("earnings", INF)):
			s = int(st["id"])
	return s


func stage_name(stage: int) -> String:
	for st in stages:
		if int(st["id"]) == stage:
			return st["name"]
	return ""
