extends Node
## Autoload "Game": dueño del GameModel durante la ejecución.
##
## - Corre la simulación a paso fijo (0,1 s) acumulando el delta real:
##   la economía no depende de los FPS.
## - Guarda automáticamente cada 30 s, al pausar/cerrar la app y tras
##   acciones importantes (save_soon()).
## - Al volver de segundo plano calcula el progreso offline.

signal offline_report(result: Dictionary)
signal model_reset
signal saved                       ## se escribió el guardado local (la nube lo copia)
signal model_loaded                ## se cargó otra partida (la de la nube)

var data: GameData
var m: GameModel
var saver := SaveSystem.new()
var pending_offline := {}
var load_warning := ""

var _acc := 0.0
var _autosave_timer := 0.0
var _save_soon := -1.0
var _last_wall := 0.0
var _tick := 0.1


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	data = GameData.load_default()
	if not data.errors.is_empty():
		push_error("Errores en los datos del juego: %s" % ", ".join(data.errors))
	_tick = float(data.balance["tick_seconds"])
	# Herramienta de capturas (tools/screenshots.sh): guardado separado.
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--dev-save="):
			saver = SaveSystem.new(a.substr(11))
	m = GameModel.new(data)
	var had_files := saver.exists()
	var payload := saver.load_payload(data)
	if not payload.is_empty():
		m.from_dict(payload)
		if saver.last_load_source != "main":
			load_warning = "Recuperamos tu partida desde el respaldo."
		var r := OfflineCalculator.apply(m)
		if float(r["credited"]) >= float(data.balance["offline_summary_min_seconds"]) or r["clock_issue"]:
			pending_offline = r
	elif had_files:
		load_warning = "No pudimos leer tu partida guardada. Empezás de nuevo (el archivo dañado quedó apartado)."
	m.inflation_enabled = bool(Settings.get_value("inflation"))
	m.invalidate()
	for id in m.owned_ids():
		EmployeeSystem.ensure_candidates(m, id)
	ProgressionSystem.ensure_daily(m)
	m.update_progress()
	_last_wall = m.now()
	for sig in ["businesses_changed", "stage_changed", "world_changed", "profile_changed"]:
		m.connect(sig, func(_a = null) -> void: save_soon())
	m.celebrate.connect(func(kind: String, _i: Dictionary) -> void:
		if kind in ["unlock", "hire", "upgrade", "zone", "prestige", "claim", "daily"]:
			save_soon())


func _process(delta: float) -> void:
	var wall := m.now()
	if wall - _last_wall > 5.0:
		_handle_gap()
	_last_wall = m.now()
	_acc += minf(delta, 0.5)
	while _acc >= _tick:
		m.simulate(_tick)
		_acc -= _tick
	_autosave_timer += delta
	if _autosave_timer >= float(data.balance["autosave_seconds"]):
		save()
	if _save_soon >= 0.0:
		_save_soon -= delta
		if _save_soon < 0.0:
			save()


func _notification(what: int) -> void:
	match what:
		NOTIFICATION_APPLICATION_PAUSED, NOTIFICATION_WM_CLOSE_REQUEST, NOTIFICATION_APPLICATION_FOCUS_OUT, NOTIFICATION_WM_GO_BACK_REQUEST:
			if m:
				save()
		NOTIFICATION_APPLICATION_RESUMED:
			if m:
				_handle_gap()


## Tiempo sin procesar (app en segundo plano o suspendida): offline.
func _handle_gap() -> void:
	var r := OfflineCalculator.apply(m)
	_last_wall = m.now()
	_acc = 0.0
	if float(r["credited"]) >= float(data.balance["offline_summary_min_seconds"]) or r["clock_issue"]:
		pending_offline = r
		offline_report.emit(r)


func save() -> bool:
	_autosave_timer = 0.0
	_save_soon = -1.0
	var ok := saver.save(m)
	if ok:
		saved.emit()
	return ok


## Reemplaza la partida en curso por otra ya validada y migrada (la de la
## nube): misma preparación que al abrir el juego, con su progreso offline.
func replace_with(payload: Dictionary) -> void:
	m.from_dict(payload)
	m.inflation_enabled = bool(Settings.get_value("inflation"))
	var r := OfflineCalculator.apply(m)
	m.invalidate()
	for id in m.owned_ids():
		EmployeeSystem.ensure_candidates(m, id)
	ProgressionSystem.ensure_daily(m)
	m.update_progress()
	_last_wall = m.now()
	_acc = 0.0
	save()
	model_loaded.emit()
	if float(r["credited"]) >= float(data.balance["offline_summary_min_seconds"]):
		pending_offline = r
		offline_report.emit(r)


## Agrupa varios cambios seguidos en un solo guardado.
func save_soon() -> void:
	if _save_soon < 0.0:
		_save_soon = 0.5


func reset_everything() -> void:
	saver.delete_all()
	m.new_game()
	for id in m.owned_ids():
		EmployeeSystem.ensure_candidates(m, id)
	ProgressionSystem.ensure_daily(m)
	m.update_progress()
	save()
	model_reset.emit()
