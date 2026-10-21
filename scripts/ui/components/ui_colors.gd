class_name UiColors
extends RefCounted
## Colores con sentido (docs/REDISENO.md). Cada color significa UNA cosa:
##   verde    = ganancia / cobrar
##   rojo     = pérdida, falta de plata, peligro
##   amarillo = aviso / atención
##   celeste  = acción o información (comprar, contratar, abrir)
## Los estilos de botón usan los mismos nombres.

const GAIN := Color("2d6a3e")
const GAIN_LIGHT := Color("8ccb6c")
const LOSS := Color("b83a3f")
const LOSS_LIGHT := Color("e2665a")
const WARN := Color("b5700a")
const INFO := Color("2f6ea8")

const BTN_ACTION := "celeste"   ## comprar, contratar, abrir, desbloquear
const BTN_GAIN := "verde"       ## vender, reclamar premios
const BTN_WARN := "amarillo"    ## reponer cuando falta mercadería
const BTN_DANGER := "rojo"      ## despedir, reiniciar


## Botón de compra que explica por qué no se puede: si falta plata dice
## "Faltan $X" (en rojo); si hay un bloqueo, muestra el motivo.
## Devuelve el botón; llamar refresh(btn) periódicamente.
static func buy_button(label: String, cost: int, on_buy: Callable, height := 36) -> Button:
	var b := U.button("", BTN_ACTION, "", height, U.SIZE_BODY)
	b.set_meta("label", label)
	b.set_meta("cost", cost)
	b.set_meta("blocked", "")
	U.on_press(b, on_buy, "")
	refresh(b)
	return b


static func set_cost(b: Button, cost: int, blocked := "") -> void:
	b.set_meta("cost", cost)
	b.set_meta("blocked", blocked)
	refresh(b)


static func refresh(b: Button) -> void:
	var m := Game.m
	var cost: int = b.get_meta("cost")
	var blocked: String = b.get_meta("blocked")
	if blocked != "":
		b.text = blocked
		b.icon = U.icon_tex("candado")
		b.disabled = true
		b.add_theme_color_override("font_disabled_color", Color("f0eee6"))
	elif not m.economy.can_afford(cost):
		b.text = "Faltan " + Fmt.cost(cost - m.economy.money)
		b.icon = U.icon_tex("candado")
		b.disabled = true
		b.add_theme_color_override("font_disabled_color", LOSS_LIGHT)
	else:
		b.text = "%s · %s" % [b.get_meta("label"), Fmt.cost(cost)]
		b.icon = null
		b.disabled = false


## Fila de requisito con barra: "🔒 Kiosco nivel 10   [████░░] 3/10".
static func requirement_row(req: Dictionary, dark := false) -> Control:
	var v := U.vbox(2)
	var h := U.hbox(4)
	h.add_child(U.icon("check" if req["met"] else "candado"))
	var t := U.para(req["text"], U.SIZE_SMALL, (GAIN_LIGHT if dark else GAIN) if req["met"] else (LOSS_LIGHT if dark else LOSS))
	h.add_child(t)
	v.add_child(h)
	if not req["met"]:
		var row := U.hbox(6)
		var bar := U.progress("amarillo", 8)
		bar.value = clampf(float(req["current"]) / maxf(float(req["target"]), 1.0), 0.0, 1.0)
		bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(bar)
		var txt := ("%s/%s" % [Fmt.money(req["current"]), Fmt.money(req["target"])]) if req["money"] else ("%d/%d" % [int(req["current"]), int(req["target"])])
		row.add_child(U.label(txt, U.SIZE_SMALL, Color("f0eee6") if dark else U.TEXT, true))
		v.add_child(row)
	return v
