// Cartero del puente de email: cada minuto entrega los mensajes cuya hora ha
// llegado (los sellados al futuro) y reintenta los que fallaron.

import { configuracionCorreo, debeSalir, entregar } from "./_lib/correo.mjs";
import { almacen } from "./cronochat.mjs";

export async function repartir(store, config, ahoraMs = Date.now(), fetchFn = fetch) {
  const { blobs } = await store.list();
  const resumen = { revisados: 0, enviados: 0, fallidos: 0 };
  for (const { key } of blobs) {
    const m = await store.get(key, { type: "json" });
    if (!m) continue;
    resumen.revisados += 1;
    if (!debeSalir(m, ahoraMs)) continue;
    const final = await entregar(m, config, ahoraMs, fetchFn);
    await store.setJSON(key, final);
    resumen[final.correo.estado === "enviado" ? "enviados" : "fallidos"] += 1;
  }
  return resumen;
}

export default async () => {
  const resumen = await repartir(await almacen(), configuracionCorreo(process.env));
  console.log("cartero", JSON.stringify(resumen));
  return new Response(JSON.stringify(resumen), { headers: { "content-type": "application/json" } });
};

export const config = { schedule: "* * * * *" };
