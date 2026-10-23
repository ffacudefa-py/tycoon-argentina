extends TestCase
## Cuentas: validaciones locales y mensajes de error de Firebase.


func test_validaciones() -> void:
	eq(AuthErrors.validate_email(""), "Escribí tu email.")
	check(AuthErrors.validate_email("sin-arroba") != "", "email inválido")
	check(AuthErrors.validate_email("a@b") != "", "falta dominio")
	eq(AuthErrors.validate_email("  juan@mail.com "), "", "con espacios alrededor es válido")
	check(AuthErrors.validate_password("123") != "", "contraseña corta")
	eq(AuthErrors.validate_password("123456"), "")


func test_mensajes_de_firebase() -> void:
	check(AuthErrors.message("EMAIL_EXISTS").contains("Ya hay una cuenta"), "email existente")
	eq(AuthErrors.message("INVALID_LOGIN_CREDENTIALS"), "Email o contraseña incorrectos.")
	eq(AuthErrors.message("INVALID_PASSWORD"), AuthErrors.message("EMAIL_NOT_FOUND"), "no revela si el email existe")
	check(AuthErrors.message("WEAK_PASSWORD : Password should be at least 6 characters").contains("débil"), "débil con detalle")
	check(AuthErrors.message("NETWORK").contains("Sin conexión"), "sin internet")
	check(AuthErrors.message("ALGO_RARO").contains("ALGO_RARO"), "código desconocido visible")


func test_codigo_desde_respuesta() -> void:
	eq(AuthErrors.code_from_body('{"error":{"code":400,"message":"EMAIL_EXISTS","errors":[]}}'), "EMAIL_EXISTS")
	eq(AuthErrors.code_from_body("no es json"), "UNKNOWN")
