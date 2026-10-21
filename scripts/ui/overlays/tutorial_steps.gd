class_name TutorialSteps
extends RefCounted
## Misión guiada inicial. La comparten el globo de Tito (TutorialOverlay) y
## la franja de objetivo (ObjectiveStrip), así el texto nunca se contradice.
## block = oscurece la pantalla y sólo deja tocar el objetivo.

const STEPS := [
	{"goal": "Abrí tu puestito", "text": "¡Bienvenido/a al barrio! Este puestito es el comienzo de tu imperio. Tocá ABRIR EL PUESTO.", "target": "main", "block": true, "reward": {}},
	{"goal": "Comprá tu primera mercadería", "text": "Sin mercadería no hay ventas. Tocá REPONER MERCADERÍA: el pedido llega en unos segundos.", "target": "main", "block": true, "reward": {"money": 10}},
	{"goal": "Vendé tu primer producto", "text": "¡Llegó la mercadería! Tocá ¡VENDER! (o mantenelo apretado) para atender clientes.", "target": "main", "block": true, "reward": {"money": 20}},
	{"goal": "Subí el puesto a nivel 2", "text": "Con lo que ganaste, tocá SUBIR NIVEL: cada nivel atiende más clientes por venta.", "target": "level", "block": false, "reward": {"money": 20}},
	{"goal": "Contratá un vendedor", "text": "Tocá ADMINISTRAR → EMPLEADOS y contratá un vendedor: el puesto va a vender solo, ¡incluso con el juego cerrado!", "target": "manage", "block": false, "reward": {"boost": {"mult": 2.0, "seconds": 300}}},
	{"goal": "Abrí tu primer kiosco", "text": "¡Tu puesto vende solo! Juntá $2.000 y abrí tu primer kiosco desde NEGOCIOS (requiere el puesto en nivel 10).", "target": "nav_1", "block": false, "reward": {"money": 300}},
]


static func done(m: GameModel, step: int) -> bool:
	match step:
		0: return not m.biz["puesto"].get("closed", false)
		1: return m.counter("restock_count") >= 1
		2: return m.counter("sales_total") >= 1
		3: return int(m.biz["puesto"]["level"]) >= 2
		4: return m.counter("hires_total") >= 1
		5: return m.biz["kiosco"]["owned"]
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
