class_name SettingsData
extends RefCounted
## Preferencias del usuario en user://settings.cfg (independientes de la
## partida: sobreviven a reinicios y al prestigio).

const DEFAULTS := {
	"master_volume": 1.0,       ## volumen general
	"mute": false,              ## silenciar todo
	"sfx_enabled": true,
	"sfx_volume": 0.8,
	"vibration": true,
	"fx_quality": 2,            ## 0 bajo, 1 medio, 2 alto
	"power_saver": false,       ## 30 FPS y menos animaciones ambientales
	"confirm_irreversible": true,
	"inflation": false,         ## inflación ficticia (experimental)
	"scene_view": "interior",   ## vista del negocio: "interior" o "fachada"
	"scene_anim": true,         ## animaciones del escenario (clientes, humo, neón...)
	"news_seen": "",            ## última versión cuyas novedades se mostraron
	"reduce_motion": false,     ## accesibilidad: sin sacudidas ni rebotes de la interfaz
}

var path: String
var values := DEFAULTS.duplicate()


func _init(p_path := "user://settings.cfg") -> void:
	path = p_path


func load() -> void:
	values = DEFAULTS.duplicate()
	var cfg := ConfigFile.new()
	if cfg.load(path) != OK:
		return
	for k in DEFAULTS:
		var v = cfg.get_value("settings", k, DEFAULTS[k])
		if typeof(v) == typeof(DEFAULTS[k]) or (DEFAULTS[k] is float and v is int):
			values[k] = v
	values["sfx_volume"] = clampf(float(values["sfx_volume"]), 0.0, 1.0)
	values["master_volume"] = clampf(float(values["master_volume"]), 0.0, 1.0)
	if values["scene_view"] not in ["interior", "fachada"]:
		values["scene_view"] = "interior"
	values["fx_quality"] = clampi(int(values["fx_quality"]), 0, 2)


func save() -> void:
	var cfg := ConfigFile.new()
	for k in values:
		cfg.set_value("settings", k, values[k])
	cfg.save(path)
