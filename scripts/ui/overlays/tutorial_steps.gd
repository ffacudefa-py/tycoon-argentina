class_name TutorialSteps
extends RefCounted
## Misión guiada inicial. La comparten el globo de Tito (TutorialOverlay) y
## la franja de objetivo (ObjectiveStrip), así el texto nunca se contradice.
## block = oscurece la pantalla y sólo deja tocar el objetivo.

const STEPS := [
	{"goal": "Abrí tu campo de algodón", "text": "¡Bienvenido/a a Santiago del Estero! Este campito de algodón es el comienzo de tu imperio: el objetivo es conquistar toda la Argentina. Tocá ABRIR.", "target": "main", "block": true, "reward": {}},
	{"goal": "Comprá tus primeros insumos", "text": "Sin insumos no hay ventas. Tocá REPONER MERCADERÍA: el pedido llega en unos segundos.", "target": "main", "block": true, "reward": {"money": 10}},
	{"goal": "Vendé tu primera cosecha", "text": "¡Llegaron los insumos! Tocá ¡VENDER! (o mantenelo apretado) para venderle a los compradores.", "target": "main", "block": true, "reward": {"money": 20}},
	{"goal": "Subí el campo a nivel 2", "text": "Con lo que ganaste, tocá SUBIR NIVEL: cada nivel vende más por cada venta.", "target": "level", "block": false, "reward": {"money": 20}},
	{"goal": "Contratá un vendedor", "text": "Tocá ADMINISTRAR → EMPLEADOS y contratá un vendedor: el campo va a vender solo, ¡incluso con el juego cerrado!", "target": "manage", "block": false, "reward": {"boost": {"mult": 2.0, "seconds": 300}}},
	{"goal": "Ganá la mitad del mercado", "text": "Para conquistar la provincia tenés que dominar su mercado. Cuanto más ganás, más cuota le sacás al rival. Llegá al 50 % (lo ves en el MAPA).", "target": "nav_2", "block": false, "reward": {"money": 300}},
]


static func done(m: GameModel, step: int) -> bool:
	var first := m.first_business()
	match step:
		0: return not m.biz[first].get("closed", false)
		1: return m.counter("restock_count") >= 1
		2: return m.counter("sales_total") >= 1
		3: return int(m.biz[first]["level"]) >= 2
		4: return m.counter("hires_total") >= 1
		5: return ConquestSystem.share(m, m.data.zone_for_business(first)) >= 0.5 or ConquestSystem.conquered_count(m) > 0
	return true


static func active(m: GameModel) -> bool:
	return not m.tutorial.get("done", false) and int(m.tutorial.get("step", 0)) < STEPS.size()


static func current(m: GameModel) -> Dictionary:
	return STEPS[int(m.tutorial.get("step", 0))] if active(m) else {}


## Avanza todos los pasos ya cumplidos y entrega sus premios (una vez).
static func update(m: GameModel) -> bool:
	var advanced := false
	while active(m) and done(m, int(m.tutorial["step"])):
		var step := int(m.tutorial["step"])
		m.grant_tutorial_reward(step, STEPS[step]["reward"])
		m.tutorial["step"] = step + 1
		advanced = true
	if int(m.tutorial.get("step", 0)) >= STEPS.size():
		m.tutorial["done"] = true
	return advanced
