// El puente: receptor anclado, diccionario y detector P12 (faro).
import assert from "node:assert/strict";
import { test } from "node:test";

import { crearMensaje, log10PesoBorn, vistaDe } from "../netlify/functions/_lib/cronologia.mjs";
import {
  CLAVE_SECRETO, HORA_MS, bitsDiccionario, crearAncla, detectar, epocaDe, pulso, receptorPara, revelaEn,
} from "../netlify/functions/_lib/puente.mjs";
import { manejar } from "../netlify/functions/cronochat.mjs";
import { debeSalir } from "../netlify/functions/_lib/correo.mjs";

const T0 = Date.parse("2026-09-22T12:30:00Z");
const ANIO = 365.25 * 24 * 3600e3;
const iso = (ms) => new Date(ms).toISOString();
const SECRETO = "secreto-de-prueba";

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
const post = (store, cuerpo, ahora = T0, env = {}) => manejar(new Request("https://x/api/cronochat",
  { method: "POST", body: JSON.stringify(cuerpo) }), store, ahora, env);
const get = (store, q, ahora = T0, env = {}) =>
  manejar(new Request(`https://x/api/cronochat?${q}`), store, ahora, env);

test("el diccionario cuesta ceil(log2 N) bits", () => {
  assert.equal(bitsDiccionario(1), 1);
  assert.equal(bitsDiccionario(2), 1);
  assert.equal(bitsDiccionario(16), 4);
  assert.equal(bitsDiccionario(17), 5);
  assert.equal(bitsDiccionario(256), 8);
});

test("el receptor es el ancla mas reciente que ya existia en el destino", () => {
  const a = { id: "a", creadaEn: "2020-01-01T00:00:00Z" };
  const b = { id: "b", creadaEn: "2024-01-01T00:00:00Z" };
  assert.equal(receptorPara([a, b], Date.parse("2019-01-01T00:00:00Z")), null);
  assert.equal(receptorPara([a, b], Date.parse("2022-01-01T00:00:00Z")).id, "a");
  assert.equal(receptorPara([b, a], Date.parse("2025-01-01T00:00:00Z")).id, "b");
});

test("un mensaje del diccionario viaja como su indice: el peso de Born sube en ordenes de magnitud", async () => {
  const codigos = ["si", "no", "espera", "todo bien", "peligro", "llama", "ven", "no vengas",
    "compra", "vende", "te quiero", "perdona", "gracias", "adios", "ok", "?"];
  const ancla = crearAncla("s", { autor: "rami", codigos }, T0 - ANIO);
  const destino = iso(T0 - ANIO / 2);
  const cod = await crearMensaje({ sala: "s", autor: "a", texto: "todo bien", destino }, T0, "simulado",
    { anclas: [ancla] });
  assert.equal(cod.receptor, ancla.id);
  assert.deepEqual(cod.codigo, { indice: 3, de: 16 });
  assert.equal(cod.paresEntrelazados, 4);
  assert.equal(cod.log10PesoBorn, log10PesoBorn(4));

  const fuera = await crearMensaje({ sala: "s", autor: "a", texto: "no esta en la lista", destino }, T0,
    "simulado", { anclas: [ancla] });
  assert.equal(fuera.codigo, undefined);
  assert.equal(fuera.paresEntrelazados, 8 * "no esta en la lista".length);
});

test("antes del ancla no hay receptor: el simulado abre rama, pero sin receptor", async () => {
  const ancla = crearAncla("s", { autor: "rami" }, T0 - ANIO);
  const m = await crearMensaje({ sala: "s", autor: "a", texto: "x", destino: iso(T0 - 2 * ANIO) }, T0,
    "simulado", { anclas: [ancla] });
  assert.equal(m.receptor, null);
  assert.match(m.rama, /^rama-/);
});

test("faro: solo detecta pulsos citados antes de revelarse", async () => {
  const futura = epocaDe(T0) + 3;
  const p = await pulso(SECRETO, futura);
  assert.match(p, /^[0-9a-f]{16}$/);
  const d = await detectar(`hola faro:${futura}:${p}`, SECRETO, T0);
  assert.equal(d.epoca, futura);
  assert.equal(d.antelacionMs, revelaEn(futura) - T0);
  // El mismo pulso, citado cuando ya es publico, no prueba nada.
  assert.equal(await detectar(`faro:${futura}:${p}`, SECRETO, revelaEn(futura)), null);
  // Un pulso inventado no dispara.
  assert.equal(await detectar(`faro:${futura}:0123456789abcdef`, SECRETO, T0), null);
  assert.equal(await detectar("sin citas", SECRETO, T0), null);
});

test("un pulso detectado queda oculto hasta su hora, para que nadie lo copie", async () => {
  const futura = epocaDe(T0) + 1;
  const p = await pulso(SECRETO, futura);
  const m = await crearMensaje({ sala: "s", autor: "a", texto: `faro:${futura}:${p}` }, T0, "simulado",
    { secretoFaro: SECRETO });
  assert.ok(m.deteccion);
  const antes = vistaDe(m, T0);
  assert.ok(!antes.texto.includes(p));
  assert.equal(antes.deteccion.pulso, undefined);
  const despues = vistaDe(m, revelaEn(futura));
  assert.ok(despues.texto.includes(p));
  const conCorreo = { ...m, correo: { para: ["a@b.es"], estado: "pendiente", intentos: 0 } };
  assert.equal(debeSalir(conCorreo, T0), false);
  assert.equal(debeSalir(conCorreo, revelaEn(futura)), true);
});

test("API: anclar, ver el faro y registrar una deteccion", async () => {
  const store = almacen();
  const env = { CRONOCHAT_SECRETO_FARO: SECRETO };
  const r = await post(store, { accion: "anclar", sala: "fam", autor: "rami", codigos: "si\nno" }, T0, env);
  assert.equal(r.status, 201);
  const { ancla } = await r.json();
  assert.deepEqual(ancla.codigos, ["si", "no"]);

  let datos = await (await get(store, "sala=fam", T0, env)).json();
  assert.equal(datos.anclas.length, 1);
  assert.equal(datos.mensajes.length, 0);
  assert.equal(datos.faro.pulsos.length, 6);
  assert.equal(datos.faro.pulsos[0].epoca, epocaDe(T0));
  assert.equal(datos.faro.pulsos[0].pulso, await pulso(SECRETO, epocaDe(T0)));
  assert.equal(datos.faro.proximo, iso(revelaEn(epocaDe(T0) + 1)));
  assert.equal(datos.faro.detecciones, 0);

  const e = epocaDe(T0) + 1;
  await post(store, { sala: "fam", autor: "futuro", texto: `faro:${e}:${await pulso(SECRETO, e)}` }, T0, env);
  datos = await (await get(store, "sala=fam", T0, env)).json();
  assert.equal(datos.faro.detecciones, 1);
  assert.match(datos.mensajes[0].texto, /pulso oculto/);

  const pasado = await post(store, { sala: "fam", autor: "a", texto: "si", destino: iso(T0 + 5 * 60_000) },
    T0 + 10 * 60_000, env);
  const { mensaje } = await pasado.json();
  assert.equal(mensaje.receptor, ancla.id);
  assert.equal(mensaje.paresEntrelazados, 1);
});

test("sin variable de entorno, el secreto del faro se genera una vez y se guarda", async () => {
  const store = almacen();
  await get(store, "sala=fam");
  const { secreto } = store.datos.get(CLAVE_SECRETO);
  assert.match(secreto, /^[0-9a-f]{64}$/);
  await get(store, "sala=fam", T0 + HORA_MS);
  assert.equal(store.datos.get(CLAVE_SECRETO).secreto, secreto);
});
