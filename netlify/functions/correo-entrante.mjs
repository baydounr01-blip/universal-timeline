// Entrada del puente de email: el proveedor de correo entrante reenvia aqui
// cada email como JSON. La direccion de destino decide sala e instante
// (ver _lib/correo.mjs). Protegido con CRONOCHAT_CLAVE_ENTRANTE, que va en
// la URL del webhook: /api/correo-entrante?clave=...

import { timingSafeEqual } from "node:crypto";

import { ErrorCronochat, crearMensaje, permitidosDe, validarSala, vistaDe } from "./_lib/cronologia.mjs";
import { configuracionCorreo, entradaDeCorreo } from "./_lib/correo.mjs";
import { almacen, contextoPuente, publicar } from "./cronochat.mjs";

const json = (cuerpo, status = 200) => new Response(JSON.stringify(cuerpo),
  { status, headers: { "content-type": "application/json; charset=utf-8" } });

function claveValida(dada, esperada) {
  if (!esperada || !dada) return false;
  const a = Buffer.from(dada);
  const b = Buffer.from(esperada);
  return a.length === b.length && timingSafeEqual(a, b);
}

export async function recibir(req, store, env = process.env, ahoraMs = Date.now(), fetchFn = fetch) {
  const config = configuracionCorreo(env);
  if (!config.claveEntrante) return json({ error: "puente de entrada sin configurar" }, 503);
  if (req.method !== "POST") return json({ error: "metodo no permitido" }, 405);
  if (!claveValida(new URL(req.url).searchParams.get("clave"), config.claveEntrante)) {
    return json({ error: "clave no valida" }, 401);
  }
  try {
    let cuerpo;
    try { cuerpo = await req.json(); } catch { throw new ErrorCronochat("el cuerpo debe ser JSON"); }
    const entrada = entradaDeCorreo(cuerpo);
    if (entrada.error) throw new ErrorCronochat(entrada.error);
    // Lo que entra por email no reenvia por email: sin bucles de correo.
    const puente = await contextoPuente(store, validarSala(entrada.sala), env);
    const mensaje = await crearMensaje(entrada, ahoraMs, "simulado",
      { permitidos: permitidosDe(config.permitidos), ...puente });
    const final = await publicar(store, mensaje, config, ahoraMs, fetchFn);
    return json({ mensaje: vistaDe(final, ahoraMs) }, 201);
  } catch (err) {
    if (err instanceof ErrorCronochat) return json({ error: err.message }, err.status);
    console.error(err);
    return json({ error: "error interno" }, 500);
  }
}

export default async (req) => recibir(req, await almacen());

export const config = { path: "/api/correo-entrante" };
