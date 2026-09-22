// Puente de email de Cronochat.
//
// Salida: cada mensaje con `correo` se entrega por email cuando su hora ha
// llegado en la linea de origen (al futuro, a su hora; al presente y al
// pasado, al enviarlo). El proveedor es Resend (API HTTP, sin dependencias);
// cambiarlo es cambiar `enviarCorreo`.
//
// Entrada: un proveedor de correo entrante (Postmark, Resend, Mailgun,
// CloudMailin...) reenvia cada email como JSON a /api/correo-entrante. La
// direccion de destino codifica sala e instante:
//
//   familia@tu-dominio                   -> sala "familia", ahora
//   familia+2030@tu-dominio              -> 1 ene 2030 00:00:00 UTC
//   familia+2030-06-01@tu-dominio        -> 1 jun 2030
//   familia+2030-06-01t10-30-00@...      -> 1 jun 2030 10:30:00 UTC
//   familia+1995-06-01@tu-dominio        -> al pasado: abre una rama

import { ORIGEN } from "./cronologia.mjs";

export const MAX_INTENTOS = 5;

export function configuracionCorreo(env) {
  return {
    clave: env.RESEND_API_KEY ?? "",
    remitente: env.CRONOCHAT_REMITENTE ?? "",
    sitio: (env.URL ?? env.CRONOCHAT_URL ?? "").replace(/\/$/, ""),
    permitidos: env.CRONOCHAT_CORREOS_PERMITIDOS ?? "",
    claveEntrante: env.CRONOCHAT_CLAVE_ENTRANTE ?? "",
  };
}

// Listo para salir en `ahoraMs`: pendiente, con intentos, y ya ha llegado su
// hora en la linea de origen.
export function debeSalir(m, ahoraMs) {
  if (!m.correo || m.correo.estado !== "pendiente" || m.correo.intentos >= MAX_INTENTOS) return false;
  if (m.direccion === "futuro") return Date.parse(m.destino) <= ahoraMs;
  return true;
}

function escaparHtml(t) {
  return String(t).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

const fecha = (iso) => new Date(iso).toISOString().replace("T", " ").replace(/\.\d+Z$/, " UTC");

export function componerCorreo(m, sitio) {
  const enlace = sitio ? `${sitio}/#${m.sala}` : "";
  let asunto;
  let cabecera;
  if (m.direccion === "futuro") {
    asunto = `Cronochat · ${m.autor} te escribió desde ${fecha(m.enviadoEn)}`;
    cabecera = `Mensaje sellado el ${fecha(m.enviadoEn)} para abrirse el ${fecha(m.destino)}.\n` +
      `Compromiso SHA-256: ${m.compromiso}\nNonce: ${m.nonce}`;
  } else if (m.rama !== ORIGEN) {
    asunto = `Cronochat · ${m.autor} → ${fecha(m.destino)} (${m.rama})`;
    cabecera = `Enviado el ${fecha(m.enviadoEn)} hacia el ${fecha(m.destino)}.\n` +
      `Llegó en la rama ${m.rama} (regla del fork): ${m.paresEntrelazados} pares entrelazados, ` +
      `peso de Born 10^${m.log10PesoBorn.toFixed(1)}.\n` +
      "Este email te llega en la línea de origen, que es donde está tu buzón.";
  } else {
    asunto = `Cronochat · ${m.autor} en #${m.sala}`;
    cabecera = `Enviado el ${fecha(m.enviadoEn)}.`;
  }
  const texto = `${m.texto}\n\n— ${m.autor}\n\n${cabecera}${enlace ? `\n\nResponder en la sala: ${enlace}` : ""}\n`;
  const html = `<div style="font-family:system-ui,sans-serif;max-width:560px">` +
    `<p style="white-space:pre-wrap;font-size:16px">${escaparHtml(m.texto)}</p>` +
    `<p style="color:#667781">— ${escaparHtml(m.autor)}</p>` +
    `<pre style="color:#667781;font-size:12px;white-space:pre-wrap">${escaparHtml(cabecera)}</pre>` +
    (enlace ? `<p><a href="${escaparHtml(enlace)}">Abrir #${escaparHtml(m.sala)} en Cronochat</a></p>` : "") +
    `</div>`;
  return { asunto, texto, html };
}

export async function enviarCorreo(m, config, fetchFn = fetch) {
  if (!config.clave || !config.remitente) {
    return { ok: false, error: "puente de salida sin configurar (RESEND_API_KEY, CRONOCHAT_REMITENTE)" };
  }
  const { asunto, texto, html } = componerCorreo(m, config.sitio);
  const res = await fetchFn("https://api.resend.com/emails", {
    method: "POST",
    headers: { authorization: `Bearer ${config.clave}`, "content-type": "application/json",
      "idempotency-key": `cronochat-${m.id}` },
    body: JSON.stringify({ from: config.remitente, to: m.correo.para, subject: asunto, text: texto, html }),
  });
  if (res.ok) return { ok: true };
  return { ok: false, error: `proveedor ${res.status}: ${(await res.text()).slice(0, 200)}` };
}

// Intenta la entrega y devuelve el mensaje con su estado actualizado.
export async function entregar(m, config, ahoraMs, fetchFn = fetch) {
  let r;
  try {
    r = await enviarCorreo(m, config, fetchFn);
  } catch (err) {
    r = { ok: false, error: String(err?.message ?? err) };
  }
  const intentos = m.correo.intentos + 1;
  const correo = r.ok
    ? { ...m.correo, estado: "enviado", intentos, enviadoEn: new Date(ahoraMs).toISOString() }
    : { ...m.correo, estado: intentos >= MAX_INTENTOS ? "error" : "pendiente", intentos, error: r.error };
  return { ...m, correo };
}

// ------------------------------------------------------------- entrada
const DESTINO_RE = /^(\d{4})(?:-(\d{2})(?:-(\d{2})(?:t(\d{2})-(\d{2})(?:-(\d{2}))?)?)?)?$/;

export function destinoDeEtiqueta(etiqueta) {
  if (!etiqueta) return null;
  const m = DESTINO_RE.exec(etiqueta.toLowerCase());
  if (!m) return undefined;
  const [, a, mes = "01", d = "01", h = "00", min = "00", s = "00"] = m;
  const iso = `${a}-${mes}-${d}T${h}:${min}:${s}Z`;
  return Number.isFinite(Date.parse(iso)) ? iso : undefined;
}

// Los proveedores mandan la direccion como texto ("Ana <ana@x.es>"), como
// objeto ({Email, Name}) o como lista de cualquiera de los dos.
function primera(valor) {
  return Array.isArray(valor) ? valor[0] : valor;
}

function primeraDireccion(valor) {
  const v = primera(valor);
  const t = String(typeof v === "object" && v ? v.Email ?? v.email ?? v.address ?? "" : v ?? "");
  const angulo = /<([^>]+)>/.exec(t);
  return (angulo ? angulo[1] : t.split(",")[0]).trim().toLowerCase();
}

function nombreDe(valor) {
  const v = primera(valor);
  const t = String(typeof v === "object" && v ? v.Name ?? v.name ?? "" : v ?? "");
  const nombre = t.replace(/<[^>]*>/, "").replace(/"/g, "").trim();
  if (nombre && !nombre.includes("@")) return nombre;
  return primeraDireccion(valor).split("@")[0] || "email";
}

// Quita la cita del correo al que se responde y la firma "-- ".
export function limpiarCuerpo(texto) {
  const lineas = String(texto ?? "").replace(/\r\n/g, "\n").split("\n");
  const fin = lineas.findIndex((l) => /^\s*>/.test(l) || /^(El|On) .+(escribió|wrote):\s*$/.test(l.trim()) || l === "-- ");
  return (fin === -1 ? lineas : lineas.slice(0, fin)).join("\n").trim();
}

// Normaliza el JSON de cualquier proveedor (campos de Postmark, Resend,
// Mailgun o genericos) a una entrada de `crearMensaje`.
export function entradaDeCorreo(cuerpo) {
  const para = primeraDireccion(cuerpo.To ?? cuerpo.to ?? cuerpo.recipient ?? cuerpo.OriginalRecipient);
  const local = para.split("@")[0] ?? "";
  const [sala, etiqueta] = local.split("+");
  const destino = destinoDeEtiqueta(etiqueta);
  if (destino === undefined) {
    return { error: `etiqueta de destino no valida: +${etiqueta} (usa AAAA, AAAA-MM-DD o AAAA-MM-DDtHH-MM-SS)` };
  }
  const de = cuerpo.FromFull ?? cuerpo.From ?? cuerpo.from ?? cuerpo.sender;
  const texto = limpiarCuerpo(cuerpo.StrippedTextReply || cuerpo.TextBody || cuerpo.text ||
    cuerpo["stripped-text"] || cuerpo["body-plain"] || "") || String(cuerpo.Subject ?? cuerpo.subject ?? "").trim();
  return { sala, autor: `${nombreDe(de)} ✉`.slice(0, 40), texto: texto.slice(0, 2000), destino };
}
