class_name AuthErrors
extends RefCounted
## Validaciones locales y traducción de errores de Firebase Auth a mensajes
## claros (puro: se prueba en tests/).

const MIN_PASSWORD := 6


static func validate_email(email: String) -> String:
	var e := email.strip_edges()
	if e == "":
		return "Escribí tu email."
	var re := RegEx.create_from_string("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$")
	if re.search(e) == null:
		return "Ese email no parece válido."
	return ""


static func validate_password(password: String) -> String:
	if password == "":
		return "Escribí tu contraseña."
	if password.length() < MIN_PASSWORD:
		return "La contraseña tiene que tener al menos %d caracteres." % MIN_PASSWORD
	return ""


## `code` es error.message de la respuesta REST (p. ej. "EMAIL_EXISTS" o
## "WEAK_PASSWORD : Password should be at least 6 characters").
static func message(code: String) -> String:
	var c := code.split(" ")[0].strip_edges()
	match c:
		"EMAIL_EXISTS":
			return "Ya hay una cuenta con ese email. Probá iniciar sesión."
		"EMAIL_NOT_FOUND", "INVALID_PASSWORD", "INVALID_LOGIN_CREDENTIALS":
			return "Email o contraseña incorrectos."
		"USER_DISABLED":
			return "Esta cuenta está deshabilitada."
		"TOO_MANY_ATTEMPTS_TRY_LATER":
			return "Demasiados intentos. Esperá unos minutos y probá de nuevo."
		"WEAK_PASSWORD":
			return "La contraseña es muy débil: usá al menos %d caracteres." % MIN_PASSWORD
		"INVALID_EMAIL", "MISSING_EMAIL":
			return "Ese email no parece válido."
		"MISSING_PASSWORD":
			return "Escribí tu contraseña."
		"OPERATION_NOT_ALLOWED":
			return "El inicio de sesión con email está desactivado en el servidor."
		"TOKEN_EXPIRED", "INVALID_REFRESH_TOKEN", "USER_NOT_FOUND", "INVALID_ID_TOKEN":
			return "Tu sesión venció. Iniciá sesión de nuevo."
		"NETWORK":
			return "Sin conexión. Revisá internet y probá de nuevo."
		"TIMEOUT":
			return "El servidor tardó demasiado. Probá de nuevo."
	return "No se pudo completar (%s)." % c


## Extrae el código de error del cuerpo JSON de Firebase.
static func code_from_body(body: String) -> String:
	var d = JSON.parse_string(body)
	if d is Dictionary and d.get("error") is Dictionary:
		var e: Dictionary = d["error"]
		if e.get("message") is String:
			return e["message"]
		if e.get("status") is String:
			return e["status"]
	return "UNKNOWN"
