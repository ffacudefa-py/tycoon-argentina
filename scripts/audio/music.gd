extends Node
## Autoload "Music" (15.0): el tema principal, de fondo en todo el juego.
## Arranca con un fundido al abrir la app y se repite sin corte: el archivo es PCM con
## loop exacto a la muestra (tools/audio/make_music.py). Si la app va a segundo plano o
## se abre un anuncio, se pausa, y al volver retoma donde estaba con un fundido corto.

const THEME := "res://assets/audio/music/main_theme.wav"
const BUS := "Music"
const FADE_IN := 4.0
const FADE_RESUME := 0.8
## Punto del salto: Godot deja en cero la muestra donde salta, así que va donde la onda
## ya pasa por cero y el archivo repite al final lo anterior (ver make_music.py).
const LOOP_HEAD := 29571

var _player: AudioStreamPlayer
var _tween: Tween


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	var stream: AudioStreamWAV = load(THEME)
	if stream == null:
		return
	stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
	stream.loop_begin = LOOP_HEAD
	stream.loop_end = roundi(stream.get_length() * stream.mix_rate)
	_player = AudioStreamPlayer.new()
	_player.stream = stream
	_player.bus = BUS
	_player.volume_db = linear_to_db(0.0001)
	add_child(_player)
	_player.play()
	_fade(FADE_IN)


## Sube del silencio al volumen pleno. Cuadrática: en dB se siente pareja.
func _fade(seconds: float) -> void:
	if _tween:
		_tween.kill()
	_tween = create_tween()
	_tween.tween_method(_set_level, 0.0, 1.0, seconds)


func _set_level(v: float) -> void:
	_player.volume_db = linear_to_db(maxf(v * v, 0.0001))


func _notification(what: int) -> void:
	if _player == null:
		return
	match what:
		NOTIFICATION_APPLICATION_PAUSED, NOTIFICATION_APPLICATION_FOCUS_OUT:
			if not _player.stream_paused:
				if _tween:
					_tween.kill()
				_player.stream_paused = true
		NOTIFICATION_APPLICATION_RESUMED, NOTIFICATION_APPLICATION_FOCUS_IN:
			if _player.stream_paused:
				_set_level(0.0)
				_player.stream_paused = false
				_fade(FADE_RESUME)
