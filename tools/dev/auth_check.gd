extends SceneTree
## Verificación manual contra el Firebase real (necesita internet):
##   godot --headless --path . -s res://tools/dev/auth_check.gd
## Crea una cuenta descartable, inicia sesión, renueva el token, prueba
## errores típicos y BORRA la cuenta al final.

var auth: Node


func _initialize() -> void:
	_run.call_deferred()


func _wait(fn: Callable) -> Dictionary:
	var box := [null]
	fn.call(func(r: Dictionary) -> void: box[0] = r)
	while box[0] == null:
		await process_frame
	return box[0]


func _run() -> void:
	auth = root.get_node("Auth")
	var email := "prueba_%d@tycoon-test.invalid" % Time.get_ticks_usec()
	var pw := "clave-segura-123"
	var r: Dictionary = await _wait(func(cb: Callable) -> void: auth.sign_up(email, "123", cb))
	print("contraseña corta -> ", r)
	r = await _wait(func(cb: Callable) -> void: auth.sign_up(email, pw, cb))
	print("registro -> ", r, " uid=", auth.uid)
	r = await _wait(func(cb: Callable) -> void: auth.sign_up(email, pw, cb))
	print("registro repetido -> ", r)
	auth.sign_out()
	r = await _wait(func(cb: Callable) -> void: auth.sign_in(email, "otra-clave-mal", cb))
	print("clave incorrecta -> ", r)
	r = await _wait(func(cb: Callable) -> void: auth.sign_in(email, pw, cb))
	print("ingreso -> ", r, " signed_in=", auth.signed_in())
	r = await _wait(func(cb: Callable) -> void: auth.refresh_session(cb))
	print("renovar token -> ", r)
	r = await _wait(func(cb: Callable) -> void: auth.send_password_reset(email, cb))
	print("recuperar contraseña -> ", r)
	# Borrar la cuenta descartable
	var http := HTTPRequest.new()
	root.add_child(http)
	http.request("https://identitytoolkit.googleapis.com/v1/accounts:delete?key=" + auth.api_key, ["Content-Type: application/json"], HTTPClient.METHOD_POST, JSON.stringify({"idToken": auth._id_token}))
	var res = await http.request_completed
	print("borrar cuenta de prueba -> HTTP ", res[1])
	auth.sign_out()
	quit()
