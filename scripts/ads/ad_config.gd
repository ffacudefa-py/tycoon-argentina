class_name AdConfig
extends RefCounted
## Configuración de anuncios (data/ads.json) y elección del entorno.
##   development: sin anuncios.
##   test:        IDs oficiales de prueba de Google (builds de debug).
##   production:  IDs reales de la cuenta de AdMob (builds de release).
## Si en producción faltan los IDs, o son los de prueba, los anuncios quedan
## desactivados con un motivo claro: nunca se publica un ID de prueba como real.

var data := {}
var environment := "test"
var enabled := false
var app_id := ""
var rewarded_unit := ""
var disabled_reason := ""


static func load_default(force_env := "") -> AdConfig:
	var f := FileAccess.open("res://data/ads.json", FileAccess.READ)
	var d = JSON.parse_string(f.get_as_text()) if f else {}
	return from_data(d if d is Dictionary else {}, force_env)


static func from_data(d: Dictionary, force_env := "") -> AdConfig:
	var c := AdConfig.new()
	c.data = d
	var env := force_env if force_env != "" else str(c.data.get("environment", "auto"))
	if env == "auto":
		env = str(ProjectSettings.get_setting("tycoon/ads/environment", "auto"))
	if env == "auto":
		env = "test" if OS.is_debug_build() else "production"
	c.environment = env
	var e: Dictionary = c.data.get("environments", {}).get(env, {})
	c.app_id = str(e.get("app_id", ""))
	c.rewarded_unit = str(e.get("rewarded_unit", ""))
	c.enabled = bool(e.get("enabled", false))
	var test_ids: Array = c.data.get("official_test_ids", [])
	if not c.enabled:
		c.disabled_reason = "Los anuncios están desactivados en esta versión (%s)." % env
	elif c.app_id == "" or c.rewarded_unit == "":
		c.enabled = false
		c.disabled_reason = "Los anuncios todavía no están configurados para esta versión."
	elif env == "production" and (test_ids.has(c.app_id) or test_ids.has(c.rewarded_unit)):
		c.enabled = false
		c.disabled_reason = "Configuración inválida: producción no puede usar IDs de prueba."
	return c


func offers() -> Array:
	return data.get("offers", [])


func daily_limit() -> int:
	return int(data.get("daily_limit", 12))


func retry_seconds() -> Array:
	return data.get("retry_seconds", [5, 15, 30, 60, 120, 300])
