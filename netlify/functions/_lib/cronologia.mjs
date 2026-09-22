// Cronochat — el protocolo de telecomunicaciones multitemporales (CTP).
//
// Hipotesis de trabajo (docs/CRONOCHAT.md): el universo es un arbol de
// bloques (P1-P3) y dos qubits entrelazados pueden quedar anclados a
// bloques distintos del tiempo, de modo que un mensaje escrito en t1 se
// lee en t0. Se toma como cierta y se disena encima como se disena
// cualquier red: capas, direcciones, reglas de entrega y un transporte
// intercambiable.
//
// Tres direcciones, tres reglas de entrega:
//
//   presente  |destino - ahora| <= 1 s: chat normal.
//   futuro    se guarda sellado. Hasta que el reloj del receptor llega al
//             destino solo se ve su compromiso sha256 (prueba de que ya
//             estaba escrito) y la cuenta atras. Funciona hoy, de verdad.
//   pasado    viaja por el canal retrocausal. Regla del fork (P6c, punto
//             fijo de Deutsch): no reescribe la historia del emisor; abre
//             una rama hermana en la que el mensaje llego en `destino`.
//             Coste: un par entrelazado por bit y una medida de Born de
//             4^-bits para la rama en la que el bucle se cierra (P-CTC,
//             Lloyd et al. 2011; E7a de la bateria).
//
// El transporte hacia el pasado es una interfaz (`TRANSPORTES`). El unico
// que existe hoy es el simulado: registra la rama y su medida exacta. Si
// algun dia hay un canal fisico, se anade aqui sin tocar nada mas.

export const VENTANA_PRESENTE_MS = 1_000;
export const MAX_TEXTO = 2_000;
export const MAX_AUTOR = 40;
export const MAX_MENSAJES_SALA = 500;
export const ORIGEN = "origen";
export const MAX_CORREOS = 3;

const CORREO_RE = /^[^\s@<>(),;:"]{1,64}@[a-z0-9.-]{1,190}\.[a-z]{2,24}$/i;

const SALA_RE = /^[a-z0-9][a-z0-9-]{0,39}$/;

export class ErrorCronochat extends Error {
  constructor(mensaje, status = 400) {
    super(mensaje);
    this.status = status;
  }
}

export const TRANSPORTES = {
  simulado: {
    nombre: "P-CTC simulado",
    disponible: true,
    descripcion:
      "teleportacion postseleccionada: el mensaje existe en la rama en la que el bucle se cierra",
  },
  fisico: {
    nombre: "CTC fisica",
    disponible: false,
    descripcion: "sin hardware conocido: la capa queda preparada para cuando exista",
  },
};

export function validarSala(sala) {
  const s = String(sala ?? "").trim().toLowerCase();
  if (!SALA_RE.test(s)) {
    throw new ErrorCronochat("la sala son 1-40 letras minusculas, cifras o guiones");
  }
  return s;
}

export function direccion(destinoMs, ahoraMs) {
  const delta = destinoMs - ahoraMs;
  if (Math.abs(delta) <= VENTANA_PRESENTE_MS) return "presente";
  return delta > 0 ? "futuro" : "pasado";
}

export function bitsDe(texto) {
  return new TextEncoder().encode(texto).length * 8;
}

// log10 de la medida de Born de la rama que cierra: 4^-bits.
export function log10PesoBorn(bits) {
  return -bits * Math.log10(4);
}

export async function sha256hex(texto) {
  const datos = new TextEncoder().encode(texto);
  const hash = await crypto.subtle.digest("SHA-256", datos);
  return [...new Uint8Array(hash)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function nuevoId() {
  const bytes = crypto.getRandomValues(new Uint8Array(9));
  return [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");
}

// Puente de email: el remitente puede pedir que el mensaje salga tambien
// por correo en su hora. Para que el sitio no sea un repetidor de spam,
// solo se admiten destinatarios de la lista blanca del operador
// (CRONOCHAT_CORREOS_PERMITIDOS: direcciones o @dominios separados por
// comas). Sin lista, el puente de salida esta cerrado.
export function permitidosDe(texto) {
  return String(texto ?? "").split(",").map((x) => x.trim().toLowerCase()).filter(Boolean);
}

export function validarCorreos(valor, permitidos) {
  const lista = (Array.isArray(valor) ? valor : String(valor ?? "").split(/[,;\s]+/))
    .map((x) => String(x).trim().toLowerCase())
    .filter(Boolean);
  if (!lista.length) return [];
  if (!permitidos.length) {
    throw new ErrorCronochat("el puente de email no esta activado en este sitio", 503);
  }
  if (lista.length > MAX_CORREOS) throw new ErrorCronochat(`como maximo ${MAX_CORREOS} destinatarios`);
  const unicos = [...new Set(lista)];
  for (const c of unicos) {
    if (!CORREO_RE.test(c)) throw new ErrorCronochat(`direccion de email no valida: ${c}`);
    const dominio = c.slice(c.indexOf("@"));
    if (!permitidos.includes(c) && !permitidos.includes(dominio)) {
      throw new ErrorCronochat(`${c} no esta en la lista de destinatarios autorizados`, 403);
    }
  }
  return unicos;
}

// Crea el mensaje a partir de lo que manda el cliente. `ahoraMs` es el
// reloj del servidor: el cliente nunca decide que hora es.
export async function crearMensaje(entrada, ahoraMs, transporte = "simulado", opciones = {}) {
  const sala = validarSala(entrada?.sala);
  const autor = String(entrada?.autor ?? "").trim();
  const texto = String(entrada?.texto ?? "");
  if (!autor || autor.length > MAX_AUTOR) {
    throw new ErrorCronochat(`el nombre tiene entre 1 y ${MAX_AUTOR} caracteres`);
  }
  if (!texto.trim() || texto.length > MAX_TEXTO) {
    throw new ErrorCronochat(`el mensaje tiene entre 1 y ${MAX_TEXTO} caracteres`);
  }
  const destinoMs = entrada?.destino == null ? ahoraMs : Date.parse(entrada.destino);
  if (!Number.isFinite(destinoMs)) throw new ErrorCronochat("fecha de destino no valida");
  const anio = new Date(destinoMs).getUTCFullYear();
  if (anio < 1 || anio > 9999) throw new ErrorCronochat("el destino va del año 1 al 9999");

  const correos = validarCorreos(entrada?.correos, opciones.permitidos ?? []);
  const dir = direccion(destinoMs, ahoraMs);
  const id = nuevoId();
  const nonce = nuevoId();
  const bits = bitsDe(texto);
  const destinoFinal = dir === "presente" ? ahoraMs : destinoMs;
  const mensaje = {
    id,
    sala,
    autor,
    texto,
    direccion: dir,
    enviadoEn: new Date(ahoraMs).toISOString(),
    destino: new Date(destinoFinal).toISOString(),
    compromiso: await sha256hex(`${texto}\u0000${nonce}\u0000${destinoFinal}`),
    nonce,
    rama: ORIGEN,
  };
  if (dir === "pasado") {
    const t = TRANSPORTES[transporte];
    if (!t?.disponible) {
      throw new ErrorCronochat(`transporte hacia el pasado no disponible: ${t?.nombre ?? transporte}`, 503);
    }
    // Regla del fork: la rama hereda la historia de origen hasta `destino`
    // y a partir de ahi contiene este mensaje. El origen no cambia.
    mensaje.rama = `rama-${id.slice(0, 8)}`;
    mensaje.transporte = t.nombre;
    mensaje.paresEntrelazados = bits;
    mensaje.log10PesoBorn = log10PesoBorn(bits);
  }
  if (correos.length) {
    // Al futuro sale a su hora; al presente y al pasado, ya (el buzon vive
    // en la linea de origen: no hay bandeja de entrada en 1995).
    mensaje.correo = { para: correos, estado: "pendiente", intentos: 0 };
  }
  return mensaje;
}

// Lo que ve un lector en `ahoraMs`. Los mensajes al futuro llegan sellados
// hasta su hora: se ve el compromiso, no el texto ni el nonce.
export function vistaDe(mensaje, ahoraMs) {
  // Las direcciones de email nunca salen por la API publica: solo cuantas son
  // y en que estado esta el envio.
  const { nonce, correo, ...publico } = mensaje;
  if (correo) publico.correo = { destinatarios: correo.para.length, estado: correo.estado };
  if (mensaje.direccion === "futuro" && Date.parse(mensaje.destino) > ahoraMs) {
    const { texto, ...sellado } = publico;
    return { ...sellado, sellado: true, faltaMs: Date.parse(mensaje.destino) - ahoraMs };
  }
  // Abierto: el nonce permite a cualquiera recomprobar el compromiso.
  return { ...publico, sellado: false, nonce: mensaje.direccion === "futuro" ? nonce : undefined };
}

// Linea temporal de una rama. `origen` es la historia del emisor: los
// mensajes al pasado aparecen en ella donde se ENVIARON (como salida hacia
// su rama), nunca donde llegaron. Una rama hermana hereda todo el origen
// anterior a su bifurcacion y ademas contiene su mensaje en el destino.
export function lineaTemporal(mensajes, rama, ahoraMs) {
  let visibles;
  if (rama === ORIGEN) {
    visibles = mensajes.map((m) =>
      m.rama === ORIGEN ? { ...m, momento: m.destino } : { ...m, momento: m.enviadoEn, salida: true },
    );
  } else {
    const propio = mensajes.find((m) => m.rama === rama);
    if (!propio) throw new ErrorCronochat("esa rama no existe en esta sala", 404);
    const bifurcacion = Date.parse(propio.destino);
    visibles = mensajes
      .filter((m) => m.rama === ORIGEN && Date.parse(m.destino) < bifurcacion)
      .map((m) => ({ ...m, momento: m.destino, heredado: true }))
      .concat([{ ...propio, momento: propio.destino, llegada: true }]);
  }
  return visibles
    .sort((a, b) => Date.parse(a.momento) - Date.parse(b.momento) || a.id.localeCompare(b.id))
    .map((m) => ({ ...vistaDe(m, ahoraMs), momento: m.momento, salida: !!m.salida,
      heredado: !!m.heredado, llegada: !!m.llegada }));
}

export function ramasDe(mensajes) {
  return mensajes
    .filter((m) => m.rama !== ORIGEN)
    .map((m) => ({ rama: m.rama, bifurcaEn: m.destino, autor: m.autor, log10PesoBorn: m.log10PesoBorn }))
    .sort((a, b) => Date.parse(a.bifurcaEn) - Date.parse(b.bifurcaEn));
}

export async function verificarCompromiso(m) {
  return (await sha256hex(`${m.texto}\u0000${m.nonce}\u0000${Date.parse(m.destino)}`)) === m.compromiso;
}
