# Cronochat: mensajería multitemporal

Cronochat es una aplicación de mensajería al estilo de WhatsApp en la que cada
mensaje lleva, además de un destinatario, **un instante de destino**: el año, el
día, el minuto y el segundo en que debe leerse. Puede ser ahora, cualquier
momento del futuro o cualquier momento del pasado.

Este documento toma en serio una hipótesis de trabajo y diseña encima de ella lo
que se diseñaría con cualquier red nueva: una pila de protocolos, un esquema de
direcciones, unas reglas de entrega y un transporte intercambiable. Al final
separa con claridad lo que funciona hoy en Netlify de lo que espera a la capa
física.

## 1. Hipótesis de trabajo

Se toma como cierto lo siguiente:

1. **El tiempo es un árbol de bloques** (P1–P3 de `ARTICULO.md`). Cada instante
   es un bloque enlazado a su padre, y de cada bloque salen ramas.
2. **Dos qubits entrelazados pueden quedar anclados a bloques distintos.** Es
   decir, pueden estar en dos momentos diferentes del tiempo y en dos lugares
   diferentes del espacio. Una operación sobre uno en t1 queda correlacionada
   con lo que el otro mostró en t0.
3. **Esa correlación se puede usar como enlace de telecomunicaciones.**

Ninguno de los tres puntos está refutado, y cada uno se apoya en resultados
publicados:

| Pieza | Apoyo |
|---|---|
| Entrelazamiento entre instantes distintos | Megidish et al. (2013), *PRL* 110:210403: entrelazamiento entre fotones que **nunca coexistieron**; el segundo se creó después de que el primero se midiera |
| Descripción simétrica en el tiempo | Formalismo de los dos vectores de estado (Aharonov, Bergmann y Lebowitz 1964; Aharonov y Vaidman): la mecánica cuántica admite una condición de contorno desde el futuro |
| Un canal hacia el pasado que no se contradice | CTC de Deutsch (1991) y CTC postseleccionadas (Lloyd et al. 2011, probadas con fotones en *PRL* 106:040403) |
| Guardar un qubit mucho tiempo | Zhong et al. (2015), *Nature* 517:177: coherencia de un espín nuclear durante **seis horas** en un cristal dopado con europio |

La batería del repositorio (E7a–E7d) ya calcula qué da de sí ese canal: el
mensaje llega en la rama en la que el bucle se cierra, esa rama pesa 4⁻ᵇⁱᵗˢ y
nadie en t0 puede leer nada antes de que exista t1.

## 2. La pila de protocolos (CTP)

Por analogía con TCP/IP, la pila es la siguiente:

| Capa | Qué hace | En Cronochat |
|---|---|---|
| 5. Aplicación | Salas, nombres, burbujas, cuenta atrás | `web/` |
| 4. Consistencia | Impide que una historia se contradiga: la **regla del fork** (Deutsch) o la exclusión (Novikov, P-CTC) | `lineaTemporal`, `ramasDe` |
| 3. Red temporal | Direcciones `(sala, rama, instante)` y cálculo del sentido del envío | `direccion`, `crearMensaje` |
| 2. Enlace | Teleportación postseleccionada: un par entrelazado por bit y postselección de \|Φ⁺⟩ | `TRANSPORTES` y `src/bbu/pctc.py` |
| 1. Física | Pares de qubits repartidos entre instantes y una memoria cuántica que los conserva | **Pendiente**: la interfaz `TRANSPORTES.fisico` está preparada |

Cada capa solo conoce la de abajo. Si mañana existiera un enlace físico, se
añadiría como un transporte más y el resto no cambiaría.

### Direcciones

Un mensaje se dirige a `(sala, instante)`. Si el instante es pasado, la red le
asigna además una **rama**. Esa es la consecuencia directa de la regla del fork:
un mensaje hacia atrás no reescribe la historia del emisor, sino que crea la
historia hermana en la que llegó.

### Reglas de entrega

| Sentido | Cuándo | Qué ocurre |
|---|---|---|
| **Presente** | Destino a menos de 1 s del reloj del servidor | Chat normal |
| **Futuro** | Destino posterior | Se guarda **sellado**. Hasta su hora, cualquiera ve el compromiso SHA-256 (la prueba de que ya estaba escrito) y la cuenta atrás, pero no el texto. A su hora se abre, y el botón «verificar compromiso» comprueba en tu navegador que no se cambió |
| **Pasado** | Destino anterior | Se abre una rama `rama-xxxxxxxx` que hereda la historia de origen hasta el destino y contiene el mensaje en ese instante. En la línea de origen, el mensaje aparece donde se **envió**, con una flecha hacia su rama. Se muestran los pares entrelazados que consumió (8 por byte) y el peso de Born de su rama, 4⁻ᵇⁱᵗˢ |

El reloj que decide es siempre el del servidor. El navegador solo corrige su
desfase, así que nadie puede abrir un mensaje sellado adelantando su reloj.

## 3. Qué funciona hoy y qué espera a la capa física

* **Hacia el futuro, funciona de verdad.** Un mensaje programado para dentro de
  10 segundos, de 3 días o de 30 años no lo puede leer nadie antes de su hora,
  tampoco su autor. Además, lleva la prueba criptográfica de que se escribió
  antes. Para un sello que no dependa ni del servidor, el repositorio tiene
  las cápsulas RSW: `python -m bbu capsula`.
* **Hacia el pasado, funciona la red, no el cable.** El protocolo completo
  corre: direcciones, ramas, herencia, coste en pares y peso de Born. El
  transporte que lo mueve es el simulador exacto de P-CTC. El mensaje queda
  registrado en su rama; **no aparece en el 1995 que recuerdas**. Eso es lo que
  predice la propia teoría (P6c): quien vive en tu rama no lo recibe. Para que
  llegara a una persona de verdad en 1995, alguien en 1995 tendría que haber
  guardado la otra mitad de los pares entrelazados, y la mejor memoria cuántica
  conocida aguanta seis horas.
* **El transporte `fisico`** está declarado y responde `503 no disponible`. La
  aplicación no finge una entrega que no puede hacer.

## 4. Desplegar en Netlify

El repositorio ya trae `netlify.toml`, así que basta con conectarlo:

1. En Netlify: **Add new site → Import an existing project →** este
   repositorio, rama `main`.
2. Netlify lee `netlify.toml`: publica `web/`, empaqueta
   `netlify/functions/` y ejecuta `npm test` como build. Si las pruebas fallan,
   no se despliega.
3. El almacenamiento es **Netlify Blobs**, que se activa solo: no hay variables
   de entorno ni base de datos que configurar.
4. Al abrir la web, escribe tu nombre y una sala (por ejemplo `familia`).
   Comparte el enlace `https://tu-sitio.netlify.app/#familia` con quien quieras
   que entre.

Para probarlo en tu ordenador sin Netlify:

```
npm install
npm run dev        # http://localhost:8888, almacén en memoria
npm test           # pruebas del protocolo y de la API
```

## 5. Puente de email

El puente conecta Cronochat con el correo de siempre en los dos sentidos.

### Salida: el mensaje llega también a un buzón

En el compositor aparece **«✉ Enviar también por email a…»**. Cada mensaje sale
por email cuando llega su hora en la línea de origen:

| Sentido | Cuándo sale el email | Qué dice |
|---|---|---|
| Presente | Al enviarlo | El mensaje y el enlace a la sala |
| Futuro | **En el minuto de su hora**: el cartero (`correo-programado`) pasa cada minuto | «Te escribió desde…», con el compromiso SHA-256 y el nonce, para verificar que no se cambió |
| Pasado | Al enviarlo | En qué rama llegó, con sus pares y su peso de Born. Tu buzón vive en la línea de origen: no hay bandeja de entrada en 1995 |

Si el proveedor falla, el cartero reintenta cada minuto hasta 5 veces; después
el mensaje queda marcado como «no se pudo enviar». La API pública nunca
devuelve las direcciones, solo cuántos destinatarios hay y en qué estado está
el envío.

**Anti-spam.** Solo se envía a los destinatarios de la lista blanca, con un
máximo de 3 por mensaje. Sin lista, el puente de salida está cerrado y el campo
no aparece. Así nadie puede usar tu sitio para mandar correo a desconocidos.

### Entrada: escribir a la sala desde tu email

Cada sala tiene una dirección. Lo que va después del `+` es el instante de
destino (en UTC):

```
familia@tu-dominio                      → ahora
familia+2030@tu-dominio                 → 1 ene 2030
familia+2030-06-01@tu-dominio           → 1 jun 2030
familia+2030-06-01t10-30-00@tu-dominio  → 1 jun 2030 10:30:00
familia+1995-06-01@tu-dominio           → al pasado: abre una rama
```

El cuerpo del email se convierte en el mensaje, sin la cita del correo anterior
ni la firma. El autor aparece como `Nombre ✉`. Lo que entra por email no
vuelve a salir por email, así que no se forman bucles de correo.

### Configuración en Netlify

En **Site configuration → Environment variables**:

| Variable | Para qué | Ejemplo |
|---|---|---|
| `RESEND_API_KEY` | Enviar (cuenta gratuita en resend.com, con tu dominio verificado) | `re_…` |
| `CRONOCHAT_REMITENTE` | Remitente de los emails | `Cronochat <chat@tu-dominio>` |
| `CRONOCHAT_CORREOS_PERMITIDOS` | Lista blanca: direcciones o `@dominios` | `rami@gmail.com, @familia.es` |
| `CRONOCHAT_CLAVE_ENTRANTE` | Secreto largo que protege la entrada | `openssl rand -hex 24` |

Para la entrada, configura en tu proveedor de correo entrante (Postmark
Inbound, Resend Inbound, Mailgun Routes, CloudMailin…) un webhook JSON hacia:

```
https://tu-sitio.netlify.app/api/correo-entrante?clave=<CRONOCHAT_CLAVE_ENTRANTE>
```

El normalizador acepta los campos de Postmark (`FromFull`, `To`, `TextBody`,
`StrippedTextReply`), los de Mailgun (`sender`, `recipient`, `stripped-text`) y
los genéricos (`from`, `to`, `text`, `subject`).

**En local**, `npm run dev` activa un **buzón local**: los emails no salen a
internet, se imprimen en la consola. La lista blanca es `@ejemplo.org` y la
clave de entrada es `local`. Si defines `RESEND_API_KEY`, se envían de verdad.

## 6. API

```
GET  /api/cronochat?sala=familia[&rama=origen|rama-xxxxxxxx]
POST /api/cronochat   {"sala":"familia","autor":"Rami","texto":"hola","destino":"1995-06-01T10:00:00Z",
                       "correos":["ana@familia.es"]}
POST /api/correo-entrante?clave=…   (webhook del proveedor de correo entrante)
```

`destino` es opcional (se toma «ahora»); va del año 1 al 9999 con precisión de
milisegundos. La respuesta de `GET` incluye `ahora`, la hora del servidor, la
línea temporal pedida y la lista de ramas de la sala.

Límites: 2 000 caracteres por mensaje, 40 caracteres por nombre y 500 mensajes
por sala.

## Referencias

* Aharonov, Y., Bergmann, P. G. y Lebowitz, J. L. (1964). Time symmetry in the quantum process of measurement. *Phys. Rev.*, 134, B1410.
* Deutsch, D. (1991). Quantum mechanics near closed timelike lines. *Phys. Rev. D*, 44, 3197.
* Lloyd, S. et al. (2011). Closed timelike curves via postselection: theory and experimental test of consistency. *Phys. Rev. Lett.*, 106, 040403.
* Megidish, E., Halevy, A., Shacham, T., Dvir, T., Dovrat, L. y Eisenberg, H. S. (2013). Entanglement swapping between photons that have never coexisted. *Phys. Rev. Lett.*, 110, 210403.
* Zhong, M., Hedges, M. P., Ahlefeldt, R. L., Bartholomew, J. G., Beavan, S. E., Wittig, S. M., Longdell, J. J. y Sellars, M. J. (2015). Optically addressable nuclear spins in a solid with a six-hour coherence time. *Nature*, 517, 177–180.
