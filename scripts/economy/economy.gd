class_name Economy
extends RefCounted
## Sistema económico central. TODA entrada o salida de dinero pasa por acá.
##
## - El saldo es un entero de 64 bits en pesos enteros: no hay errores de
##   redondeo acumulados. Las fracciones (precios con centavos, bonificaciones)
##   se acumulan aparte en cada negocio ("carry") y se acreditan al llegar a $1.
## - Tope de seguridad: max_money (1e18 = un trillón). Nunca hay desborde ni
##   saldo negativo: spend() rechaza si no alcanza, earn() satura en el tope.
## - Ver docs/ECONOMIA.md para la estrategia de números grandes.

signal changed(money: int, delta: int)

const LEDGER_MAX := 40
const INT_SAFE := 9_000_000_000_000_000_000

var money: int = 0
var max_money: int = 1_000_000_000_000_000_000
var run_earned: int = 0          ## ganado en esta partida (se reinicia con prestigio)
var lifetime_earned: int = 0     ## histórico, nunca se reinicia
var run_spent: int = 0
var income_by_source := {}       ## categoría -> int (esta partida)
var expense_by_reason := {}      ## categoría -> int (esta partida)
var ledger: Array = []           ## últimas transacciones [{t, amount, cat}]
var clock: Callable = func() -> float: return Time.get_unix_time_from_system()


func can_afford(amount: int) -> bool:
	return amount >= 0 and money >= amount


## Acredita dinero. Devuelve lo realmente acreditado (puede ser menos si se
## llega al tope). counts_as_income=false para devoluciones que no son ganancias.
func earn(amount: int, category: String, counts_as_income := true) -> int:
	if amount <= 0:
		return 0
	var credited := mini(amount, max_money - money)
	if credited <= 0:
		return 0
	money += credited
	if counts_as_income:
		run_earned = sat_add(run_earned, credited)
		lifetime_earned = sat_add(lifetime_earned, credited)
		income_by_source[category] = sat_add(int(income_by_source.get(category, 0)), credited)
	_log(credited, category)
	changed.emit(money, credited)
	return credited


## Gasta sólo si alcanza. Nunca deja el saldo negativo.
func spend(amount: int, category: String) -> bool:
	if amount < 0:
		return false
	if amount == 0:
		return true
	if money < amount:
		return false
	money -= amount
	run_spent = sat_add(run_spent, amount)
	expense_by_reason[category] = sat_add(int(expense_by_reason.get(category, 0)), amount)
	_log(-amount, category)
	changed.emit(money, -amount)
	return true


## Paga hasta donde alcance (sueldos). Devuelve lo pagado.
func spend_up_to(amount: int, category: String) -> int:
	var paid := mini(maxi(amount, 0), money)
	if paid > 0:
		spend(paid, category)
	return paid


func reset_run(start_money: int) -> void:
	money = clampi(start_money, 0, max_money)
	run_earned = 0
	run_spent = 0
	income_by_source.clear()
	expense_by_reason.clear()
	ledger.clear()
	changed.emit(money, 0)


func _log(amount: int, cat: String) -> void:
	# Las ventas son muy frecuentes: se agrupan con la última entrada igual.
	if not ledger.is_empty():
		var last: Dictionary = ledger[-1]
		if last["cat"] == cat and sign(last["amount"]) == sign(amount) and clock.call() - float(last["t"]) < 5.0:
			last["amount"] = sat_add(int(last["amount"]), amount)
			return
	ledger.append({"t": clock.call(), "amount": amount, "cat": cat})
	if ledger.size() > LEDGER_MAX:
		ledger.pop_front()


## Convierte un monto calculado en float a entero sin desbordar.
static func to_int_ceil(x: float) -> int:
	if is_nan(x) or x <= 0.0:
		return 0
	if x >= 9.0e18:
		return INT_SAFE
	return int(ceilf(x - 1e-9))


static func to_int_floor(x: float) -> int:
	if is_nan(x) or x <= 0.0:
		return 0
	if x >= 9.0e18:
		return INT_SAFE
	return int(floorf(x + 1e-9))


static func sat_add(a: int, b: int) -> int:
	if b > 0 and a > INT_SAFE - b:
		return INT_SAFE
	return a + b


func to_dict() -> Dictionary:
	return {
		"money": str(money),
		"run_earned": str(run_earned),
		"lifetime_earned": str(lifetime_earned),
		"run_spent": str(run_spent),
		"income_by_source": _stringify(income_by_source),
		"expense_by_reason": _stringify(expense_by_reason),
	}


func from_dict(d: Dictionary) -> void:
	money = clampi(s2i(d.get("money", 0)), 0, max_money)
	run_earned = maxi(s2i(d.get("run_earned", 0)), 0)
	lifetime_earned = maxi(s2i(d.get("lifetime_earned", 0)), run_earned)
	run_spent = maxi(s2i(d.get("run_spent", 0)), 0)
	income_by_source = _parse(d.get("income_by_source", {}))
	expense_by_reason = _parse(d.get("expense_by_reason", {}))
	ledger.clear()


## Los enteros grandes se guardan como texto: JSON los leería como float y
## perdería precisión por encima de 2^53.
static func s2i(v: Variant) -> int:
	if v is String:
		return (v as String).to_int()
	if v is float or v is int:
		return int(v)
	return 0


static func _stringify(d: Dictionary) -> Dictionary:
	var out := {}
	for k in d:
		out[k] = str(d[k])
	return out


static func _parse(d: Variant) -> Dictionary:
	var out := {}
	if d is Dictionary:
		for k in d:
			out[k] = maxi(s2i(d[k]), 0)
	return out
