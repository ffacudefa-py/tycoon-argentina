// Idioma de los correos de Firebase Auth (verificación y contraseña) y de la
// página a la que lleva el enlace: castellano (es-419). Usa la sesión ya
// iniciada de la CLI de Firebase.
//   node tools/firebase/apply_email_templates.js
// Firebase NO deja cambiar el texto del correo de verificación (responde
// EMAIL_TEMPLATE_UPDATE_NOT_ALLOWED, medida antispam): se usa su plantilla
// traducida. Ver docs/CUENTAS.md.
const PROJECT = "coronadosdegloria";
const TOOLS = process.env.FIREBASE_TOOLS_LIB || "D:/Users/Family/Tools/npm-global/node_modules/firebase-tools/lib/";
const URL = `https://identitytoolkit.googleapis.com/admin/v2/projects/${PROJECT}/config`;

async function token() {
  const auth = require(TOOLS + "auth.js");
  const { configstore } = require(TOOLS + "configstore.js");
  return (await auth.getAccessToken(configstore.get("tokens").refresh_token, [])).access_token;
}

(async () => {
  const res = await fetch(`${URL}?updateMask=notification.defaultLocale`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${await token()}`, "Content-Type": "application/json", "X-Goog-User-Project": PROJECT },
    body: JSON.stringify({ notification: { defaultLocale: "es-419" } }),
  });
  const out = await res.json();
  if (!res.ok) throw new Error(`${res.status}: ${JSON.stringify(out.error || out)}`);
  console.log(`Idioma de los correos: ${out.notification.defaultLocale}`);
})().catch((e) => { console.error("Error:", e.message); process.exit(1); });
