class_name ConfirmDialog
extends RefCounted
## Cuadro de confirmación reutilizable.


static func open(title: String, text: String, confirm_text: String, on_yes: Callable, danger := true) -> ModalHost.ModalWindow:
	var body := U.vbox(8)
	body.add_child(U.para(text, U.SIZE_BODY, U.TEXT))
	var row := U.hbox(6)
	var no := U.button("Cancelar", "crema", "", 30)
	no.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var yes := U.button(confirm_text, "rojo" if danger else "verde", "", 30)
	yes.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(no)
	row.add_child(yes)
	body.add_child(row)
	var w := Main.instance.modal_host.open(title, body, true, 300)
	U.on_press(no, w.close)
	U.on_press(yes, func() -> void:
		w.close()
		on_yes.call(), "")
	return w
