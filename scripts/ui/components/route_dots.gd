class_name RouteDots
extends Control
## Puntitos dorados que marchan entre las provincias de una región (orden de
## conquista). Ambiental: sin toques; quieto con "Reducir movimiento".

var points: Array = []
var _t := 0.0
var _frame := 0


func _process(delta: float) -> void:
	if not is_visible_in_tree() or Settings.get_value("reduce_motion"):
		return
	_t += delta
	_frame += 1
	if _frame % 3 == 0:                          # redibuja cada 3 cuadros
		queue_redraw()


func _draw() -> void:
	for i in range(points.size() - 1):
		var a: Vector2 = points[i]
		var b: Vector2 = points[i + 1]
		var n := int(a.distance_to(b) / 7.0)
		var gap := 20.0 / maxf(1.0, a.distance_to(b))   # no pisa los pines ni sus rótulos
		for k in n:
			var f := (float(k) + fmod(_t * 1.5, 1.0)) / float(maxi(1, n))
			if f < gap or f > 1.0 - gap:
				continue
			var p := a.lerp(b, f).round()
			draw_rect(Rect2(p - Vector2(1, 1), Vector2(3, 3)), Color("3d1b0b"))
			draw_rect(Rect2(p, Vector2(1, 1)), Color("f7eda4"))
