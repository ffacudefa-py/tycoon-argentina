extends TestCase
## 15.2: insignias en el perfil (Badges) y su publicación para los amigos.


func test_pionero_especial() -> void:
	var m := make_model()
	check(not Badges.owns(m, "pionero"), "una partida nueva no es pionera")
	check(Badges.special_owned(m).is_empty(), "sin especiales")
	check(Badges.grant(m, "pionero"), "se gana la insignia Pionero")
	check(Badges.owns(m, "pionero"), "la tiene")
	check(not Badges.grant(m, "pionero"), "no se gana dos veces")
	check(not Badges.grant(m, "inventada"), "no existen especiales inventadas")
	eq(Badges.shown(m), ["pionero"], "la especial se muestra sola")
	check(ResourceLoader.exists("res://assets/iconos/badges/pionero.png"), "tiene su imagen")
	# Sobrevive a guardar y cargar.
	var m2 := make_model()
	m2.from_dict(JSON.parse_string(JSON.stringify(m.to_dict())))
	check(Badges.owns(m2, "pionero") and Badges.is_shown(m2, "pionero"), "se guarda y se carga")


func test_mostrar_logros_hasta_tres() -> void:
	var m := make_model()
	var ids: Array = []
	for a in m.data.achievements.slice(0, 4):
		m.achievements[a["id"]] = 1.0
		ids.append(a["id"])
	var locked: String = m.data.achievements[10]["id"]
	check(not Badges.toggle_shown(m, locked)["ok"], "una insignia que no tenés no se muestra")
	for i in 3:
		check(Badges.toggle_shown(m, ids[i])["ok"], "se muestra la %d" % (i + 1))
	check(not Badges.toggle_shown(m, ids[3])["ok"], "la cuarta no entra")
	eq(Badges.shown(m).size(), Badges.MAX_SHOWN, "hasta %d" % Badges.MAX_SHOWN)
	check(Badges.toggle_shown(m, ids[1])["ok"] and not Badges.is_shown(m, ids[1]), "se saca")
	check(Badges.toggle_shown(m, ids[3])["ok"], "y entra otra")
	eq(Badges.shown(m), [ids[0], ids[2], ids[3]], "en orden")
	# Una partida editada a mano no cuela insignias ajenas ni repetidas.
	m.profile["shown_badges"] = [ids[0], ids[0], "pionero", locked, 5]
	eq(Badges.shown(m), [ids[0]], "sólo las propias, sin repetir")
	m.profile["shown_badges"] = "basura"
	eq(Badges.shown(m), [], "un valor roto no rompe nada")


func test_insignias_de_amigos() -> void:
	var m := make_model()
	var a0: String = m.data.achievements[0]["id"]
	m.achievements[a0] = 1.0
	Badges.toggle_shown(m, a0)
	Badges.grant(m, "pionero")
	var p := FriendLogic.profile_of(m, "uid-a", "K7M2QX")
	eq(p["badges"], ["pionero", a0], "el perfil público lleva las que muestra")
	var doc: Dictionary = JSON.parse_string(JSON.stringify({"name": "projects/x/databases/(default)/documents/players/uid-a", "fields": FriendLogic.profile_fields(p, 1.0)["fields"]}))
	eq(FriendLogic.profile_from_doc(doc)["badges"], ["pionero", a0], "van y vuelven por Firestore")
	p["badges"] = []
	check(not (FriendLogic.profile_fields(p, 1.0)["fields"] as Dictionary).has("badges"), "sin insignias no hay campo")
	# Lo que viene de otro teléfono se filtra: sólo ids que existen, hasta 3.
	eq(Badges.filter_known(m, ["pionero", "../hack", a0, a0, "billonario", "primera_venta"]).size(), 3, "hasta 3 conocidas")
	check(not Badges.filter_known(m, ["../hack"]).has("../hack"), "ids desconocidos fuera")


func test_denuncia_formato() -> void:
	var f: Dictionary = FriendLogic.report_fields("yo", "otro", "foto", "x".repeat(80), 5.0)["fields"]
	eq(f["reason"]["stringValue"], "foto", "motivo válido")
	eq(str(f["company"]["stringValue"]).length(), 40, "nombre recortado a 40")
	eq(FriendLogic.report_fields("yo", "otro", "<script>", "A", 5.0)["fields"]["reason"]["stringValue"], "otro", "motivo desconocido -> otro")
	eq(FriendLogic.block_fields("y".repeat(50), 1.0)["fields"]["company"]["stringValue"].length(), 40, "bloqueo recortado a 40")


func test_play_no_avisa_apk_de_github() -> void:
	eq(NotifPlan.releases_url("https://x", false), "https://x", "APK de GitHub: avisa versiones nuevas")
	eq(NotifPlan.releases_url("https://x", true), "", "versión de Play: no manda a GitHub")


func test_tope_de_solicitudes() -> void:
	var day := 20500
	var t := day * 86400.0 + 100.0
	eq(FriendLogic.next_limit({}, t), {"day": day, "count": 1}, "primera del día")
	eq(FriendLogic.next_limit({"day": day, "count": 7}, t), {"day": day, "count": 8}, "suma de a 1")
	eq(FriendLogic.next_limit({"day": day - 1, "count": 20}, t), {"day": day, "count": 1}, "otro día arranca de 1")
	check(FriendLogic.next_limit({"day": day, "count": FriendLogic.REQUESTS_PER_DAY}, t)["count"] > FriendLogic.REQUESTS_PER_DAY, "pasado el tope se nota")


func test_fotos_solo_png_y_jpeg() -> void:
	var img := Image.create(20, 20, false, Image.FORMAT_RGB8)
	img.fill(Color(0.8, 0.3, 0.2))
	check(ProfileImages.decode(img.save_png_to_buffer()) != null, "PNG sí")
	check(ProfileImages.decode(img.save_jpg_to_buffer()) != null, "JPEG sí")
	check(ProfileImages.decode(img.save_webp_to_buffer()) == null, "WEBP no")
	var gif := "GIF89a".to_ascii_buffer()
	gif.resize(64)
	check(ProfileImages.decode(gif) == null, "GIF no")
	check(ProfileImages.decode("<script>alert(1)</script> renombrado.jpg".to_utf8_buffer()) == null, "texto renombrado a .jpg no")
	check(ProfileImages.texture_from_b64(Marshalls.raw_to_base64(img.save_png_to_buffer())) != null, "miniatura PNG de otro jugador se ve")
	check(ProfileImages.texture_from_b64(Marshalls.raw_to_base64(img.save_jpg_to_buffer())) != null, "miniatura JPEG se ve")
	check(ProfileImages.texture_from_b64(Marshalls.raw_to_base64(img.save_webp_to_buffer())) == null, "miniatura WEBP no")


func test_registro_de_pioneros() -> void:
	var t := 20500 * 86400.0 + 50.0
	var d := PioneerRegistry.next_doc({}, "a@gmail.com", "Mates", "15.2", t)
	eq([d["first_day"], d["last_day"], d["days"]], [20500, 20500, 1], "primer día")
	check(PioneerRegistry.next_doc(d, "a@gmail.com", "Mates", "15.2", t + 3600).is_empty(), "mismo día: nada que escribir")
	var d2 := PioneerRegistry.next_doc(d, "a@gmail.com", "Mates", "15.2", t + 86400 * 3)
	eq([d2["first_day"], d2["last_day"], d2["days"]], [20500, 20503, 2], "otro día suma uno (días jugados, no seguidos)")
	var d3 := PioneerRegistry.next_doc(d2, "a@gmail.com", "Mates SA", "15.2", t + 86400 * 3)
	eq([d3["days"], d3["company"]], [2, "Mates SA"], "cambiar el nombre no suma días")
	var back := PioneerRegistry.from_fields(JSON.parse_string(JSON.stringify(PioneerRegistry.to_fields(d2))))
	eq(back, d2, "va y vuelve por Firestore")
