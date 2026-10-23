class_name CropMath
extends RefCounted
## Matemática del recorte (pura, sin nodos: se prueba en tests/).
##
## La imagen se muestra escalada por `scale` (píxeles de pantalla por píxel de
## imagen) y desplazada por `offset` (posición de la esquina superior izquierda
## de la imagen respecto de la esquina del marco). El marco de recorte mide
## `frame` píxeles de pantalla. Reglas:
##   - la imagen siempre cubre el marco (nunca quedan bordes vacíos);
##   - el zoom mínimo es el que justo cubre el marco ("cover");
##   - el zoom máximo es 8 veces ese mínimo.

const MAX_ZOOM := 8.0


static func min_scale(img_size: Vector2, frame: Vector2) -> float:
	return maxf(frame.x / img_size.x, frame.y / img_size.y)


static func clamp_scale(scale: float, img_size: Vector2, frame: Vector2) -> float:
	var lo := min_scale(img_size, frame)
	return clampf(scale, lo, lo * MAX_ZOOM)


## Limita el desplazamiento para que la imagen cubra todo el marco.
static func clamp_offset(offset: Vector2, scale: float, img_size: Vector2, frame: Vector2) -> Vector2:
	var shown := img_size * scale
	return Vector2(clampf(offset.x, frame.x - shown.x, 0.0), clampf(offset.y, frame.y - shown.y, 0.0))


## Encuadre inicial: centrado y con el zoom mínimo.
static func initial(img_size: Vector2, frame: Vector2) -> Dictionary:
	var s := min_scale(img_size, frame)
	return {"scale": s, "offset": (frame - img_size * s) / 2.0}


## Zoom alrededor de un punto del marco (el punto bajo los dedos queda quieto).
static func zoom_at(scale: float, offset: Vector2, factor: float, pivot: Vector2, img_size: Vector2, frame: Vector2) -> Dictionary:
	var new_scale := clamp_scale(scale * factor, img_size, frame)
	var real := new_scale / scale
	var new_offset := pivot - (pivot - offset) * real
	return {"scale": new_scale, "offset": clamp_offset(new_offset, new_scale, img_size, frame)}


## Rectángulo de la imagen original que queda dentro del marco.
static func source_rect(scale: float, offset: Vector2, img_size: Vector2, frame: Vector2) -> Rect2i:
	var pos := -offset / scale
	var size := frame / scale
	var r := Rect2(pos, size)
	r.position = r.position.clamp(Vector2.ZERO, img_size)
	r.size = r.size.min(img_size - r.position)
	return Rect2i(r.position.round(), r.size.round()).intersection(Rect2i(Vector2i.ZERO, Vector2i(img_size)))
