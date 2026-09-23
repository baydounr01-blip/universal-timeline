// Cronochat — cliente. Sin dependencias; habla con /api/cronochat.

const $ = (id) => document.getElementById(id);
const API = "/api/cronochat";
const estado = { sala: null, rama: "origen", datos: null, desfaseMs: 0 };

const guardar = (k, v) => { try { localStorage.setItem(k, v); } catch { /* sin almacenamiento */ } };
const leer = (k) => { try { return localStorage.getItem(k) || ""; } catch { return ""; } };

// El reloj que cuenta es el del servidor: el cliente solo corrige su desfase.
const ahora = () => Date.now() + estado.desfaseMs;

function formatoFecha(iso) {
  const d = new Date(iso);
  const anio = d.getFullYear();
  const base = d.toLocaleString("es-ES", {
    day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", second: "2-digit",
  });
  return `${base} · ${anio}`;
}

function duracion(ms) {
  const s = Math.max(0, Math.round(ms / 1000));
  const partes = [
    ["a", Math.floor(s / 31557600)], ["d", Math.floor((s % 31557600) / 86400)],
    ["h", Math.floor((s % 86400) / 3600)], ["min", Math.floor((s % 3600) / 60)], ["s", s % 60],
  ].filter(([, v]) => v > 0);
  return partes.length ? partes.slice(0, 3).map(([u, v]) => `${v} ${u}`).join(" ") : "0 s";
}

function pesoBorn(log10) {
  const e = Math.floor(log10);
  const m = 10 ** (log10 - e);
  return `${m.toFixed(1)}·10^${e}`;
}

async function sha256hex(texto) {
  const h = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(texto));
  return [...new Uint8Array(h)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

// ------------------------------------------------------------------ destino
function modo() {
  return document.querySelector('input[name="modo"]:checked').value;
}

function destinoElegido() {
  const m = modo();
  if (m === "ahora") return null;
  if (m === "fecha") {
    const v = $("fecha").value;
    return v ? new Date(v).toISOString() : undefined;
  }
  const delta = Number($("cantidad").value) * Number($("unidad").value);
  if (!Number.isFinite(delta) || delta <= 0) return undefined;
  const t = ahora() + (m === "futuro" ? delta : -delta);
  return new Date(t).toISOString();
}

function actualizarResumen() {
  const m = modo();
  $("relativo").hidden = !(m === "futuro" || m === "pasado");
  $("absoluto").hidden = m !== "fecha";
  const d = destinoElegido();
  const texto = $("texto").value;
  const bits = new TextEncoder().encode(texto).length * 8;
  let r = "";
  if (d === null) r = "Llega ahora.";
  else if (d === undefined) r = "Elige un destino.";
  else {
    const delta = Date.parse(d) - ahora();
    if (Math.abs(delta) <= 1000) r = "Llega ahora.";
    else if (delta > 0) r = `Llegará sellado dentro de ${duracion(delta)} (${formatoFecha(d)}).`;
    else {
      r = `Viaja ${duracion(-delta)} atrás, hasta ${formatoFecha(d)}. Abre una rama nueva`;
      r += bits ? `: ${bits} pares entrelazados, peso de Born ${pesoBorn(-bits * Math.log10(4))}.` : ".";
    }
  }
  $("resumen").textContent = r;
}

// ----------------------------------------------------------------- pintado
function burbuja(m) {
  const li = document.createElement("li");
  const mio = m.autor === $("autor").value.trim();
  li.className = `burbuja ${mio ? "mia" : "ajena"} ${m.direccion}`;
  if (m.salida) li.classList.add("salida");
  if (m.llegada) li.classList.add("llegada");
  if (m.heredado) li.classList.add("heredado");

  const autor = document.createElement("p");
  autor.className = "autor";
  autor.textContent = m.autor;
  li.append(autor);

  const cuerpo = document.createElement("p");
  cuerpo.className = "cuerpo";
  if (m.sellado) {
    cuerpo.textContent = "🔒 Mensaje sellado para el futuro";
    const cuenta = document.createElement("span");
    cuenta.className = "cuenta";
    cuenta.dataset.abre = m.destino;
    cuerpo.append(document.createElement("br"), cuenta);
  } else {
    cuerpo.textContent = m.texto;
  }
  li.append(cuerpo);

  const meta = document.createElement("p");
  meta.className = "meta";
  const partes = [];
  if (m.salida) partes.push(`↩ enviado al pasado → ${m.rama} (llega ${formatoFecha(m.destino)})`);
  else if (m.llegada) partes.push(`⟲ llegó desde ${formatoFecha(m.enviadoEn)} · ${m.paresEntrelazados} pares · Born ${pesoBorn(m.log10PesoBorn)}`);
  else if (m.direccion === "futuro") partes.push(`⇢ escrito ${formatoFecha(m.enviadoEn)}`);
  if (m.heredado) partes.push("heredado del origen");
  if (m.correo) {
    const estados = { enviado: "enviado", error: "no se pudo enviar",
      pendiente: m.sellado ? "saldrá a su hora" : "en cola" };
    partes.push(`✉ ${m.correo.destinatarios} · ${estados[m.correo.estado] ?? m.correo.estado}`);
  }
  partes.push(formatoFecha(m.momento));
  meta.textContent = partes.join(" · ");
  li.append(meta);

  if (m.direccion === "futuro") {
    const c = document.createElement("button");
    c.type = "button";
    c.className = "compromiso";
    c.textContent = m.sellado ? `compromiso ${m.compromiso.slice(0, 12)}…` : "verificar compromiso";
    c.title = m.compromiso;
    if (!m.sellado) {
      c.addEventListener("click", async () => {
        const ok = (await sha256hex(`${m.texto}\u0000${m.nonce}\u0000${Date.parse(m.destino)}`)) === m.compromiso;
        c.textContent = ok ? "✓ estaba escrito antes de abrirse" : "✗ el compromiso no cuadra";
      });
    }
    li.append(c);
  }
  return li;
}

function pintar() {
  const d = estado.datos;
  if (!d) return;
  const lista = $("mensajes");
  const abajo = lista.scrollHeight - lista.scrollTop - lista.clientHeight < 40;
  lista.replaceChildren(...d.mensajes.map(burbuja));
  if (!d.mensajes.length) {
    const vacio = document.createElement("li");
    vacio.className = "vacio";
    vacio.textContent = d.rama === "origen" ? "Aún no hay mensajes en esta línea temporal." : "Rama vacía.";
    lista.append(vacio);
  }
  if (abajo) lista.scrollTop = lista.scrollHeight;

  $("puente").hidden = !d.puenteCorreo;
  $("titulo").textContent = `# ${d.sala}`;
  $("subtitulo").textContent = d.rama === "origen"
    ? "Línea de origen: tu historia"
    : `Rama ${d.rama}: la historia en la que el mensaje llegó`;

  const ramas = $("ramas");
  const items = [{ rama: "origen", texto: "Origen (tu historia)" }].concat(
    d.ramas.map((r) => ({ rama: r.rama, texto: `${r.rama} · bifurca ${formatoFecha(r.bifurcaEn)} · ${r.autor}` })));
  ramas.replaceChildren(...items.map(({ rama, texto }) => {
    const li = document.createElement("li");
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = texto;
    if (rama === estado.rama) b.setAttribute("aria-current", "true");
    b.addEventListener("click", () => {
      estado.rama = rama;
      document.body.classList.remove("lateral-abierta");
      cargar();
    });
    li.append(b);
    return li;
  }));
  tic(false);
}

function tic(recargar = true) {
  $("reloj").textContent = formatoFecha(new Date(ahora()).toISOString());
  let abrir = false;
  for (const span of document.querySelectorAll(".cuenta")) {
    const falta = Date.parse(span.dataset.abre) - ahora();
    span.textContent = falta > 0 ? `se abre en ${duracion(falta)}` : "abriendo…";
    if (falta <= 0) abrir = true;
  }
  if (abrir && recargar) cargar();
}

// ------------------------------------------------------------------- red
async function cargar() {
  if (!estado.sala) return;
  const q = new URLSearchParams({ sala: estado.sala, rama: estado.rama });
  try {
    const res = await fetch(`${API}?${q}`);
    const datos = await res.json();
    if (!res.ok) throw new Error(datos.error || res.statusText);
    estado.desfaseMs = Date.parse(datos.ahora) - Date.now();
    // Solo se repinta si algo cambio: asi no se pierde lo que el usuario
    // esta mirando (una verificacion, la posicion del scroll).
    const huella = JSON.stringify([datos.sala, datos.rama, datos.puenteCorreo, datos.ramas,
      datos.mensajes.map((m) => [m.id, m.sellado, m.correo?.estado])]);
    estado.datos = datos;
    if (huella !== estado.huella) {
      estado.huella = huella;
      pintar();
    }
  } catch (err) {
    $("subtitulo").textContent = `Sin conexión con el canal: ${err.message}`;
  }
}

async function enviar(ev) {
  ev.preventDefault();
  const destino = destinoElegido();
  if (destino === undefined) { actualizarResumen(); return; }
  const cuerpo = { sala: estado.sala, autor: $("autor").value.trim(), texto: $("texto").value, destino };
  if (!$("puente").hidden && $("correos").value.trim()) cuerpo.correos = $("correos").value;
  const res = await fetch(API, {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(cuerpo),
  });
  const datos = await res.json();
  if (!res.ok) { $("resumen").textContent = datos.error; return; }
  $("texto").value = "";
  actualizarResumen();
  await cargar();
  $("mensajes").scrollTop = $("mensajes").scrollHeight;
}

function entrar(ev) {
  ev?.preventDefault();
  const sala = $("sala").value.trim().toLowerCase();
  if (!sala || !$("autor").value.trim()) return;
  guardar("cronochat.autor", $("autor").value.trim());
  guardar("cronochat.sala", sala);
  estado.sala = sala;
  estado.rama = "origen";
  history.replaceState(null, "", `#${sala}`);
  document.body.classList.remove("lateral-abierta");
  cargar();
}

// ----------------------------------------------------------------- arranque
$("autor").value = leer("cronochat.autor");
$("sala").value = decodeURIComponent(location.hash.slice(1)) || leer("cronochat.sala");
$("entrar").addEventListener("submit", entrar);
$("enviar").addEventListener("submit", enviar);
$("menu").addEventListener("click", () => document.body.classList.toggle("lateral-abierta"));
$("texto").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); $("enviar").requestSubmit(); }
});
for (const el of document.querySelectorAll('input[name="modo"], #cantidad, #unidad, #fecha, #texto')) {
  el.addEventListener("input", actualizarResumen);
}
actualizarResumen();
if ($("sala").value && $("autor").value) entrar();
else document.body.classList.add("lateral-abierta");
setInterval(() => tic(), 1000);
setInterval(cargar, 3000);
