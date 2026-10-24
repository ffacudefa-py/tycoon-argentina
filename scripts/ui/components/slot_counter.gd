class_name SlotCounter
extends HBoxContainer
## Saldo con rodillos de tragamonedas: cada dígito que cambia gira hasta el
## valor nuevo (con un rebote al frenar) y se ilumina en dorado. Los rodillos
## frenan de izquierda a derecha, como en una máquina de casino; en un premio
## grande dan vueltas completas antes de frenar.
##
## Sólo visual: muestra un texto ya formateado (Fmt.money) y no calcula nada.
## Cada carácter es una celda que recorta su contenido (clip_contents) con
## dos etiquetas: el dígito que sale hacia arriba y el que entra desde abajo.

signal reel_stopped(index: int)

const ROLL_TIME := 0.42      ## un rodillo que avanza poco
const SPIN_TIME := 1.1       ## un rodillo en premio grande (con vueltas extra)
const STAGGER := 0.06        ## cada rodillo frena un poco después del anterior
const FLASH_TIME := 0.7
const GOLD := Color("ffd85c")

var font_size := U.SIZE_BIG
var color := Color.WHITE

var _text := ""
## Una celda por carácter: {box, cur, nxt, ch, pos, from, to, t, dur, delay, flash}.
var _cells: Array = []
var _line_h := 0.0


func _init() -> void:
	add_theme_constant_override("separation", 0)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	size_flags_vertical = Control.SIZE_SHRINK_CENTER


func is_spinning() -> bool:
	for c in _cells:
		if c["t"] < c["dur"]:
			return true
	return false


func _label() -> Label:
	var l := U.label("", font_size, color, true)
	l.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


func _make_cell() -> Dictionary:
	var box := Control.new()
	box.clip_contents = true
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var cur := _label()
	var nxt := _label()
	box.add_child(cur)
	box.add_child(nxt)
	add_child(box)
	var cw: float = cur.get_theme_font("font").get_string_size("0", HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x
	_line_h = cur.get_combined_minimum_size().y
	box.custom_minimum_size = Vector2(cw, _line_h)
	return {"box": box, "cur": cur, "nxt": nxt, "ch": "", "pos": 0.0, "from": 0.0, "to": 0.0,
		"t": 0.0, "dur": 0.0, "delay": 0.0, "flash": 0.0}


## Cambia el texto. animate=false lo pone de golpe (al cargar la partida);
## big=true hace girar los rodillos varias vueltas (premios grandes).
func set_text(s: String, animate := true, big := false) -> void:
	if s == _text:
		return
	var old := _text
	_text = s
	while _cells.size() < s.length():
		_cells.append(_make_cell())
	while _cells.size() > s.length():
		var c: Dictionary = _cells.pop_back()
		c["box"].queue_free()
	var shift := s.length() - old.length()       # se alinea a la derecha
	var order := 0
	for i in s.length():
		var c: Dictionary = _cells[i]
		var ch := s[i]
		var j := i - shift
		var prev := old[j] if j >= 0 and j < old.length() else ""
		c["ch"] = ch
		c["t"] = 0.0
		c["dur"] = 0.0
		if animate and ch.is_valid_int() and (prev != ch or big):
			var a := int(prev) if prev.is_valid_int() else 0
			var steps := (int(ch) - a + 10) % 10
			if big:
				steps += 10 * (2 + order % 2)
			elif steps == 0:
				steps = 10
			c["from"] = float(a)
			c["to"] = float(a + steps)
			c["pos"] = c["from"]
			c["delay"] = order * STAGGER
			c["dur"] = (SPIN_TIME if big else ROLL_TIME) + c["delay"]
			c["flash"] = 1.0
			order += 1
		elif animate and prev != ch:
			c["flash"] = 1.0
		_paint(c)


func _process(delta: float) -> void:
	for i in _cells.size():
		var c: Dictionary = _cells[i]
		var busy := false
		if c["flash"] > 0.0:
			c["flash"] = maxf(0.0, c["flash"] - delta / FLASH_TIME)
			busy = true
		if c["t"] < c["dur"]:
			c["t"] = minf(c["dur"], c["t"] + delta)
			var k := clampf((c["t"] - c["delay"]) / maxf(0.01, c["dur"] - c["delay"]), 0.0, 1.0)
			c["pos"] = lerpf(c["from"], c["to"], _ease_out_back(k))
			if c["t"] >= c["dur"]:
				reel_stopped.emit(i)
			busy = true
		if busy:
			_paint(c)


## Llega un poco más allá y vuelve: el "clac" del rodillo al frenar.
static func _ease_out_back(k: float) -> float:
	var c1 := 1.4
	var c3 := c1 + 1.0
	return 1.0 + c3 * pow(k - 1.0, 3) + c1 * pow(k - 1.0, 2)


func _paint(c: Dictionary) -> void:
	var cur: Label = c["cur"]
	var nxt: Label = c["nxt"]
	var col := color.lerp(GOLD, c["flash"])
	cur.add_theme_color_override("font_color", col)
	nxt.add_theme_color_override("font_color", col)
	if c["t"] < c["dur"]:
		# Rodillo girando: el dígito actual sube y entra el siguiente desde abajo.
		var p: float = c["pos"]
		var d0 := posmod(int(floorf(p)), 10)
		var off := roundf((p - floorf(p)) * _line_h)
		cur.text = str(d0)
		nxt.text = str((d0 + 1) % 10)
		cur.position.y = -off
		nxt.position.y = _line_h - off
		nxt.visible = true
	else:
		cur.text = c["ch"]
		cur.position.y = 0
		nxt.visible = false
