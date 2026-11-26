/**
 * Coronados de Gloria — mail automático a los pioneros.
 *
 * Corre en Google Apps Script con la cuenta sarceapps@gmail.com (el mail sale de ahí).
 * Al instante (doPost) y cada 1 minuto busca en Firestore las inscripciones (signups/<email>) nuevas que no
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
  fromName: "Sarce And Company",
  replyTo: "sarceapps@gmail.com",
  // No mandar a cuentas de prueba internas.
  skip: /(@coronadosdegloria\.web\.app$|^prueba|^test)/,
};

const GROUP_URL = "https://groups.google.com/g/" + CFG.group;
const OPTIN_URL = "https://play.google.com/apps/testing/" + CFG.pkg;
const STORE_URL = "https://play.google.com/store/apps/details?id=" + CFG.pkg;
const FS = "https://firestore.googleapis.com/v1/projects/" + CFG.project + "/databases/(default)/documents";

/** Ejecutar UNA vez a mano: crea el disparador de respaldo cada 1 minuto y procesa lo pendiente. */
function setup() {
  ScriptApp.getProjectTriggers().forEach((t) => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger("check").timeBased().everyMinutes(1).create();
  check();
}

/**
 * Aviso instantáneo: pioneros.html hace un POST a la URL de esta app web justo después de
 * inscribir a alguien. No recibe datos (a quién mandar sale siempre de Firestore), así que
 * llamarla de más sólo hace una revisión extra.
 * Implementar → Nueva implementación → App web, Ejecutar como: Yo, Acceso: Cualquier usuario.
 */
function doPost() {
  // Freno contra quien llame la URL en bucle: como mucho una revisión cada 10 s (el resto lo
  // agarra el disparador de 1 minuto). Así no se gasta la cuota gratis de Firestore del juego.
  const cache = CacheService.getScriptCache();
  if (!cache.get("ping")) {
    cache.put("ping", "1", 10);
    run(false, 25000);
  }
  return ContentService.createTextOutput("ok");
}

/** Prueba: se manda el mail a vos mismo (sarceapps) sin tocar Firestore. */
function testMail() {
  send(Session.getActiveUser().getEmail(), "Prueba");
}

/** Lo llama el disparador: inscriptos sin mail y sin marcar como invitados a mano. */
function check() { run(false); }

/** A mano, una vez: manda el mail también a los que ya estaban marcados como invitados. */
function mailAlsoInvited() { run(true); }

// Tope de mails automáticos por día: si alguien llena el formulario con emails ajenos, el
// script no puede usarse para mandar cientos de mails desde sarceapps (y quedan
// pendientes para el día siguiente, no se pierden).
const MAX_PER_DAY = 40;

function run(includeInvited, waitMs) {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(waitMs || 1000)) return;     // otra corrida sigue en curso (el aviso espera)
  try {
    const props = PropertiesService.getScriptProperties();
    const today = Utilities.formatDate(new Date(), "America/Argentina/Buenos_Aires", "yyyy-MM-dd");
    const sentKey = "sent_" + today;
    let sentToday = Number(props.getProperty(sentKey) || 0);
    // Sólo se leen las inscripciones posteriores a la última procesada (`cursor`), no todas:
    // el disparador corre 1440 veces por día y el plan gratis de Firestore da 50.000 lecturas
    // diarias para TODO el proyecto (juego incluido).
    const cursor = includeInvited ? null : props.getProperty("cursor");
    const docs = cursor ? newSignups(cursor) : listSignups().sort((a, b) =>
      String(a.fields.created && a.fields.created.timestampValue).localeCompare(String(b.fields.created && b.fields.created.timestampValue)));
    let last = cursor;
    let sent = 0;
    for (const d of docs) {
      const f = d.fields || {};
      const created = f.created && f.created.timestampValue;
      const email = (f.email && f.email.stringValue || "").toLowerCase();
      const pending = !f.mailed && (includeInvited || !(f.invited && f.invited.booleanValue)) &&
        email && !CFG.skip.test(email);
      if (pending) {
        if (sentToday >= MAX_PER_DAY || MailApp.getRemainingDailyQuota() < 1) {
          console.warn("Tope diario de mails alcanzado; el resto sale mañana");
          break;
        }
        send(email, (f.name && f.name.stringValue || "").trim());
        markMailed(d.name);
        sent++; sentToday++;
        props.setProperty(sentKey, String(sentToday));
      }
      if (!includeInvited && created) last = created;   // docs ya vienen en orden
    }
    if (!includeInvited && last && last !== cursor) props.setProperty("cursor", last);
    if (sent) console.log("Mails enviados: " + sent);
  } finally {
    lock.releaseLock();
  }
}

/** Inscripciones con `created` posterior al cursor, en orden (1 lectura si no hay ninguna). */
function newSignups(cursor) {
  const r = api(FS + ":runQuery", "post", { structuredQuery: {
    from: [{ collectionId: "signups" }],
    where: { fieldFilter: { field: { fieldPath: "created" }, op: "GREATER_THAN", value: { timestampValue: cursor } } },
    orderBy: [{ field: { fieldPath: "created" }, direction: "ASCENDING" }],
    limit: 100,
  } });
  return (r || []).filter((x) => x.document).map((x) => x.document);
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

const IMG = "https://coronadosdegloria.web.app/img/mail/";

// Paleta del juego (web/pioneros.html).
const C = { night: "#1a1730", night2: "#24203f", ink: "#3d1b0b", inkSoft: "#6b3f26", wood: "#5c3520",
  crema: "#f6efe2", crema2: "#f7e7c4", gold: "#f2d173", gold2: "#f6b40e", goldDark: "#8e5a10",
  green: "#256b42", greenDark: "#1d5a34", light: "#fff6e6", dim: "#c9c2dc" };

const SUBJECT = "Ya podés jugar Coronados de Gloria! 🏆 Sos Pionero";

function send(email, name) {
  MailApp.sendEmail({ to: email, subject: SUBJECT, body: mailText(email, name), htmlBody: mailHtml(email, name),
    name: CFG.fromName, replyTo: CFG.replyTo });
}

function mailHtml(email, name) {
  const F = "font-family:'Trebuchet MS',Verdana,sans-serif;";
  const hola = "¡Hola!";

  // Botón que funciona también en Outlook: celda de tabla con borde inferior grueso, como los del juego.
  const button = (label, url, bg, edge, fg) =>
    '<table role="presentation" cellpadding="0" cellspacing="0" style="margin-top:10px"><tr>' +
    '<td style="background:' + bg + ';border:3px solid ' + C.ink + ';border-bottom-width:6px;border-radius:4px;' +
    'box-shadow:inset 0 -4px 0 ' + edge + ';">' +
    '<a href="' + url + '" style="display:block;padding:11px 22px;' + F + 'font-size:17px;font-weight:bold;' +
    'color:' + fg + ';text-decoration:none;letter-spacing:.5px">' + label + "</a></td></tr></table>";

  const step = (n, title, sub, label, url, green) =>
    '<tr><td style="padding:14px 0;border-top:2px dashed ' + C.crema2 + '">' +
    '<table role="presentation" cellpadding="0" cellspacing="0" width="100%"><tr>' +
    '<td width="50" valign="top"><div style="width:36px;height:36px;line-height:36px;text-align:center;' +
    'background:' + C.gold2 + ';border:3px solid ' + C.ink + ';border-radius:50%;' + F +
    'font-size:18px;font-weight:bold;color:' + C.ink + '">' + n + "</div></td>" +
    '<td valign="top" style="' + F + 'color:' + C.ink + '">' +
    '<div style="font-size:18px;font-weight:bold">' + title + "</div>" +
    '<div style="font-size:14px;color:' + C.inkSoft + ';margin-top:2px">' + sub + "</div>" +
    (green ? button(label, url, C.green, C.greenDark, "#ffffff") : button(label, url, C.gold2, C.goldDark, C.ink)) +
    "</td></tr></table></td></tr>";

  return '<!doctype html><html><body style="margin:0;padding:0;background:' + C.night + '">' +
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:' + C.night + '"><tr><td align="center" style="padding:18px 8px">' +
    '<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:100%;max-width:600px">' +
    // Cabecera: pilares de las regiones con el logo
    '<tr><td style="border:4px solid ' + C.goldDark + ';border-bottom:0;border-radius:6px 6px 0 0;overflow:hidden;line-height:0">' +
    '<img src="' + IMG + 'cabecera.png" width="592" alt="Coronados de Gloria" style="display:block;width:100%;height:auto;border:0"></td></tr>' +
    // Franja dorada
    '<tr><td style="background:' + C.gold2 + ';border:4px solid ' + C.goldDark + ';border-top:3px solid ' + C.gold +
    ';text-align:center;padding:8px;' + F + 'font-size:15px;font-weight:bold;letter-spacing:3px;color:' + C.ink + '">' +
    "&#9670; PRUEBA CERRADA &middot; PIONEROS &#9670;</td></tr>" +
    // Panel crema
    '<tr><td style="background:' + C.crema + ';border:4px solid ' + C.wood + ';border-top:0;padding:22px 24px 8px">' +
    '<table role="presentation" cellpadding="0" cellspacing="0" width="100%"><tr>' +
    '<td valign="top" style="' + F + 'color:' + C.ink + '">' +
    '<div style="font-size:26px;font-weight:bold;line-height:1.2">' + hola + "</div>" +
    '<div style="font-size:16px;line-height:1.5;margin-top:8px">Te anotaste para la <b>prueba cerrada</b> de ' +
    "Coronados de Gloria y ya está lista. Para entrar, usá tu celular Android con la <b>misma cuenta de Google</b> " +
    "con la que te anotaste:</div>" +
    '<div style="display:inline-block;margin-top:8px;padding:4px 10px;background:' + C.crema2 + ';border:2px solid ' + C.wood +
    ';border-radius:3px;font-size:15px;font-weight:bold">' + esc(email) + "</div></td>" +
    '<td width="96" valign="top" align="right"><img src="' + IMG + 'pionero.png" width="88" height="88" alt="Insignia Pionero" style="display:block;border:0"></td>' +
    "</tr></table>" +
    '<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-top:16px">' +
    step(1, "Unite al grupo de pioneros", "Tocá <b>Unirse al grupo</b>. Es lo que te habilita como tester.", "UNIRME AL GRUPO", GROUP_URL) +
    step(2, "Hacete tester", "Abrí este link desde tu celular y tocá <b>Ser tester</b> (o <b>Unirse</b>).", "SER TESTER", OPTIN_URL) +
    step(3, "Instalá el juego desde Google Play", "Si dice que no está disponible, esperá unos minutos y volvé a probar.", "INSTALAR EN GOOGLE PLAY", STORE_URL, true) +
    "</table>" +
    '<div style="' + F + 'color:' + C.ink + ';font-size:15px;line-height:1.5;padding:14px 0 16px;border-top:2px dashed ' + C.crema2 + '">' +
    "Mientras juegues esta versión vas a ganar la insignia <b>Pionero</b>, que solo tienen los que prueban " +
    "el juego antes del lanzamiento. &#129351;</div></td></tr>" +
    // Recuadro oscuro: los 14 días
    '<tr><td style="background:' + C.night2 + ';border:4px solid ' + C.wood + ';border-top:0;padding:16px 24px;' + F +
    'color:' + C.light + ';font-size:15px;line-height:1.5">' +
    '<span style="color:' + C.gold + ';font-weight:bold">&#9733; Los 14 días</span><br>' +
    "Para que el juego pueda salir para todos, Google nos pide que los testers lo mantengan instalado y lo abran " +
    "<b>durante 14 días</b>. Así que si podés, entrá aunque sea un ratito cada día. " +
    '<b style="color:' + C.gold + '">¡Nos ayuda muchísimo!</b></td></tr>' +
    // Pie: base dorada con los rótulos de región
    '<tr><td style="line-height:0;border:4px solid ' + C.goldDark + ';border-top:0;border-radius:0 0 6px 6px;overflow:hidden">' +
    '<img src="' + IMG + 'pie.png" width="592" alt="" style="display:block;width:100%;height:auto;border:0"></td></tr>' +
    '<tr><td style="padding:14px 8px;text-align:center;' + F + 'font-size:13px;color:' + C.dim + ';line-height:1.5">' +
    "Si encontrás un error o tenés una idea, respondé este mail.<br>" +
    '<b style="color:' + C.light + '">¡Gracias por ser de los primeros!</b><br>El equipo de Coronados de Gloria<br>' +
    '<a href="https://coronadosdegloria.web.app" style="color:' + C.gold + '">coronadosdegloria.web.app</a></td></tr>' +
    "</table></td></tr></table></body></html>";
}

function mailText(email, name) {
  return [
    "¡Hola!",
    "",
    "Te anotaste para la prueba cerrada de Coronados de Gloria y ya está lista. Para entrar, usá tu celular Android",
    "con la misma cuenta de Google con la que te anotaste (" + email + "):",
    "",
    "1. Unite al grupo de pioneros (tocá \"Unirse al grupo\"):",
    "   👉 " + GROUP_URL,
    "2. Abrí este link y tocá \"Ser tester\" (o \"Unirse\"):",
    "   👉 " + OPTIN_URL,
    "3. Instalá el juego desde Google Play:",
    "   👉 " + STORE_URL,
    "",
    "Mientras juegues esta versión vas a ganar la insignia Pionero, que solo tienen los que prueban el juego antes del lanzamiento. 🥇",
    "",
    "Para que el juego pueda salir para todos, Google nos pide que los testers lo mantengan instalado y lo abran durante 14 días. Así que si podés, entrá aunque sea un ratito cada día. ¡Nos ayuda muchísimo!",
    "",
    "Si encontrás un error o tenés una idea, respondé este mail.",
    "",
    "¡Gracias por ser de los primeros!",
    "El equipo de Coronados de Gloria",
  ].join("\n");
}
