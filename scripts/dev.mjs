// Servidor local sin Netlify: sirve web/ y la API con un almacen en memoria.
//   npm run dev   ->  http://localhost:8888
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, normalize } from "node:path";
import { manejar } from "../netlify/functions/cronochat.mjs";

const RAIZ = new URL("../web/", import.meta.url).pathname;
const TIPOS = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css" };
const datos = new Map();
const store = {
  async list({ prefix }) { return { blobs: [...datos.keys()].filter((k) => k.startsWith(prefix)).map((key) => ({ key })) }; },
  async get(key) { return datos.has(key) ? structuredClone(datos.get(key)) : null; },
  async setJSON(key, v) { datos.set(key, structuredClone(v)); },
};

createServer(async (req, res) => {
  const url = new URL(req.url, "http://localhost");
  if (url.pathname === "/api/cronochat") {
    const cuerpo = req.method === "POST" ? await new Promise((ok) => {
      let b = ""; req.on("data", (c) => (b += c)); req.on("end", () => ok(b));
    }) : undefined;
    const r = await manejar(new Request(url, { method: req.method, body: cuerpo }), store);
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
}).listen(process.env.PORT ?? 8888, () => console.log(`Cronochat en http://localhost:${process.env.PORT ?? 8888}`));
