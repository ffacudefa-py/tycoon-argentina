/**
 * Coronados de Gloria — mail automático a los pioneros.
 *
 * Corre en Google Apps Script con la cuenta sarceapps@gmail.com (el mail sale de ahí).
 * Cada 5 minutos busca en Firestore las inscripciones (signups/<email>) que todavía no
 * recibieron el mail, les manda los pasos para entrar a la prueba cerrada y las marca
 * con `mailed` (fecha) e `invited: true`.
 *
 * La prueba cerrada usa un Grupo de Google abierto: el tester se une al grupo con su
 * cuenta y queda habilitado en Play solo, sin cargar emails a mano en Play Console.
 *
 * Instalación (una vez): ver docs/PIONEROS.md → "Mail automático".
 */

const CFG = {
  project: "coronadosdegloria",
  group: "coronados-pioneros",                       // <grupo>@googlegroups.com
  pkg: "ar.tycoonargentina.juego",
  fromName: "Coronados de Gloria",
  replyTo: "sarceapps@gmail.com",
  // No mandar a cuentas de prueba internas.
  skip: /(@coronadosdegloria\.web\.app$|^prueba|^test)/,
};

const GROUP_URL = "https://groups.google.com/g/" + CFG.group;
const OPTIN_URL = "https://play.google.com/apps/testing/" + CFG.pkg;
const STORE_URL = "https://play.google.com/store/apps/details?id=" + CFG.pkg;
const FS = "https://firestore.googleapis.com/v1/projects/" + CFG.project + "/databases/(default)/documents";

/** Ejecutar UNA vez a mano: crea el disparador cada 5 minutos y procesa lo pendiente. */
function setup() {
  ScriptApp.getProjectTriggers().forEach((t) => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger("check").timeBased().everyMinutes(5).create();
  check();
}

/** Prueba: se manda el mail a vos mismo (sarceapps) sin tocar Firestore. */
function testMail() {
  send(Session.getActiveUser().getEmail(), "Prueba");
}

/** Lo llama el disparador: inscriptos sin mail y sin marcar como invitados a mano. */
function check() { run(false); }

/** A mano, una vez: manda el mail también a los que ya estaban marcados como invitados. */
function mailAlsoInvited() { run(true); }

function run(includeInvited) {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) return;               // otra corrida sigue en curso
  try {
    let sent = 0;
    for (const d of listSignups()) {
      const f = d.fields || {};
      if (f.mailed || (!includeInvited && f.invited && f.invited.booleanValue)) continue;
      const email = (f.email && f.email.stringValue || "").toLowerCase();
      if (!email || CFG.skip.test(email)) continue;
      if (MailApp.getRemainingDailyQuota() < 1) { console.warn("Sin cuota de mails por hoy"); break; }
      const name = (f.name && f.name.stringValue || "").trim();
      send(email, name);
      markMailed(d.name);
      sent++;
    }
    if (sent) console.log("Mails enviados: " + sent);
  } finally {
    lock.releaseLock();
  }
}

function listSignups() {
  const out = [];
  let token = "";
  do {
    const url = FS + "/signups?pageSize=300" + (token ? "&pageToken=" + encodeURIComponent(token) : "");
    const r = api(url, "get");
    (r.documents || []).forEach((d) => out.push(d));
    token = r.nextPageToken || "";
  } while (token);
  return out;
}

function markMailed(docName) {
  const url = "https://firestore.googleapis.com/v1/" + docName +
    "?updateMask.fieldPaths=mailed&updateMask.fieldPaths=invited&currentDocument.exists=true";
  api(url, "patch", { fields: { mailed: { timestampValue: new Date().toISOString() }, invited: { booleanValue: true } } });
}

function api(url, method, body) {
  const opt = {
    method: method,
    headers: { Authorization: "Bearer " + ScriptApp.getOAuthToken() },
    muteHttpExceptions: true,
  };
  if (body) { opt.contentType = "application/json"; opt.payload = JSON.stringify(body); }
  const r = UrlFetchApp.fetch(url, opt);
  if (r.getResponseCode() >= 300) throw new Error(method + " " + url + " → " + r.getResponseCode() + " " + r.getContentText().slice(0, 300));
  return JSON.parse(r.getContentText() || "{}");
}

function esc(s) {
  return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

function send(email, name) {
  const hola = name ? "¡Hola, " + name + "!" : "¡Hola!";
  const subject = "Ya sos Pionero de Coronados de Gloria: así entrás a la prueba";
  const text = [
    hola,
    "",
    "Gracias por anotarte. Ya podés entrar a la prueba cerrada de Coronados de Gloria en Google Play.",
    "Hacé estos 3 pasos con la MISMA cuenta de Google que usás en el Play Store del celular (" + email + "):",
    "",
    "1) Unite al grupo de pioneros (botón \"Unirse al grupo\"): " + GROUP_URL,
    "2) Aceptá la invitación a la prueba (\"Convertirte en tester\"): " + OPTIN_URL,
    "3) Instalá el juego desde Google Play: " + STORE_URL,
    "",
    "Si Play dice que la app no está disponible, esperá unos minutos después del paso 1 y volvé a probar.",
    "Para que la prueba cuente, abrí el juego al menos una vez por día durante 14 días. Al abrirlo ganás la insignia Pionero.",
    "",
    "¿Dudas o te querés bajar? Respondé este mail.",
    "— El equipo de Coronados de Gloria",
  ].join("\n");

  const btn = (n, label, url, sub) =>
    '<tr><td style="padding:10px 0">' +
    '<div style="font:bold 15px sans-serif;color:#3a2a1a">' + n + ". " + label + "</div>" +
    '<div style="font:13px sans-serif;color:#6b5a48;margin:4px 0 8px">' + sub + "</div>" +
    '<a href="' + url + '" style="display:inline-block;background:#c8962e;color:#fff;text-decoration:none;' +
    'font:bold 15px sans-serif;padding:10px 18px;border-radius:6px">' + label + "</a></td></tr>";

  const html =
    '<div style="background:#f3e7cf;padding:24px"><table role="presentation" style="max-width:520px;margin:auto;' +
    'background:#fffaf0;border:3px solid #3a2a1a;border-radius:8px;padding:20px" cellpadding="0" cellspacing="0">' +
    '<tr><td style="font:bold 22px sans-serif;color:#3a2a1a">' + esc(hola) + "</td></tr>" +
    '<tr><td style="font:15px sans-serif;color:#3a2a1a;padding:8px 0">Gracias por anotarte. Ya podés entrar a la ' +
    "<b>prueba cerrada</b> de Coronados de Gloria. Hacé estos pasos con la <b>misma cuenta de Google</b> " +
    "del Play Store de tu celular (<b>" + esc(email) + "</b>):</td></tr>" +
    btn(1, "Unirme al grupo", GROUP_URL, "Tocá \"Unirse al grupo\". Es lo que te habilita como tester.") +
    btn(2, "Ser tester", OPTIN_URL, "Aceptá la invitación (\"Convertirte en tester\").") +
    btn(3, "Instalar el juego", STORE_URL, "Si dice que no está disponible, esperá unos minutos y volvé a probar.") +
    '<tr><td style="font:14px sans-serif;color:#3a2a1a;padding-top:12px">Para que la prueba cuente, abrí el juego ' +
    "<b>al menos una vez por día durante 14 días</b>. Al abrirlo ganás la insignia <b>Pionero</b>.</td></tr>" +
    '<tr><td style="font:13px sans-serif;color:#6b5a48;padding-top:12px">¿Dudas o te querés bajar? Respondé este mail.<br>' +
    "— El equipo de Coronados de Gloria</td></tr></table></div>";

  MailApp.sendEmail({ to: email, subject: subject, body: text, htmlBody: html, name: CFG.fromName, replyTo: CFG.replyTo });
}
