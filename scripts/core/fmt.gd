class_name Fmt
extends RefCounted
## Formato de números, dinero y tiempos para la interfaz (español rioplatense).
## Sólo presentación: la lógica nunca lee estos textos.

const SUFFIXES := [
	[1e18, "T"],
	[1e15, "mil B"],
	[1e12, "B"],
	[1e9, "mil M"],
	[1e6, "M"],
	[1e3, "mil"],
]


## Saldo: redondea hacia abajo para no mostrar plata que no hay. Los montos
## negativos llevan el signo adelante: "-$1,2 mil".
static func money(v: float) -> String:
	return ("-$" + num(-v, true)) if v < 0.0 else ("$" + num(v, false))


## Precio: redondea hacia arriba para que "me alcanza" sea confiable a la vista.
static func cost(v: float) -> String:
	return ("-$" + num(-v, false)) if v < 0.0 else ("$" + num(v, true))


static func per_sec(v: float) -> String:
	return ("-$" + num(-v, true) if v < 0.0 else "$" + num(v, false)) + "/s"


static func num(v: float, round_up := false) -> String:
	var neg := v < 0.0
	var a := absf(v)
	var s := ""
	if a < 1000.0:
		if a < 10.0:
			s = _dec(a, round_up)
		else:
			s = str(int(ceilf(a - 0.0001) if round_up else floorf(a + 0.0001)))
	else:
		for pair in SUFFIXES:
			var unit: float = pair[0]
			if a >= unit:
				var x := a / unit
				s = (_dec(x, round_up) if x < 100.0 else str(int(ceilf(x) if round_up else floorf(x)))) + " " + pair[1]
				break
	return ("-" if neg else "") + s


static func _dec(x: float, round_up: bool) -> String:
	var t := (ceilf(x * 10.0 - 0.0001) if round_up else floorf(x * 10.0 + 0.0001)) / 10.0
	if absf(t - roundf(t)) < 0.001:
		return str(int(roundf(t)))
	return ("%.1f" % t).replace(".", ",")


static func integer(v: float) -> String:
	## 12345 -> "12.345"
	var s := str(int(floorf(absf(v))))
	var out := ""
	var count := 0
	for i in range(s.length() - 1, -1, -1):
		out = s[i] + out
		count += 1
		if count % 3 == 0 and i > 0:
			out = "." + out
	return ("-" if v < 0 else "") + out


static func duration(seconds: float) -> String:
	var s := int(maxf(seconds, 0.0))
	if s < 60:
		return "%d s" % s
	if s < 3600:
		var m := s / 60
		var r := s % 60
		return ("%d min" % m) if r == 0 else ("%d min %d s" % [m, r])
	var h := s / 3600
	var mm := (s % 3600) / 60
	return ("%d h" % h) if mm == 0 else ("%d h %d min" % [h, mm])


static func cycle(seconds: float) -> String:
	if seconds < 10.0:
		return ("%.1f s" % seconds).replace(".", ",")
	return duration(seconds)


static func percent(v: float) -> String:
	return "%d %%" % int(roundf(v * 100.0))
