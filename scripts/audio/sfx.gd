extends Node
## Autoload "Sfx": efectos de sonido (sintetizados para el proyecto, ver
## tools/sfx.py) y vibración. No hay música en esta versión.

const NAMES := ["tap", "coin", "buy", "upgrade", "unlock", "hire", "mission", "error", "event", "register", "tier", "whoosh"]
const POOL := 6

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _last_play := {}


func _ready() -> void:
	for n in NAMES:
		var p := "res://assets/audio/%s.wav" % n
		if ResourceLoader.exists(p):
			_streams[n] = load(p)
	for i in POOL:
		var pl := AudioStreamPlayer.new()
		pl.bus = "SFX"
		add_child(pl)
		_players.append(pl)


## Reproduce un efecto. Limita repeticiones muy seguidas del mismo sonido
## (p. ej. muchas ventas por segundo) para no saturar.
func play(name: String, pitch := 1.0, min_gap := 0.05) -> void:
	if not Settings.get_value("sfx_enabled") or not _streams.has(name):
		return
	var t := Time.get_ticks_msec() / 1000.0
	if t - float(_last_play.get(name, -10.0)) < min_gap:
		return
	_last_play[name] = t
	var pl := _players[_next]
	_next = (_next + 1) % POOL
	pl.stream = _streams[name]
	pl.pitch_scale = pitch
	pl.play()


func vibrate(ms := 30) -> void:
	if Settings.get_value("vibration") and OS.has_feature("mobile"):
		Input.vibrate_handheld(ms)
