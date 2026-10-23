# Foto de perfil y banner

## Flujo

Perfil → tocar la foto → **Elegir foto de la galería** (o Perfil → **Cambiar
banner**). Se abre el selector del sistema; al elegir una imagen aparece la
pantalla de recorte:

- arrastrar con un dedo mueve la imagen, pellizcar acerca/aleja;
- botones − / + y deslizador de zoom (accesibilidad); rueda del mouse en PC;
- la imagen siempre cubre el marco (nunca quedan bordes vacíos) y nunca se deforma;
- arriba se ve la vista previa con la forma final (círculo o 3:1);
- CONFIRMAR guarda, CANCELAR no toca nada.

También: "Usar avatar pixel art", "Quitar foto" y "Restaurar banner por defecto".

## Detalles técnicos

- `scripts/profile/image_picker.gd`: en Android usa el selector nativo
  (`DisplayServer.file_dialog_show`, Storage Access Framework). No pide permisos
  de almacenamiento: el sistema da acceso sólo al archivo elegido (URI
  `content://`). El resultado llega cuando Android devuelve el control al juego
  y se procesa con `call_deferred` (respeta el ciclo de vida: si la app pasó a
  segundo plano, el juego ya guardó y el recorte se abre al volver).
  En PC usa el diálogo de archivos de Godot.
- `profile_images.gd`: detecta PNG/JPEG/WEBP por la firma, corrige la rotación
  EXIF de las fotos de cámara, achica a 2048 px como máximo para trabajar y
  guarda PNG optimizados: foto **256×256**, banner **768×256**, en
  `user://profile/` (escritura a temporal + verificación + renombrado).
- `crop_math.gd`: matemática del recorte (pura, con pruebas).
- La partida guarda sólo `profile.photo` / `profile.banner` (sí/no). Si el
  archivo falta (otro teléfono) se muestra el avatar pixel y el banner de la calle.
- Nube: no hay. Queda preparado para subir esos mismos PNG asociados al `uid`
  de Firebase (ver `docs/CUENTAS.md`).

## Cómo probarlo en un teléfono o emulador

1. Tener alguna imagen en el teléfono (en el emulador:
   `adb push foto.jpg /sdcard/Pictures/` y abrir la app Fotos una vez para que
   la indexe, o sacar una foto con la cámara virtual).
2. Perfil → tocar la foto → Elegir foto de la galería → elegir la imagen.
3. Mover, pellizcar, CONFIRMAR. La foto aparece circular en Perfil, en la barra
   superior y en la pantalla de inicio (con sesión iniciada).
4. Cerrar la app desde multitarea y volver a abrir: la foto sigue.
5. Probar CANCELAR en el selector y en el recorte: no cambia nada.
