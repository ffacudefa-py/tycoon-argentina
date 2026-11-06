extends TestCase
## 15.0: la moneda tiene 5 versiones (golpes de coin.mp3) y suena una por vez.


func test_moneda_una_version_por_vez() -> void:
	var paths := SoundVariants.paths("coin", 5)
	eq(paths.size(), 5, "las 5 versiones de la moneda")
	for p in paths:
		check(load(p) is AudioStream, "%s se carga" % p)
	var last := -1
	var seen := {}
	for i in 60:
		var k := SoundVariants.pick(5, last)
		check(k != last and k >= 0 and k < 5, "una distinta a la anterior")
		seen[k] = true
		last = k
	eq(seen.size(), 5, "van saliendo todas")
	eq(SoundVariants.pick(1, 0), 0, "con una sola versión, esa")


func test_una_fanfarria_no_se_corta_por_las_monedas() -> void:
	eq(SoundVariants.least_busy([6.5, 0.0, 0.2]), 1, "usa el reproductor libre")
	eq(SoundVariants.least_busy([6.5, 0.4, 0.2]), 2, "si no hay libre, el que está por terminar")
	eq(SoundVariants.least_busy([0.0, 0.0]), 0, "con todos libres, el primero")
