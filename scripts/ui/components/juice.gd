class_name Juice
extends RefCounted
## Animaciones de festejo sobre tarjetas de la interfaz (sólo visuales):
## - gold_shine: la tarjeta brilla unos segundos con un barrido dorado en
##   degradé (mejora comprada).
## - mission_done: la tarjeta se llena de verde, aparece un tick y se desliza
##   hacia la izquierda antes de desaparecer (misión reclamada).
## Con "Reducir movimiento" se acortan y no hay desplazamientos.

const SHINE_TIME := 2.4
const SHINE_SWEEPS := 3

## Barrido diagonal con degradé dorado (ocre -> oro -> crema) y bordes en
## escalones de 1/4 para que se vea pixelado como el resto del juego.
const SHINE_SHADER := """
shader_type canvas_item;
uniform float sweep = 0.0;      // 0..1: posición del barrido
uniform float strength = 1.0;   // se apaga al final
uniform vec2 px_size = vec2(300.0, 100.0);
void fragment() {
	vec2 p = floor(UV * px_size / 2.0) * 2.0 / px_size;   // bloques de 2 px
	float d = p.x + p.y * 0.4 - (sweep * 2.2 - 0.6);
	float band = abs(d);
	float a = clamp(1.0 - band / 0.32, 0.0, 1.0);
	a = floor(a * 4.0) / 4.0;
	vec3 deep = vec3(0.80, 0.50, 0.10);
	vec3 gold = vec3(1.00, 0.84, 0.36);
	vec3 pale = vec3(1.00, 0.97, 0.80);
	vec3 c = mix(deep, gold, clamp(1.0 - band / 0.2, 0.0, 1.0));
	c = mix(c, pale, step(band, 0.05));
	COLOR = vec4(c, (0.16 + a * 0.62) * strength);
}
"""

static var _shader: Shader


static func _reduced() -> bool:
	return bool(Settings.get_value("reduce_motion"))


## Capa que cubre TODA la tarjeta (también los márgenes del estilo): el
## contenedor la estira al área de contenido y el hijo se sale hacia afuera.
static func _overlay(card: Control) -> Array:
	var holder := Control.new()
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.add_child(holder)
	var sb := card.get_theme_stylebox("panel") if card is PanelContainer else null
	var ml := sb.content_margin_left if sb else 0.0
	var mt := sb.content_margin_top if sb else 0.0
	var mr := sb.content_margin_right if sb else 0.0
	var mb := sb.content_margin_bottom if sb else 0.0
	var rect := ColorRect.new()
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.add_child(rect)
	var fit := func() -> void:
		rect.position = Vector2(-ml, -mt)
		rect.size = holder.size + Vector2(ml + mr, mt + mb)
	holder.resized.connect(fit)
	fit.call()
	return [holder, rect]


## La tarjeta brilla con barridos dorados durante SHINE_TIME segundos.
static func gold_shine(card: Control) -> void:
	if _shader == null:
		_shader = Shader.new()
		_shader.code = SHINE_SHADER
	var parts := _overlay(card)
	var holder: Control = parts[0]
	var rect: ColorRect = parts[1]
	var mat := ShaderMaterial.new()
	mat.shader = _shader
	rect.material = mat
	var set_size := func() -> void: mat.set_shader_parameter("px_size", rect.size)
	rect.resized.connect(set_size)
	set_size.call()
	var sweeps := 1 if _reduced() else SHINE_SWEEPS
	var each := SHINE_TIME / SHINE_SWEEPS
	var tw := holder.create_tween()
	for i in sweeps:
		tw.tween_method(func(v: float) -> void: mat.set_shader_parameter("sweep", v), 0.0, 1.0, each).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.tween_method(func(v: float) -> void: mat.set_shader_parameter("strength", v), 1.0, 0.0, 0.5)
	tw.tween_callback(holder.queue_free)
	# Un saltito dorado al empezar.
	if not _reduced():
		var pop := card.create_tween()
		pop.tween_callback(func() -> void: card.pivot_offset = card.size / 2.0)
		pop.tween_property(card, "scale", Vector2(1.03, 1.03), 0.12).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		pop.tween_property(card, "scale", Vector2.ONE, 0.25)


## Misión reclamada: relleno verde de izquierda a derecha, tick que aparece
## con rebote y la tarjeta sale deslizándose a la izquierda. Al terminar se
## llama on_done (la pantalla se rearma ahí).
static func mission_done(card: Control, on_done: Callable) -> void:
	# on_done se llama UNA vez aunque la tarjeta se borre a mitad de la
	# animación (cambio de pestaña, rearmado de la lista): si no, quien espera
	# el aviso (Objetivos) queda trabado y no deja reclamar nada más.
	var once := {"done": false}
	var finish := func() -> void:
		if not once["done"]:
			once["done"] = true
			on_done.call()
	card.tree_exiting.connect(finish, CONNECT_ONE_SHOT)
	on_done = finish
	var parts := _overlay(card)
	var holder: Control = parts[0]
	var fill: ColorRect = parts[1]
	fill.color = Color(0.30, 0.69, 0.36, 0.82)
	fill.size.x = 0.0
	# La capa recién agregada recibe su tamaño en el próximo acomodo del contenedor.
	if not card.is_inside_tree():
		on_done.call()
		return
	await card.get_tree().process_frame
	if not is_instance_valid(card):
		on_done.call()
		return
	var full_w := fill.size.x
	fill.size.x = 0.0
	var tick := U.icon32("check")
	tick.pivot_offset = tick.custom_minimum_size / 2.0
	tick.scale = Vector2.ZERO
	holder.add_child(tick)
	tick.position = (holder.size - tick.custom_minimum_size) / 2.0
	var fast := _reduced()
	var tw := card.create_tween()
	tw.tween_method(func(w: float) -> void: fill.size.x = roundf(w), 0.0, full_w, 0.15 if fast else 0.45).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tw.tween_property(tick, "scale", Vector2(2.0, 2.0), 0.1 if fast else 0.22).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_interval(0.15 if fast else 0.35)
	if fast:
		tw.tween_property(card, "modulate:a", 0.0, 0.15)
	else:
		tw.tween_property(card, "position:x", card.position.x - card.size.x - 24.0, 0.35).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_IN)
		tw.parallel().tween_property(card, "modulate:a", 0.0, 0.35)
	tw.tween_callback(on_done)
