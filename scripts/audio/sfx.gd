extends Node
## Autoload "Sfx": efectos de sonido (sintetizados en tools/sfx.py o exportados
## de FL Studio, ver tools/audio/import_sfx.py) y vibración. La música la maneja
## el autoload Music.

const NAMES := ["tap", "coin", "buy", "upgrade", "unlock", "hire", "mission", "error", "event", "register", "tier", "whoosh",
	"shot", "hit", "ricochet", "empty", "reload", "bag", "alarm", "siren", "swipe", "shred", "stamp", "buzzer", "tick"]
const POOL := 6
## Sonidos con varias versiones (assets/audio/<nombre>_0.wav, _1...): cada vez
## suena UNA, elegida al azar sin repetir la anterior, con el tono un poco
## cambiado. "coin" = los 5 golpes de coin.mp3 (tools/audio/split_coin.sh).
const VARIANTS := {"coin": 5}
const VARIANT_PITCH := 0.06

var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _last_play := {}
var _variants := {}          ## nombre -> [streams]
var _last_variant := {}


func _ready() -> void:
	for n in NAMES:
		var p := "res://assets/audio/%s.wav" % n
		if ResourceLoader.exists(p):
			_streams[n] = load(p)
	for n in VARIANTS:
		var list := SoundVariants.paths(n, int(VARIANTS[n])).map(func(p: String) -> AudioStream: return load(p))
		if not list.is_empty():
			_variants[n] = list
	for i in POOL:
		var pl := AudioStreamPlayer.new()
		pl.bus = "SFX"
		add_child(pl)
		_players.append(pl)


## Reproduce un efecto. Limita repeticiones muy seguidas del mismo sonido
## (p. ej. muchas ventas por segundo) para no saturar.
func play(name: String, pitch := 1.0, min_gap := 0.05) -> void:
	if not Settings.get_value("sfx_enabled") or not (_streams.has(name) or _variants.has(name)):
		return
	var t := Time.get_ticks_msec() / 1000.0
	if t - float(_last_play.get(name, -10.0)) < min_gap:
		return
	_last_play[name] = t
	var pl := _free_player()
	if _variants.has(name):
		pl.stream = _pick_variant(name)
		pitch *= randf_range(1.0 - VARIANT_PITCH, 1.0 + VARIANT_PITCH)
	else:
		pl.stream = _streams[name]
	pl.pitch_scale = pitch
	pl.play()


## Un reproductor libre o, si están todos ocupados, el que está por terminar:
## así una seguidilla de monedas no corta una fanfarria de varios segundos.
func _free_player() -> AudioStreamPlayer:
	var left := []
	for pl in _players:
		left.append(pl.stream.get_length() - pl.get_playback_position() if pl.playing else 0.0)
	return _players[SoundVariants.least_busy(left)]


func _pick_variant(name: String) -> AudioStream:
	var list: Array = _variants[name]
	var i := SoundVariants.pick(list.size(), int(_last_variant.get(name, -1)))
	_last_variant[name] = i
	return list[i]


func vibrate(ms := 30) -> void:
	if Settings.get_value("vibration") and OS.has_feature("mobile"):
		Input.vibrate_handheld(ms)
