// Servidor local sin Netlify: sirve web/ y la API con un almacen en memoria.
//   npm run dev   ->  http://localhost:8888
//
// Puente de email en local: sin RESEND_API_KEY, los emails no salen a
// internet; se imprimen en esta consola ("buzon local") y el cartero pasa
// cada 10 s. Con RESEND_API_KEY se envian de verdad.
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, normalize } from "node:path";
import { manejar } from "../netlify/functions/cronochat.mjs";
import { repartir } from "../netlify/functions/correo-programado.mjs";
import { recibir } from "../netlify/functions/correo-entrante.mjs";
import { configuracionCorreo } from "../netlify/functions/_lib/correo.mjs";

const PUERTO = process.env.PORT ?? 8888;
const env = {
  CRONOCHAT_CORREOS_PERMITIDOS: "@ejemplo.org",
  CRONOCHAT_CLAVE_ENTRANTE: "local",
  URL: `http://localhost:${PUERTO}`,
  ...process.env,
};
const real = Boolean(env.RESEND_API_KEY);
if (!real) Object.assign(env, { RESEND_API_KEY: "buzon-local", CRONOCHAT_REMITENTE: "cronochat@localhost" });

async function buzonLocal(url, init) {
  const c = JSON.parse(init.body);
  console.log(`\n✉  ${new Date().toISOString()}  →  ${c.to.join(", ")}\n   ${c.subject}\n   ${c.text.replace(/\n/g, "\n   ")}`);
  return new Response("{}", { status: 200 });
}
const fetchCorreo = real ? fetch : buzonLocal;

const RAIZ = new URL("../web/", import.meta.url).pathname;
const TIPOS = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css" };
const datos = new Map();
const store = {
  async list({ prefix = "" } = {}) { return { blobs: [...datos.keys()].filter((k) => k.startsWith(prefix)).map((key) => ({ key })) }; },
  async get(key) { return datos.has(key) ? structuredClone(datos.get(key)) : null; },
  async setJSON(key, v) { datos.set(key, structuredClone(v)); },
};

createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${PUERTO}`);
  if (url.pathname === "/api/cronochat" || url.pathname === "/api/correo-entrante") {
    const cuerpo = req.method === "POST" ? await new Promise((ok) => {
      let b = ""; req.on("data", (c) => (b += c)); req.on("end", () => ok(b));
    }) : undefined;
    const peticion = new Request(url, { method: req.method, body: cuerpo });
    const r = url.pathname === "/api/cronochat"
      ? await manejar(peticion, store, Date.now(), env, fetchCorreo)
      : await recibir(peticion, store, env, Date.now(), fetchCorreo);
    res.writeHead(r.status, Object.fromEntries(r.headers));
    return res.end(await r.text());
  }
  const ruta = normalize(join(RAIZ, url.pathname === "/" ? "index.html" : url.pathname));
  if (!ruta.startsWith(RAIZ)) { res.writeHead(403); return res.end(); }
  try {
    const f = await readFile(ruta);
    res.writeHead(200, { "content-type": TIPOS[extname(ruta)] ?? "application/octet-stream" });
    res.end(f);
  } catch { res.writeHead(404); res.end("no encontrado"); }
}).listen(PUERTO, () => {
  console.log(`Cronochat en http://localhost:${PUERTO}`);
  console.log(real ? "Puente de email: Resend (envio real)" : "Puente de email: buzon local (se imprime aqui)");
  console.log(`Destinatarios permitidos: ${env.CRONOCHAT_CORREOS_PERMITIDOS}`);
});
setInterval(() => repartir(store, configuracionCorreo(env), Date.now(), fetchCorreo), 10_000);
