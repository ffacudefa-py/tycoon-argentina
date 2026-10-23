class_name AdRewards
extends RefCounted
## Lógica de recompensas por anuncio (pura: se prueba sin anuncios reales).
##
## Flujo seguro:
##   1. begin(): valida (límite diario, espera, una sola sesión a la vez),
##      FIJA el monto prometido y crea un token único.
##   2. El proveedor muestra el anuncio.
##   3. complete(token, earned=true) SÓLO cuando el proveedor confirma que se
##      vio completo. Entrega una única vez: el token queda registrado en el
##      guardado (m.ads.granted). Un segundo aviso con el mismo token, un
##      token viejo, o un anuncio cerrado antes de tiempo no entregan nada.

const GRANTED_KEEP := 50

static var session := {}      ## sesión en curso (no se guarda: no sobrevive a cerrar la app)


static func state(m: GameModel) -> Dictionary:
	var s: Dictionary = m.ads
	var today := ProgressionSystem.day_index(m)
	if int(s.get("day", -1)) != today:
		s["day"] = today
		s["today"] = 0
	for k in ["granted", "cooldowns"]:
		if not s.has(k):
			s[k] = [] if k == "granted" else {}
	return s


static func amount_for(m: GameModel, offer: Dictionary, params := {}) -> int:
	match offer["kind"]:
		"money", "daily_extra":
			if offer["kind"] == "daily_extra" and int(m.daily_reward.get("last_money", 0)) > 0:
				return int(m.daily_reward["last_money"])
			return ProgressionSystem.reward_money(m, {"income_seconds": offer.get("income_seconds", 0), "min": offer.get("min", 0)})
		"restock":
			var bid: String = params.get("business", "")
			return int(m.restock_quote(bid)["total"]) if m.biz.has(bid) and m.biz[bid]["owned"] else 0
	return 0


## Estado de cada oferta para la interfaz.
static func offer_status(m: GameModel, cfg: AdConfig, offer: Dictionary, params := {}) -> Dictionary:
	var s := state(m)
	var now := m.now()
	var left := float(s["cooldowns"].get(offer["id"], 0.0)) - now
	var out := {"available": true, "reason": "", "amount": amount_for(m, offer, params), "cooldown_left": maxf(0.0, left)}
	if int(s["today"]) >= cfg.daily_limit():
		out["available"] = false
		out["reason"] = "Llegaste al máximo de %d anuncios por hoy." % cfg.daily_limit()
	elif left > 0.0:
		out["available"] = false
		out["reason"] = "Disponible en %s." % Fmt.duration(left)
	elif offer["kind"] == "daily_extra":
		if int(m.daily_reward.get("last_day", -1)) != ProgressionSystem.day_index(m):
			out["available"] = false
			out["reason"] = "Primero reclamá la recompensa diaria de hoy."
		elif int(s.get("daily_extra_day", -1)) == ProgressionSystem.day_index(m):
			out["available"] = false
			out["reason"] = "Ya la reclamaste hoy."
	elif offer["kind"] == "restock" and out["amount"] <= 0:
		out["available"] = false
		out["reason"] = "Ese negocio ya tiene el depósito lleno."
	return out


static func describe(m: GameModel, offer: Dictionary, params := {}) -> Dictionary:
	var amount := amount_for(m, offer, params)
	var bname := ""
	if params.has("business") and m.data.business_by_id.has(params["business"]):
		bname = m.data.business_by_id[params["business"]]["name"]
	var rep := func(t: String) -> String: return t.replace("{amount}", Fmt.money(amount)).replace("{business}", bname)
	return {"title": rep.call(offer["title"]), "description": rep.call(offer["description"])}


static func begin(m: GameModel, cfg: AdConfig, offer_id: String, params := {}) -> Dictionary:
	if not session.is_empty():
		return GameModel.fail("Ya hay un anuncio en curso.")
	var offer: Dictionary = {}
	for o in cfg.offers():
		if o["id"] == offer_id:
			offer = o
	if offer.is_empty():
		return GameModel.fail("Esa recompensa no existe.")
	var st := offer_status(m, cfg, offer, params)
	if not st["available"]:
		return GameModel.fail(st["reason"])
	var s := state(m)
	s["seq"] = int(s.get("seq", 0)) + 1
	var token := "%d-%d-%s" % [int(m.now()), int(s["seq"]), offer_id]
	session = {"token": token, "offer": offer, "amount": st["amount"], "params": params}
	return {"ok": true, "msg": "", "token": token}


## earned=true sólo con la confirmación del proveedor. Devuelve {ok, msg, granted}.
static func complete(m: GameModel, token: String, earned: bool) -> Dictionary:
	var s := state(m)
	if (s["granted"] as Array).has(token):
		session = {}
		return {"ok": false, "msg": "Esa recompensa ya se entregó.", "granted": false}
	if session.is_empty() or session.get("token", "") != token:
		return {"ok": false, "msg": "No hay un anuncio en curso con ese identificador.", "granted": false}
	var ses := session
	session = {}
	if not earned:
		return {"ok": false, "msg": "Cerraste el anuncio antes de terminarlo: esta vez no hay recompensa.", "granted": false}
	var offer: Dictionary = ses["offer"]
	var amount: int = ses["amount"]
	var msg := ""
	match offer["kind"]:
		"money", "daily_extra":
			m.economy.earn(amount, "anuncios")
			msg = "¡Recibiste %s!" % Fmt.money(amount)
			if offer["kind"] == "daily_extra":
				s["daily_extra_day"] = ProgressionSystem.day_index(m)
		"boost":
			m.add_boost(float(offer["mult"]), float(offer["seconds"]))
			msg = "¡Ganancias x%s durante %s!" % [str(offer["mult"]).trim_suffix(".0"), Fmt.duration(offer["seconds"])]
		"restock":
			var bid: String = ses["params"].get("business", "")
			if m.biz.has(bid) and m.biz[bid]["owned"]:
				for p in m.derive(bid)["products"]:
					m.biz[bid]["stock"][p["id"]] = float(p["cap"])
				m.biz[bid]["orders"] = {}
				m.business_changed.emit(bid)
				msg = "¡Depósito lleno en %s!" % m.data.business_by_id[bid]["name"]
	var granted: Array = s["granted"]
	granted.append(token)
	while granted.size() > GRANTED_KEEP:
		granted.pop_front()
	s["today"] = int(s["today"]) + 1
	if float(offer.get("cooldown", 0)) > 0.0:
		s["cooldowns"][offer["id"]] = m.now() + float(offer["cooldown"])
	m._count("ads_watched", 1)
	m.celebrate.emit("claim", {"ad": offer["id"]})
	return {"ok": true, "msg": msg, "granted": true}


static func cancel_session() -> void:
	session = {}
