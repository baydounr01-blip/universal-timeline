// Cronochat: protocolo y API con un almacen en memoria.
import assert from "node:assert/strict";
import { test } from "node:test";

import {
  ErrorCronochat,
  crearMensaje,
  direccion,
  lineaTemporal,
  log10PesoBorn,
  verificarCompromiso,
  vistaDe,
} from "../netlify/functions/_lib/cronologia.mjs";
import { manejar } from "../netlify/functions/cronochat.mjs";

const T0 = Date.parse("2026-09-22T12:00:00Z");
const iso = (ms) => new Date(ms).toISOString();
const ANIO = 365.25 * 24 * 3600e3;

function almacen() {
  const datos = new Map();
  return {
    async list({ prefix }) {
      return { blobs: [...datos.keys()].filter((k) => k.startsWith(prefix)).map((key) => ({ key })) };
    },
    async get(key) { return datos.has(key) ? structuredClone(datos.get(key)) : null; },
    async setJSON(key, v) { datos.set(key, structuredClone(v)); },
  };
}

const post = (store, cuerpo, ahora = T0) => manejar(new Request("https://x/api/cronochat",
  { method: "POST", body: JSON.stringify(cuerpo) }), store, ahora);
const get = (store, q, ahora = T0) => manejar(new Request(`https://x/api/cronochat?${q}`), store, ahora);

test("direccion: presente, futuro y pasado", () => {
  assert.equal(direccion(T0 + 800, T0), "presente");
  assert.equal(direccion(T0 + 3000, T0), "futuro");
  assert.equal(direccion(T0 - ANIO, T0), "pasado");
});

test("un mensaje al futuro llega sellado y se abre a su hora con compromiso verificable", async () => {
  const m = await crearMensaje({ sala: "s", autor: "rami", texto: "hola 2027", destino: iso(T0 + ANIO) }, T0);
  const antes = vistaDe(m, T0 + ANIO - 1000);
  assert.equal(antes.sellado, true);
  assert.equal(antes.texto, undefined);
  assert.equal(antes.nonce, undefined);
  assert.ok(antes.faltaMs > 0);
  const despues = vistaDe(m, T0 + ANIO);
  assert.equal(despues.texto, "hola 2027");
  assert.ok(await verificarCompromiso(despues));
  assert.equal(await verificarCompromiso({ ...despues, texto: "otro" }), false);
});

test("un mensaje al pasado abre una rama y no reescribe el origen (regla del fork)", async () => {
  const store = almacen();
  await post(store, { sala: "s", autor: "a", texto: "antes", destino: iso(T0 - 2 * ANIO) }, T0);
  // "antes" viajo 2 anios atras: esta en su rama, no en el origen.
  const res = await post(store, { sala: "s", autor: "b", texto: "de hoy", destino: null }, T0);
  assert.equal(res.status, 201);
  const retro = await (await post(store, { sala: "s", autor: "c", texto: "hola 1995",
    destino: "1995-06-01T10:00:00Z" }, T0 + 10_000)).json();
  assert.equal(retro.mensaje.direccion, "pasado");
  assert.match(retro.mensaje.rama, /^rama-/);
  assert.equal(retro.mensaje.paresEntrelazados, 9 * 8);
  assert.ok(Math.abs(retro.mensaje.log10PesoBorn - log10PesoBorn(72)) < 1e-12);

  const origen = await (await get(store, "sala=s", T0 + 20_000)).json();
  const enOrigen = origen.mensajes.find((m) => m.texto === "hola 1995");
  assert.equal(enOrigen.salida, true);                   // aparece donde se ENVIO
  assert.equal(enOrigen.momento, iso(T0 + 10_000));
  assert.equal(origen.ramas.length, 2);

  const rama = await (await get(store, `sala=s&rama=${retro.mensaje.rama}`, T0 + 20_000)).json();
  assert.deepEqual(rama.mensajes.map((m) => m.texto), ["hola 1995"]); // nada del origen era anterior a 1995
  assert.equal(rama.mensajes[0].llegada, true);
  assert.equal(rama.mensajes[0].momento, "1995-06-01T10:00:00.000Z");
});

test("una rama hereda el origen anterior a la bifurcacion", async () => {
  const store = almacen();
  await post(store, { sala: "h", autor: "a", texto: "primero" }, T0);
  const r = await (await post(store, { sala: "h", autor: "b", texto: "atras 1 min",
    destino: iso(T0 + 30_000) }, T0 + 90_000)).json();
  await post(store, { sala: "h", autor: "a", texto: "despues" }, T0 + 60_000);
  const rama = await (await get(store, `sala=h&rama=${r.mensaje.rama}`, T0 + 100_000)).json();
  assert.deepEqual(rama.mensajes.map((m) => [m.texto, m.heredado, m.llegada]),
    [["primero", true, false], ["atras 1 min", false, true]]);
});

test("el transporte fisico no existe: se rechaza, no se finge", async () => {
  const ancla = { id: "ancla-1", creadaEn: "1999-01-01T00:00:00Z", codigos: [] };
  await assert.rejects(
    crearMensaje({ sala: "s", autor: "a", texto: "x", destino: "2000-01-01T00:00:00Z" }, T0, "fisico",
      { anclas: [ancla] }),
    (e) => e instanceof ErrorCronochat && e.status === 503);
});

test("sin receptor anclado, el canal fisico no llega a ese instante", async () => {
  const ancla = { id: "ancla-1", creadaEn: "2001-01-01T00:00:00Z", codigos: [] };
  await assert.rejects(
    crearMensaje({ sala: "s", autor: "a", texto: "x", destino: "2000-01-01T00:00:00Z" }, T0, "fisico",
      { anclas: [ancla] }),
    (e) => e instanceof ErrorCronochat && e.status === 409);
});

test("validacion de entrada", async () => {
  const store = almacen();
  for (const malo of [
    { sala: "S A", autor: "a", texto: "x" },
    { sala: "s", autor: "", texto: "x" },
    { sala: "s", autor: "a", texto: "   " },
    { sala: "s", autor: "a", texto: "x".repeat(2001) },
    { sala: "s", autor: "a", texto: "x", destino: "no-es-fecha" },
  ]) {
    assert.equal((await post(store, malo)).status, 400, JSON.stringify(malo).slice(0, 60));
  }
  assert.equal((await get(store, "sala=s&rama=rama-nada")).status, 404);
  assert.equal((await manejar(new Request("https://x/api/cronochat", { method: "PUT" }), store)).status, 405);
});

test("el origen muestra el futuro sellado para el lector de hoy", async () => {
  const store = almacen();
  await post(store, { sala: "f", autor: "a", texto: "secreto", destino: iso(T0 + 3_600_000) });
  const hoy = await (await get(store, "sala=f")).json();
  assert.equal(hoy.mensajes[0].sellado, true);
  assert.equal(JSON.stringify(hoy).includes("secreto"), false);
  const luego = await (await get(store, "sala=f", T0 + 3_600_000)).json();
  assert.equal(luego.mensajes[0].texto, "secreto");
});
