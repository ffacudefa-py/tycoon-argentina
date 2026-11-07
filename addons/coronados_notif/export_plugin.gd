@tool
extends EditorExportPlugin


func _get_name() -> String:
	return "CoronadosNotif"


func _supports_platform(platform: EditorExportPlatform) -> bool:
	return platform is EditorExportPlatformAndroid


func _get_android_libraries(_platform: EditorExportPlatform, _debug: bool) -> PackedStringArray:
	return PackedStringArray(["res://addons/coronados_notif/bin/coronados-notif.aar"])
