extends Node
## Autoload "Settings": lee, guarda y APLICA las preferencias al instante.

signal changed(key: String, value: Variant)

var store := SettingsData.new()


func _ready() -> void:
	store.load()
	if AudioServer.get_bus_index("SFX") == -1:
		AudioServer.add_bus()
		AudioServer.set_bus_name(AudioServer.bus_count - 1, "SFX")
		AudioServer.set_bus_send(AudioServer.bus_count - 1, "Master")
	for k in store.values:
		_apply(k)


func get_value(key: String) -> Variant:
	return store.values.get(key, SettingsData.DEFAULTS.get(key))


func set_value(key: String, value: Variant) -> void:
	store.values[key] = value
	store.save()
	_apply(key)
	changed.emit(key, value)


func _apply(key: String) -> void:
	match key:
		"master_volume", "mute":
			var master := AudioServer.get_bus_index("Master")
			var mv := float(get_value("master_volume"))
			AudioServer.set_bus_mute(master, bool(get_value("mute")) or mv <= 0.001)
			AudioServer.set_bus_volume_db(master, linear_to_db(maxf(mv, 0.001)))
		"sfx_enabled", "sfx_volume":
			var bus := AudioServer.get_bus_index("SFX")
			var vol := float(get_value("sfx_volume"))
			AudioServer.set_bus_mute(bus, not get_value("sfx_enabled") or vol <= 0.001)
			AudioServer.set_bus_volume_db(bus, linear_to_db(maxf(vol, 0.001)))
		"power_saver":
			Engine.max_fps = 30 if get_value("power_saver") else 60


## 0 bajo, 1 medio, 2 alto (el ahorro de energía fuerza bajo).
func fx_level() -> int:
	return 0 if get_value("power_saver") else int(get_value("fx_quality"))
