class_name SlotCounter
extends HBoxContainer
## Saldo con rodillos de tragamonedas: cada carácter va en su propia ventanita
## (un rodillo con degradé de cilindro laqueado y dígitos de metal con contorno
## y sombra; ver DIGIT_SHADER) separada de la
## siguiente por una barra dorada. Cada dígito que cambia gira hasta el valor
## nuevo (borroso mientras va rápido, con un rebote al frenar) y se ilumina en
## dorado. Los rodillos frenan de izquierda a derecha, como en una máquina de
## casino; en un premio grande dan vueltas completas antes de frenar.
##
## Sólo visual: muestra un texto ya formateado (Fmt.money) y no calcula nada.
## Cada celda recorta su contenido (clip_contents) y tiene dos etiquetas: el
## dígito que sale hacia arriba y el que entra desde abajo. Los espacios
## ("12,5 M") cortan la tira de rodillos en vez de ocupar una ventanita.

signal reel_stopped(index: int)

const ROLL_TIME := 0.42      ## un rodillo que avanza poco
const SPIN_TIME := 1.1       ## un rodillo en premio grande (con vueltas extra)
const STAGGER := 0.06        ## cada rodillo frena un poco después del anterior
const FLASH_TIME := 0.7
const GOLD := Color("ffd85c")
const PAD := 1               ## aire a cada lado del dígito dentro del rodillo
const BAR_W := 2
const BAR := Color("c8963e")
## Fondo de cada rodillo: oscuro en los bordes, con un brillo arriba del
## centro, como un cilindro laqueado iluminado desde arriba.
const FACE_STOPS := [[0.0, "0d0603"], [0.16, "2a170c"], [0.34, "5c3a22"], [0.5, "35200f"], [0.82, "1c0f07"], [1.0, "080402"]]
const OUTLINE := Color("1a0b04")
const GAP_W := 5             ## ancho del corte que deja un espacio
## Dígitos por segundo a partir de los cuales el rodillo se ve borroso.
const BLUR_SPEED := 18.0

var font_size := U.SIZE_BIG
var color := Color.WHITE

var _text := ""
## Una celda por carácter: {bar, box, face, shade, cur, nxt, ch, pos, from, to,
## t, dur, delay, flash, speed}.
var _cells: Array = []
var _line_h := 0.0
var _digit_w := 0.0

## Recursos compartidos por todos los rodillos.
static var _shade_tex: GradientTexture2D
static var _face_tex: GradientTexture2D
static var _digit_mat: ShaderMaterial

## Dígitos de metal: el color base se ilumina arriba y se vuelve dorado abajo,
## con un corte de brillo a media altura (como los números de una máquina
## de casino). Multiplica el color, así que el contorno y la sombra oscuros
## quedan oscuros y el rojo del saldo negativo sigue siendo rojo.
const DIGIT_SHADER := """
shader_type canvas_item;
uniform float top = 0.0;
uniform float bottom = 32.0;
varying float ly;
void vertex() { ly = VERTEX.y; }
void fragment() {
	float t = clamp((ly - top) / max(bottom - top, 1.0), 0.0, 1.0);
	vec3 hi = vec3(1.0);
	vec3 mid = vec3(1.0, 0.86, 0.6);
	vec3 lo = vec3(0.95, 0.66, 0.28);
	vec3 k = t < 0.5 ? mix(hi, mid, t * 2.0) : mix(vec3(0.82, 0.6, 0.3), lo, (t - 0.5) * 2.0);
	COLOR.rgb *= k;
}
"""


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
	var l := U.label("", font_size, color, true, HORIZONTAL_ALIGNMENT_CENTER)
	l.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	l.add_theme_color_override("font_outline_color", OUTLINE)
	l.add_theme_constant_override("outline_size", 4)
	l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.7))
	l.add_theme_constant_override("shadow_offset_x", 0)
	l.add_theme_constant_override("shadow_offset_y", 2)
	l.material = _digit_mat
	return l


static func _vertical(offsets: Array, colors: Array) -> GradientTexture2D:
	var g := Gradient.new()
	g.offsets = PackedFloat32Array(offsets)
	g.colors = PackedColorArray(colors)
	var t := GradientTexture2D.new()
	t.gradient = g
	t.fill_from = Vector2(0, 0)
	t.fill_to = Vector2(0, 1)
	t.width = 4
	t.height = 64
	return t


## Sombra que oscurece los dígitos al entrar y salir del rodillo.
static func _shade() -> GradientTexture2D:
	if _shade_tex == null:
		var clear := Color(0, 0, 0, 0)
		_shade_tex = _vertical([0.0, 0.26, 0.74, 1.0], [Color(0, 0, 0, 0.55), clear, clear, Color(0, 0, 0, 0.55)])
	return _shade_tex


static func _face() -> GradientTexture2D:
	if _face_tex == null:
		var offs := []
		var cols := []
		for st in FACE_STOPS:
			offs.append(st[0])
			cols.append(Color(st[1]))
		_face_tex = _vertical(offs, cols)
	return _face_tex


func _make_cell() -> Dictionary:
	var bar := ColorRect.new()
	bar.color = BAR
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bar)
	var box := Control.new()
	box.clip_contents = true
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var face := TextureRect.new()
	face.texture = _face()
	face.stretch_mode = TextureRect.STRETCH_SCALE
	face.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	face.mouse_filter = Control.MOUSE_FILTER_IGNORE
	face.set_anchors_preset(Control.PRESET_FULL_RECT)
	if _digit_mat == null:
		var sh := Shader.new()
		sh.code = DIGIT_SHADER
		_digit_mat = ShaderMaterial.new()
		_digit_mat.shader = sh
	var cur := _label()
	var nxt := _label()
	var shade := TextureRect.new()
	shade.texture = _shade()
	shade.stretch_mode = TextureRect.STRETCH_SCALE
	shade.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	for n in [face, cur, nxt, shade]:
		box.add_child(n)
	add_child(box)
	if _line_h == 0.0:
		_digit_w = cur.get_theme_font("font").get_string_size("0", HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x
		_line_h = cur.get_combined_minimum_size().y
		# El degradé de los dígitos va del alto de las mayúsculas a la base.
		var font := cur.get_theme_font("font")
		var asc := font.get_ascent(font_size)
		_digit_mat.set_shader_parameter("top", asc * 0.3)
		_digit_mat.set_shader_parameter("bottom", asc)
	bar.custom_minimum_size = Vector2(BAR_W, _line_h)
	return {"bar": bar, "box": box, "face": face, "shade": shade, "cur": cur, "nxt": nxt,
		"ch": "", "pos": 0.0, "from": 0.0, "to": 0.0, "t": 0.0, "dur": 0.0, "delay": 0.0,
		"flash": 0.0, "speed": 0.0}


## Color base de los dígitos (rojo para saldo negativo).
func set_color(c: Color) -> void:
	if c == color:
		return
	color = c
	for cell in _cells:
		_paint(cell)


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
		c["bar"].queue_free()
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
		_layout(c, i)
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


## Ventanita de rodillo para cada carácter; un espacio es un corte sin rodillo
## y sin barras a sus lados.
func _layout(c: Dictionary, i: int) -> void:
	var gap: bool = c["ch"] == " "
	var box: Control = c["box"]
	box.custom_minimum_size = Vector2(GAP_W if gap else _digit_w + PAD * 2, _line_h)
	c["face"].visible = not gap
	c["shade"].visible = not gap
	c["cur"].size = Vector2(box.custom_minimum_size.x, _line_h)
	c["nxt"].size = c["cur"].size
	c["bar"].visible = i > 0 and not gap and _text[i - 1] != " "


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
			var p := lerpf(c["from"], c["to"], _ease_out_back(k))
			c["speed"] = absf(p - c["pos"]) / maxf(delta, 0.001)
			c["pos"] = p
			if c["t"] >= c["dur"]:
				c["speed"] = 0.0
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
	# El rodillo se aclara un poco al frenar: el "destello" del premio.
	c["face"].modulate = Color.WHITE.lerp(Color(1.9, 1.6, 1.1), c["flash"] * 0.7)
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
		# Borroso a toda velocidad: los dígitos se ven a medias.
		var blur := clampf(c["speed"] / BLUR_SPEED, 0.0, 1.0)
		cur.modulate.a = 1.0 - 0.45 * blur
		nxt.modulate.a = cur.modulate.a
	else:
		cur.text = c["ch"]
		cur.position.y = 0
		cur.modulate.a = 1.0
		nxt.visible = false
