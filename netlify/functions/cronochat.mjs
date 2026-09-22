// API de Cronochat (Netlify Functions v2 + Netlify Blobs).
//
//   GET  /api/cronochat?sala=x[&rama=origen|rama-...]  linea temporal + ramas
//   POST /api/cronochat  {sala, autor, texto, destino?}  enviar
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
} from "./_lib/cronologia.mjs";

const JSON_HEADERS = { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" };

function responder(cuerpo, status = 200) {
  return new Response(JSON.stringify(cuerpo), { status, headers: JSON_HEADERS });
}

async function mensajesDe(store, sala) {
  const { blobs } = await store.list({ prefix: `${sala}/` });
  const todos = await Promise.all(blobs.map((b) => store.get(b.key, { type: "json" })));
  return todos.filter(Boolean);
}

export async function manejar(req, store, ahoraMs = Date.now()) {
  try {
    const url = new URL(req.url);
    if (req.method === "GET") {
      const sala = validarSala(url.searchParams.get("sala"));
      const rama = url.searchParams.get("rama") || ORIGEN;
      const mensajes = await mensajesDe(store, sala);
      return responder({
        sala,
        rama,
        ahora: new Date(ahoraMs).toISOString(),
        mensajes: lineaTemporal(mensajes, rama, ahoraMs),
        ramas: ramasDe(mensajes),
        transportes: TRANSPORTES,
      });
    }
    if (req.method === "POST") {
      let entrada;
      try {
        entrada = await req.json();
      } catch {
        throw new ErrorCronochat("el cuerpo debe ser JSON");
      }
      const mensaje = await crearMensaje(entrada, ahoraMs, entrada?.transporte ?? "simulado");
      const { blobs } = await store.list({ prefix: `${mensaje.sala}/` });
      if (blobs.length >= MAX_MENSAJES_SALA) {
        throw new ErrorCronochat("la sala esta llena; abre otra", 409);
      }
      await store.setJSON(`${mensaje.sala}/${mensaje.id}`, mensaje);
      return responder({ mensaje: vistaDe(mensaje, ahoraMs) }, 201);
    }
    return responder({ error: "metodo no permitido" }, 405);
  } catch (err) {
    if (err instanceof ErrorCronochat) return responder({ error: err.message }, err.status);
    console.error(err);
    return responder({ error: "error interno" }, 500);
  }
}

export default async (req) => {
  const { getStore } = await import("@netlify/blobs");
  return manejar(req, getStore({ name: "cronochat", consistency: "strong" }));
};

export const config = { path: "/api/cronochat" };
