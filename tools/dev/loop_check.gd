extends SceneTree
## 15.0: graba lo que sale del motor mientras el tema da la vuelta, para comprobar la
## unión del loop con el audio real.
##   godot --headless --path . -s res://tools/dev/loop_check.gd -- --out=<archivo.raw>
## Escribe flotantes de 32 bits estéreo; arranca 1,5 s antes del final.

const LEAD := 1.5
const TAIL := 1.5


func _init() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "user://loop.raw"
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out = a.substr(6)
	var bus := AudioServer.bus_count
	AudioServer.add_bus()
	AudioServer.set_bus_name(bus, "Check")
	var cap := AudioEffectCapture.new()
	cap.buffer_length = 8.0
	AudioServer.add_bus_effect(bus, cap)
	var stream: AudioStreamWAV = load("res://assets/audio/music/main_theme.wav")
	stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
	stream.loop_begin = 29571
	stream.loop_end = roundi(stream.get_length() * stream.mix_rate)
	print("largo ", stream.get_length(), " rate ", stream.mix_rate, " loop_end ", stream.loop_end, " formato ", stream.format)
	var p := AudioStreamPlayer.new()
	p.stream = stream
	p.bus = "Check"
	root.add_child(p)
	p.play(stream.get_length() - LEAD)
	var frames := PackedVector2Array()
	var want := int((LEAD + TAIL) * AudioServer.get_mix_rate())
	var t0 := Time.get_ticks_msec()
	while frames.size() < want and Time.get_ticks_msec() - t0 < 8000:
		await process_frame
		var n := cap.get_frames_available()
		if n > 0:
			frames.append_array(cap.get_buffer(n))
	print("capturado ", frames.size(), " a ", AudioServer.get_mix_rate(), " Hz, sonando: ", p.playing)
	var f := FileAccess.open(out, FileAccess.WRITE)
	for v in frames:
		f.store_float(v.x)
		f.store_float(v.y)
	f.close()
	quit()
