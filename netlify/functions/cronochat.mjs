// API de Cronochat (Netlify Functions v2 + Netlify Blobs).
//
//   GET  /api/cronochat?sala=x[&rama=origen|rama-...]  linea temporal + ramas
//   POST /api/cronochat  {sala, autor, texto, destino?}  enviar
//   POST /api/cronochat  {accion: "anclar", sala, autor, codigos?}  receptor
//
// Un blob por mensaje (`<sala>/<id>`): dos envios simultaneos nunca se pisan.

import {
  ErrorCronochat,
  MAX_MENSAJES_SALA,
  ORIGEN,
  TRANSPORTES,
  crearMensaje,
  lineaTemporal,
  ramasDe,
  validarSala,
  vistaDe,
  permitidosDe,
} from "./_lib/cronologia.mjs";
import { configuracionCorreo, debeSalir, entregar } from "./_lib/correo.mjs";
import {
  MAX_ANCLAS_SALA,
  PREFIJO_ANCLAS,
  crearAncla,
  estadoFaro,
  secretoFaro,
} from "./_lib/puente.mjs";

const JSON_HEADERS = { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" };

function responder(cuerpo, status = 200) {
  return new Response(JSON.stringify(cuerpo), { status, headers: JSON_HEADERS });
}

async function mensajesDe(store, sala) {
  const { blobs } = await store.list({ prefix: `${sala}/` });
  const todos = await Promise.all(blobs.map((b) => store.get(b.key, { type: "json" })));
  return todos.filter(Boolean);
}

async function anclasDe(store, sala) {
  const { blobs } = await store.list({ prefix: `${PREFIJO_ANCLAS}${sala}/` });
  const todas = await Promise.all(blobs.map((b) => store.get(b.key, { type: "json" })));
  return todas.filter(Boolean).sort((a, b) => Date.parse(a.creadaEn) - Date.parse(b.creadaEn));
}

// Lo que el protocolo necesita saber del puente para crear un mensaje.
export async function contextoPuente(store, sala, env) {
  return { anclas: await anclasDe(store, sala), secretoFaro: await secretoFaro(store, env) };
}

// Guarda un mensaje nuevo y, si lleva email y ya es su hora, lo entrega.
export async function publicar(store, mensaje, config, ahoraMs, fetchFn = fetch) {
  const { blobs } = await store.list({ prefix: `${mensaje.sala}/` });
  if (blobs.length >= MAX_MENSAJES_SALA) {
    throw new ErrorCronochat("la sala esta llena; abre otra", 409);
  }
  let final = mensaje;
  await store.setJSON(`${mensaje.sala}/${mensaje.id}`, final);
  if (debeSalir(final, ahoraMs)) {
    final = await entregar(final, config, ahoraMs, fetchFn);
    await store.setJSON(`${mensaje.sala}/${mensaje.id}`, final);
  }
  return final;
}

export async function manejar(req, store, ahoraMs = Date.now(), env = process.env, fetchFn = fetch) {
  try {
    const url = new URL(req.url);
    if (req.method === "GET") {
      const sala = validarSala(url.searchParams.get("sala"));
      const rama = url.searchParams.get("rama") || ORIGEN;
      const mensajes = await mensajesDe(store, sala);
      const { anclas, secretoFaro: secreto } = await contextoPuente(store, sala, env);
      const faro = await estadoFaro(secreto, ahoraMs);
      faro.detecciones = mensajes.filter((m) => m.deteccion).length;
      return responder({
        sala,
        rama,
        ahora: new Date(ahoraMs).toISOString(),
        mensajes: lineaTemporal(mensajes, rama, ahoraMs),
        ramas: ramasDe(mensajes),
        transportes: TRANSPORTES,
        anclas,
        faro,
        puenteCorreo: permitidosDe(configuracionCorreo(env).permitidos).length > 0,
      });
    }
    if (req.method === "POST") {
      let entrada;
      try {
        entrada = await req.json();
      } catch {
        throw new ErrorCronochat("el cuerpo debe ser JSON");
      }
      const sala = validarSala(entrada?.sala);
      if (entrada?.accion === "anclar") {
        const { blobs } = await store.list({ prefix: `${PREFIJO_ANCLAS}${sala}/` });
        if (blobs.length >= MAX_ANCLAS_SALA) throw new ErrorCronochat("esta sala ya tiene demasiadas anclas", 409);
        const ancla = crearAncla(sala, entrada, ahoraMs);
        await store.setJSON(`${PREFIJO_ANCLAS}${sala}/${ancla.id}`, ancla);
        return responder({ ancla }, 201);
      }
      const config = configuracionCorreo(env);
      const mensaje = await crearMensaje(entrada, ahoraMs, entrada?.transporte ?? "simulado",
        { permitidos: permitidosDe(config.permitidos), ...(await contextoPuente(store, sala, env)) });
      const final = await publicar(store, mensaje, config, ahoraMs, fetchFn);
      return responder({ mensaje: vistaDe(final, ahoraMs) }, 201);
    }
    return responder({ error: "metodo no permitido" }, 405);
  } catch (err) {
    if (err instanceof ErrorCronochat) return responder({ error: err.message }, err.status);
    console.error(err);
    return responder({ error: "error interno" }, 500);
  }
}

export async function almacen() {
  const { getStore } = await import("@netlify/blobs");
  return getStore({ name: "cronochat", consistency: "strong" });
}

export default async (req) => manejar(req, await almacen());

export const config = { path: "/api/cronochat" };
