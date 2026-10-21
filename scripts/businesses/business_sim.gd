class_name BusinessSim
extends RefCounted
## Avance temporal de un negocio: pedidos de mercadería en camino, ciclos
## de venta y reposición automática.
##
## Un ciclo de venta atiende `units` clientes repartidos entre los productos
## según su demanda. Al terminar el ciclo se vende lo que haya en stock
## (si falta un producto, esa parte de la venta se pierde) y se acredita.
## Con dt grandes (offline) se completan varios ciclos de una vez.


static func advance(m: GameModel, id: String, dt: float) -> void:
	var s: Dictionary = m.biz[id]
	var d := m.derive(id)
	_advance_orders(m, id, s, dt)

	var t := dt
	var guard := 0
	while t > 0.0 and guard < 4:
		guard += 1
		if not s["running"]:
			if d["auto_sell"] and m.has_stock(id):
				s["running"] = true
				s["progress"] = 0.0
			else:
				break
		var cycle: float = d["cycle"]
		var remaining := cycle - float(s["progress"])
		if t < remaining:
			s["progress"] = float(s["progress"]) + t
			t = 0.0
			break
		t -= remaining
		var n := 1
		if d["auto_sell"]:
			var extra := int(t / cycle)
			n += extra
			t -= extra * cycle
		_complete(m, id, s, d, n)
		s["progress"] = 0.0
		s["running"] = false
		if d["auto_restock"]:
			_maybe_auto_restock(m, id, s, d)
		if not d["auto_sell"]:
			break
	if d["auto_restock"]:
		_maybe_auto_restock(m, id, s, d)
	var empty: bool = not m.has_stock(id) and s["orders"].is_empty()
	if empty != bool(s.get("stockout", false)):
		s["stockout"] = empty
		if empty:
			m._count("stockouts", 1)
		m.business_changed.emit(id)


static func _advance_orders(m: GameModel, id: String, s: Dictionary, dt: float) -> void:
	if s["orders"].is_empty():
		return
	var arrived := []
	for pid in s["orders"]:
		var o: Dictionary = s["orders"][pid]
		o["eta"] = float(o["eta"]) - dt
		if o["eta"] <= 0.0:
			arrived.append(pid)
	for pid in arrived:
		s["stock"][pid] = float(s["stock"].get(pid, 0.0)) + float(s["orders"][pid]["units"])
		s["orders"].erase(pid)
	if not arrived.is_empty():
		m.business_changed.emit(id)


static func _complete(m: GameModel, id: String, s: Dictionary, d: Dictionary, n: int) -> void:
	var revenue := 0.0
	var sold_total := 0.0
	var def: Dictionary = m.data.business_by_id[id]
	for i in d["products"].size():
		var p: Dictionary = d["products"][i]
		var want: float = p["u"] * n
		var have := float(s["stock"].get(p["id"], 0.0))
		var sold := minf(want, have)
		if sold <= 0.0:
			continue
		s["stock"][p["id"]] = maxf(0.0, have - sold)
		revenue += sold * float(p["price"])
		sold_total += sold
		m._count("sold:" + p["id"], sold)
		for tag in def["products"][i]["tags"]:
			m._count("sold_tag:" + tag, sold)
	if sold_total <= 0.0:
		return
	var total := revenue + float(s["carry"])
	var whole := Economy.to_int_floor(total)
	s["carry"] = clampf(total - whole, 0.0, 1.0)
	var credited := m.economy.earn(whole, "ventas")
	s["earned"] = Economy.sat_add(int(s["earned"]), credited)
	s["sales"] = int(s["sales"]) + n
	m._count("sales_total", n)
	if not m.events["active"].is_empty() and EventSystem.affects(m, id):
		m._count("event_sales", n)
	m.sale.emit(id, credited)


static func _maybe_auto_restock(m: GameModel, id: String, s: Dictionary, d: Dictionary) -> void:
	var threshold := float(m.data.balance["restock_threshold"])
	for p in d["products"]:
		if s["orders"].has(p["id"]):
			continue
		if float(s["stock"].get(p["id"], 0.0)) < float(p["cap"]) * threshold:
			m.restock(id, true)
			return
