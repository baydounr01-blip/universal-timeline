# Auditoría de seguridad — 29 de septiembre de 2026

Revisión de código de Cronochat (funciones de Netlify, puente de email, web)
y de la cápsula temporal de `src/bbu/timelock.py` tras las últimas
integraciones. Forma parte de la auditoría conjunta de los tres repositorios
del proyecto; el informe completo, con el método y sus límites, está en
RAMI-Ledger (`docs/AUDITORIA-2026-09-29.md`). Aquí, lo de este repositorio.

Lo que se revisó y quedó correcto sin cambios: la lista blanca de
destinatarios del puente de salida (el sitio no es un repetidor de correo),
que las direcciones de email nunca salen por la API (`vistaDe`), el
compromiso SHA‑256 con nonce de 72 bits oculto hasta la apertura, el faro
(HMAC por época, pulso oculto hasta revelarse), la web (`textContent` en todo
lo que se pinta) y su CSP con `frame-ancestors 'none'`, y la cápsula RSW
(módulo de 2048 bits, Miller–Rabin de 40 rondas sobre `secrets.SystemRandom`,
flujo SHA‑256 en contador con etiqueta HMAC comparada en tiempo constante,
trampilla destruida al sellar).

| # | Sev. | Dónde | Problema | Estado |
|---|---|---|---|---|
| U1 | Media | `netlify/functions/cronochat.mjs` (`POST`) | Sin límite de ritmo ni de salas: cualquiera crea salas sin fin, cada una con hasta 500 mensajes de 2 KB y 20 anclas de 256 códigos × 200 caracteres. Coste del almacén sin tope. | Pendiente: límite persistente por IP y tope global de salas |
| U2 | Media | `netlify/functions/correo-programado.mjs` | Cada minuto lista todos los blobs y lee cada mensaje; con N mensajes son N lecturas por minuto para siempre, y N lo fija quien llene salas (U1). | Pendiente: índice de mensajes con correo pendiente |
| U3 | Baja | `netlify/functions/correo-entrante.mjs` | La clave del webhook viajaba solo en la URL (`?clave=`): queda en los registros del proveedor de correo, de Netlify y de cualquier proxy. | Corregido: se acepta `Authorization: Bearer <clave>` (recomendado) y la URL sigue valiendo para proveedores sin cabeceras |
| U4 | Baja | `_lib/cronologia.mjs` (`vistaDe`) | Los mensajes sellados al futuro se guardan en claro; el sello lo aplica el servidor al servirlos. Quien administre el sitio los lee antes de hora. | Documentado en `docs/CRONOCHAT.md` §2; cifrar en reposo con la cápsula RSW es la siguiente entrega |
| U5 | Info | `correo-entrante.mjs` | Cualquiera que envíe un email a `sala@dominio` publica en esa sala con el nombre del remitente, que se falsifica. Coherente con salas públicas sin cuenta. | Diseño |
| U6 | Info | `web/app.js`, `netlify.toml` | Sin hallazgos. | Correcto |

Las pruebas (`npm test`, 27; `pytest`) siguen cubriendo el cambio de U3: el
webhook con `?clave=` se prueba igual que antes.
