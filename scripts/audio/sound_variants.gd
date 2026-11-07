class_name SoundVariants
extends RefCounted
## Sonidos con varias versiones (15.0): assets/audio/<nombre>_0.wav, _1... Cada
## vez suena UNA, al azar y sin repetir la anterior. Lo usa Sfx.

const DIR := "res://assets/audio/"


## Rutas de las versiones que existen de `name` (hasta `count`).
static func paths(name: String, count: int) -> Array:
	var out := []
	for i in count:
		var p := "%s%s_%d.wav" % [DIR, name, i]
		if ResourceLoader.exists(p):
			out.append(p)
	return out


## Índice del reproductor al que le queda menos por sonar (0.0 = libre).
static func least_busy(time_left: Array) -> int:
	return time_left.find(time_left.min())


## Índice de la próxima versión: al azar, distinto de `last` si hay más de una.
static func pick(count: int, last: int) -> int:
	if count <= 1:
		return 0
	var i := randi() % count
	if i == last:
		i = (i + 1 + randi() % (count - 1)) % count
	return i
