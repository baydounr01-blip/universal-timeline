// El puente hacia el pasado, tal como lo exige la propia teoria.
//
// 1. Ancla (receptor). En la teleportacion postseleccionada (P-CTC, E7a) la
//    mitad del par entrelazado tiene que estar en t0 antes de que t1
//    escriba. Un canal no llega a un instante en el que nadie guardaba su
//    otro extremo: igual que una maquina del tiempo de agujero de gusano no
//    lleva a antes de su construccion. Un ancla es ese extremo: se crea hoy
//    y desde ese instante la sala puede recibir del futuro.
//
// 2. Diccionario. La rama en la que el bucle cierra pesa 4^-bits. Si el
//    ancla fija de antemano N mensajes posibles, cualquiera de ellos cuesta
//    ceil(log2 N) bits en vez de 8 por byte: un "si/no" pesa 1/4 en lugar de
//    4^-16.
//
// 3. Faro (detector P12). Cada hora el servidor revela un pulso secreto de
//    64 bits. Un mensaje que cita un pulso antes de que se revele contiene
//    informacion que aun no existia: la firma observable del canal. Sin
//    canal (y sin fuga del secreto) no se dispara nunca.

import { ErrorCronochat } from "./cronologia.mjs";

export const HORA_MS = 3_600_000;
export const MAX_CODIGOS = 256;
export const MAX_CODIGO = 200;
export const MAX_ANCLAS_SALA = 20;
export const PREFIJO_ANCLAS = "_anclas/";
export const CLAVE_SECRETO = "_faro/secreto";

const FARO_RE = /faro:(\d{1,9}):([0-9a-f]{16})/gi;
const MAX_CITAS = 5;

const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");

function nuevoId() {
  return hex(crypto.getRandomValues(new Uint8Array(6)));
}

// ------------------------------------------------------------------ ancla
export function crearAncla(sala, entrada, ahoraMs) {
  const autor = String(entrada?.autor ?? "").trim().slice(0, 40);
  if (!autor) throw new ErrorCronochat("el ancla necesita un nombre");
  const lista = Array.isArray(entrada?.codigos)
    ? entrada.codigos
    : String(entrada?.codigos ?? "").split("\n");
  const codigos = [...new Set(lista.map((c) => String(c).trim()).filter(Boolean))];
  if (codigos.length > MAX_CODIGOS) throw new ErrorCronochat(`como maximo ${MAX_CODIGOS} codigos`);
  if (codigos.some((c) => c.length > MAX_CODIGO)) {
    throw new ErrorCronochat(`cada codigo tiene como maximo ${MAX_CODIGO} caracteres`);
  }
  return { id: `ancla-${nuevoId()}`, sala, autor, creadaEn: new Date(ahoraMs).toISOString(), codigos };
}

// El receptor de un mensaje al pasado: el ancla mas reciente que ya existia
// en el instante de destino. Sin ella, el mensaje no tiene donde llegar.
export function receptorPara(anclas, destinoMs) {
  return anclas
    .filter((a) => Date.parse(a.creadaEn) <= destinoMs)
    .sort((a, b) => Date.parse(b.creadaEn) - Date.parse(a.creadaEn))[0] ?? null;
}

export function bitsDiccionario(n) {
  return Math.max(1, Math.ceil(Math.log2(n)));
}

// Si el texto es una entrada del diccionario del receptor, viaja como su
// indice: ceil(log2 N) bits.
export function codificar(texto, ancla) {
  const i = ancla?.codigos?.indexOf(texto.trim()) ?? -1;
  if (i < 0) return null;
  return { codigo: i, de: ancla.codigos.length, bits: bitsDiccionario(ancla.codigos.length) };
}

// ------------------------------------------------------------------- faro
export const epocaDe = (ms) => Math.floor(ms / HORA_MS);
export const revelaEn = (epoca) => epoca * HORA_MS;

async function claveHmac(secreto) {
  return crypto.subtle.importKey("raw", new TextEncoder().encode(secreto),
    { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
}

export async function pulso(secreto, epoca) {
  const firma = await crypto.subtle.sign("HMAC", await claveHmac(secreto), new TextEncoder().encode(`faro:${epoca}`));
  return hex(firma).slice(0, 16);
}

// Busca citas "faro:<epoca>:<pulso>" de pulsos que en `ahoraMs` todavia no
// se habian revelado. Una cita correcta es una deteccion.
export async function detectar(texto, secreto, ahoraMs) {
  if (!secreto) return null;
  const citas = [...String(texto).matchAll(FARO_RE)].slice(0, MAX_CITAS);
  for (const [, e, p] of citas) {
    const epoca = Number(e);
    if (revelaEn(epoca) <= ahoraMs) continue;
    if ((await pulso(secreto, epoca)) === p.toLowerCase()) {
      return { epoca, pulso: p.toLowerCase(), antelacionMs: revelaEn(epoca) - ahoraMs };
    }
  }
  return null;
}

export async function estadoFaro(secreto, ahoraMs, n = 6) {
  const actual = epocaDe(ahoraMs);
  const pulsos = [];
  for (let e = actual; e > actual - n; e--) {
    pulsos.push({ epoca: e, revelado: new Date(revelaEn(e)).toISOString(), pulso: await pulso(secreto, e) });
  }
  return { epoca: actual, proximo: new Date(revelaEn(actual + 1)).toISOString(), pulsos };
}

// El secreto del faro: de la variable de entorno o, si no hay, uno aleatorio
// guardado en el almacen la primera vez.
export async function secretoFaro(store, env = {}) {
  if (env.CRONOCHAT_SECRETO_FARO) return env.CRONOCHAT_SECRETO_FARO;
  const guardado = await store.get(CLAVE_SECRETO, { type: "json" });
  if (guardado?.secreto) return guardado.secreto;
  const secreto = hex(crypto.getRandomValues(new Uint8Array(32)));
  await store.setJSON(CLAVE_SECRETO, { secreto });
  return secreto;
}
