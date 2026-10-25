extends SceneTree
## Ejecuta todas las pruebas:
##   godot --headless --path . -s res://tests/run_tests.gd
## Opcional: -- --only=economy   (filtra por nombre de archivo)
## Sale con código 1 si alguna prueba falla.

const DIRS := ["res://tests/economy", "res://tests/progression", "res://tests/persistence", "res://tests/ads", "res://tests/profile", "res://tests/cloud", "res://tests/ui"]


func _init() -> void:
	var only := ""
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--only="):
			only = a.substr(7)
	var total := 0
	var failed := 0
	var all_failures: PackedStringArray = []
	var started := Time.get_ticks_msec()
	for dir in DIRS:
		var da := DirAccess.open(dir)
		if da == null:
			continue
		var files := Array(da.get_files())
		files.sort()
		for f in files:
			if not (f.begins_with("test_") and f.ends_with(".gd")):
				continue
			if only != "" and not f.contains(only):
				continue
			var script: GDScript = load(dir + "/" + f)
			var inst = script.new()
			for method in inst.get_method_list():
				var mname: String = method["name"]
				if not mname.begins_with("test_"):
					continue
				total += 1
				inst.current = "%s::%s" % [f.get_basename(), mname]
				var before: int = inst.failures.size()
				var t0 := Time.get_ticks_msec()
				inst.call(mname)
				var ms := Time.get_ticks_msec() - t0
				if inst.failures.size() > before:
					failed += 1
					print("  FALLA  %s (%d ms)" % [inst.current, ms])
					for i in range(before, inst.failures.size()):
						all_failures.append(inst.failures[i])
				else:
					print("  ok     %s (%d ms)" % [inst.current, ms])
	print("")
	for fmsg in all_failures:
		print("  ✗ " + fmsg)
	print("\n%d pruebas, %d fallidas (%.1f s)" % [total, failed, (Time.get_ticks_msec() - started) / 1000.0])
	quit(1 if failed > 0 else 0)
