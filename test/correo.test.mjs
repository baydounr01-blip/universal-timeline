// Puente de email: salida (inmediata y programada) y entrada.
import assert from "node:assert/strict";
import { test } from "node:test";

import { crearMensaje, validarCorreos } from "../netlify/functions/_lib/cronologia.mjs";
import {
  MAX_INTENTOS, componerCorreo, debeSalir, destinoDeEtiqueta, entradaDeCorreo, limpiarCuerpo,
} from "../netlify/functions/_lib/correo.mjs";
import { manejar } from "../netlify/functions/cronochat.mjs";
import { repartir } from "../netlify/functions/correo-programado.mjs";
import { recibir } from "../netlify/functions/correo-entrante.mjs";

const T0 = Date.parse("2026-09-22T12:00:00Z");
const ENV = {
  RESEND_API_KEY: "re_test", CRONOCHAT_REMITENTE: "Cronochat <chat@ejemplo.org>",
  URL: "https://crono.netlify.app", CRONOCHAT_CORREOS_PERMITIDOS: "rami@correo.es, @familia.org",
  CRONOCHAT_CLAVE_ENTRANTE: "secreto-largo",
};

function almacen() {
  const datos = new Map();
  return {
    datos,
    async list({ prefix = "" } = {}) {
      return { blobs: [...datos.keys()].filter((k) => k.startsWith(prefix)).map((key) => ({ key })) };
    },
    async get(key) { return datos.has(key) ? structuredClone(datos.get(key)) : null; },
    async setJSON(key, v) { datos.set(key, structuredClone(v)); },
  };
}

function proveedor(status = 200) {
  const enviados = [];
  const fetchFn = async (url, init) => {
    enviados.push({ url, init, cuerpo: JSON.parse(init.body) });
    return new Response(status === 200 ? '{"id":"x"}' : "fallo", { status });
  };
  return { enviados, fetchFn };
}

const post = (store, cuerpo, { ahora = T0, env = ENV, fetchFn } = {}) =>
  manejar(new Request("https://x/api/cronochat", { method: "POST", body: JSON.stringify(cuerpo) }),
    store, ahora, env, fetchFn);

test("sin lista blanca el puente de salida esta cerrado", () => {
  assert.throws(() => validarCorreos("a@b.es", []), /no esta activado/);
  assert.deepEqual(validarCorreos("", []), []);
});

test("solo destinatarios autorizados, como mucho 3", () => {
  const p = ["rami@correo.es", "@familia.org"];
  assert.deepEqual(validarCorreos("Rami@Correo.es, tia@familia.org", p), ["rami@correo.es", "tia@familia.org"]);
  assert.throws(() => validarCorreos("otro@spam.com", p), (e) => e.status === 403);
  assert.throws(() => validarCorreos("no-es-email", p), /no valida/);
  assert.throws(() => validarCorreos("a@familia.org,b@familia.org,c@familia.org,d@familia.org", p), /maximo/);
});

test("un mensaje al presente sale por email al momento y la API no revela la direccion", async () => {
  const store = almacen();
  const { enviados, fetchFn } = proveedor();
  const res = await post(store, { sala: "fam", autor: "Rami", texto: "hola", correos: "rami@correo.es" }, { fetchFn });
  assert.equal(res.status, 201);
  const cuerpo = await res.json();
  assert.deepEqual(cuerpo.mensaje.correo, { destinatarios: 1, estado: "enviado" });
  assert.equal(enviados.length, 1);
  assert.equal(enviados[0].url, "https://api.resend.com/emails");
  assert.deepEqual(enviados[0].cuerpo.to, ["rami@correo.es"]);
  assert.equal(enviados[0].init.headers.authorization, "Bearer re_test");
  const lectura = await (await manejar(new Request("https://x/api/cronochat?sala=fam"), store, T0, ENV)).text();
  assert.equal(lectura.includes("rami@correo.es"), false);
  assert.equal(JSON.parse(lectura).puenteCorreo, true);
});

test("un mensaje al futuro espera sellado y el cartero lo entrega a su hora", async () => {
  const store = almacen();
  const { enviados, fetchFn } = proveedor();
  const destino = new Date(T0 + 3_600_000).toISOString();
  await post(store, { sala: "fam", autor: "Rami", texto: "para dentro de una hora", destino,
    correos: ["tia@familia.org"] }, { fetchFn });
  assert.equal(enviados.length, 0);
  assert.deepEqual(await repartir(store, cfg(), T0 + 3_599_000, fetchFn), { revisados: 1, enviados: 0, fallidos: 0 });
  assert.deepEqual(await repartir(store, cfg(), T0 + 3_600_000, fetchFn), { revisados: 1, enviados: 1, fallidos: 0 });
  assert.match(enviados[0].cuerpo.subject, /te escribió desde 2026-09-22 12:00:00 UTC/);
  assert.match(enviados[0].cuerpo.text, /para dentro de una hora/);
  assert.match(enviados[0].cuerpo.text, /Compromiso SHA-256: [0-9a-f]{64}/);
  // Entregado: no se repite.
  await repartir(store, cfg(), T0 + 7_200_000, fetchFn);
  assert.equal(enviados.length, 1);
});

const cfg = () => ({ clave: "re_test", remitente: "chat@ejemplo.org", sitio: "https://crono.netlify.app",
  permitidos: ENV.CRONOCHAT_CORREOS_PERMITIDOS, claveEntrante: "" });

test("si el proveedor falla se reintenta y tras MAX_INTENTOS queda en error", async () => {
  const store = almacen();
  const { fetchFn } = proveedor(500);
  await post(store, { sala: "fam", autor: "R", texto: "x", correos: "rami@correo.es" }, { fetchFn });
  for (let i = 1; i < MAX_INTENTOS; i++) await repartir(store, cfg(), T0 + i * 60_000, fetchFn);
  const [, m] = [...store.datos].find(([k]) => !k.startsWith("_"));
  assert.equal(m.correo.estado, "error");
  assert.equal(m.correo.intentos, MAX_INTENTOS);
  assert.match(m.correo.error, /proveedor 500/);
  assert.equal(debeSalir(m, T0 + 3_600_000), false);
});

test("al pasado: el email llega hoy, contando la rama en la que llego", async () => {
  const m = await crearMensaje({ sala: "fam", autor: "Rami", texto: "hola 1995",
    destino: "1995-06-01T10:00:00Z", correos: "rami@correo.es" }, T0, "simulado",
  { permitidos: ["rami@correo.es"] });
  assert.equal(debeSalir(m, T0), true);
  const { asunto, texto, html } = componerCorreo(m, "https://crono.netlify.app");
  assert.match(asunto, /1995-06-01 10:00:00 UTC \(rama-/);
  assert.match(texto, /regla del fork/);
  assert.match(texto, /https:\/\/crono\.netlify\.app\/#fam/);
  assert.equal(html.includes("<script"), false);
});

test("el html escapa el texto del mensaje", async () => {
  const m = await crearMensaje({ sala: "fam", autor: "<b>x</b>", texto: "<script>alert(1)</script>" }, T0);
  const { html } = componerCorreo({ ...m, correo: { para: [] } }, "");
  assert.equal(html.includes("<script>"), false);
  assert.match(html, /&lt;script&gt;/);
});

test("etiquetas de destino en la direccion", () => {
  assert.equal(destinoDeEtiqueta(undefined), null);
  assert.equal(destinoDeEtiqueta("2030"), "2030-01-01T00:00:00Z");
  assert.equal(destinoDeEtiqueta("2030-06-01"), "2030-06-01T00:00:00Z");
  assert.equal(destinoDeEtiqueta("2030-06-01T10-30-15"), "2030-06-01T10:30:15Z");
  assert.equal(destinoDeEtiqueta("mañana"), undefined);
});

test("limpieza del cuerpo: fuera la cita y la firma", () => {
  assert.equal(limpiarCuerpo("hola\r\nqué tal\r\n\r\nEl lun, 1 ene 2030, Ana escribió:\r\n> antes"), "hola\nqué tal");
  assert.equal(limpiarCuerpo("uno\n-- \nfirma"), "uno");
});

test("normaliza Postmark y formatos genericos", () => {
  const pm = entradaDeCorreo({ FromFull: { Email: "ana@x.es", Name: "Ana" }, From: "Ana <ana@x.es>",
    To: "fam+2030-06-01@crono.org", TextBody: "hola futuro", Subject: "s" });
  assert.deepEqual(pm, { sala: "fam", autor: "Ana ✉", texto: "hola futuro", destino: "2030-06-01T00:00:00Z" });
  const gen = entradaDeCorreo({ from: "luis@y.es", to: ["fam@crono.org"], text: "", subject: "solo asunto" });
  assert.deepEqual(gen, { sala: "fam", autor: "luis ✉", texto: "solo asunto", destino: null });
  assert.match(entradaDeCorreo({ to: "fam+ayer@c.org", text: "x" }).error, /etiqueta/);
});

test("entrada: sin clave o con clave mala no entra nada; con clave abre rama o sella", async () => {
  const store = almacen();
  const req = (clave, cuerpo) => new Request(`https://x/api/correo-entrante?clave=${clave}`,
    { method: "POST", body: JSON.stringify(cuerpo) });
  const email = { From: "Ana <ana@x.es>", To: "fam+1995-06-01@crono.org", TextBody: "hola 1995" };
  assert.equal((await recibir(req("x", email), store, { ...ENV, CRONOCHAT_CLAVE_ENTRANTE: "" }, T0)).status, 503);
  assert.equal((await recibir(req("mala", email), store, ENV, T0)).status, 401);
  const ok = await recibir(req("secreto-largo", email), store, ENV, T0);
  assert.equal(ok.status, 201);
  const m = (await ok.json()).mensaje;
  assert.equal(m.direccion, "pasado");
  assert.match(m.rama, /^rama-/);
  assert.equal(m.autor, "Ana ✉");
  const futuro = await (await recibir(req("secreto-largo", { ...email, To: "fam+2030@crono.org" }),
    store, ENV, T0)).json();
  assert.equal(futuro.mensaje.sellado, true);
  assert.equal(futuro.mensaje.texto, undefined);
});
