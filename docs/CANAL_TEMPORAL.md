# El canal temporal: P6 con mecanismo

El artículo deja el canal interbloque (P6) como «un postulado sin mecanismo»
(sección 9). Este documento explica el mecanismo que le da el repositorio desde
la versión 0.2.0. Los resultados se calculan en la batería (E7 y E8); aquí no se
declara ninguno.

La regla que se impuso fue usar solo teorías que **nadie haya refutado**, y
decir en cada caso qué parte es experimental y qué parte es interpretación.

| Dirección | Teoría | Estado | Qué funciona hoy |
|---|---|---|---|
| Futuro → pasado | CTC postseleccionadas, o P-CTC (Lloyd et al. 2011) | Circuito probado con fotones (*PRL* 106:040403); la lectura «viaje en el tiempo» es interpretación no refutada | El circuito corre en cualquier procesador cuántico: `python -m bbu qasm …` |
| Pasado → futuro | Cápsula temporal RSW (Rivest, Shamir y Wagner 1996) | La secuencialidad es una conjetura abierta que nadie ha refutado | Sellar y abrir mensajes de verdad: `python -m bbu capsula …` |

## 1. Hacia el pasado: CTC postseleccionadas

### El mecanismo

Que un sistema «vuelva al pasado» equivale, operativamente, a teleportarlo
(Bennett et al. 1993) hacia el extremo antiguo de un par entrelazado y
quedarse solo con la rama en la que la medida de Bell sale |Φ⁺⟩. La idea de
tratar esto como una CTC la formularon Lloyd, Maccone, García-Patrón,
Giovannetti y Shikano (*Phys. Rev. D* 84:025007, 2011) y Svetlichny (2011).
Lloyd et al. la sometieron además a una prueba experimental de consistencia con
fotones (*Phys. Rev. Lett.* 106:040403, 2011).

En el lenguaje de bloques:

```
 t0   se crea el par (A, B) ─────────────┐   B: lo que lee el receptor del pasado
      el receptor lee B                  │
      ...                                │   (el registro de B persiste)
 t1   el emisor escribe M                │
      medida de Bell sobre (A, M) ◄──────┘   4^n ramas (P3)
        · rama |Φ⁺⟩^n  → t0 tenía exactamente M: el bucle se cerró
        · otras ramas  → t0 tenía M cifrado con un Pauli que solo existe en t1
```

El código está en `src/bbu/pctc.py`, sobre un simulador exacto de vector de
estado que no depende de nada (`src/bbu/qsim.py`).

### Lo que la batería calcula

| Exp. | Afirmación | Veredicto y evidencia |
|---|---|---|
| E7a | En la rama que cierra, t0 lee exactamente lo que t1 envió (P6a, P6c) | **CORROBORADO**: fidelidad 1 para los 2ⁿ mensajes; la rama pesa 4⁻ⁿ; `b"hola"` llega intacto en una rama de medida 5,4·10⁻²⁰ |
| E7b | No señalización: sin esa rama (es decir, sin conocer el futuro), el pasado ve lo mismo se mande lo que se mande | **CORROBORADO**: la matriz densidad del receptor es I/2ⁿ antes y después de t1, para cualquier mensaje (diferencia máxima ~10⁻¹⁷). En cada rama de Bell el receptor tenía `m ⊕ s`: una libreta de un solo uso cuya clave se genera en el futuro |
| E7c | Autoconsistencia: solo existen las historias que no se contradicen (sección 2, P6c) | **CORROBORADO**: la paradoja del abuelo tiene medida **exactamente 0**. El bootstrap cierra con medida 1/N pero entrega ruido uniforme (n bits de entropía), así que no crea contenido. Para cualquier f, la medida de cierre es k/N², con k el número de puntos fijos |
| E7d | «Años de cómputo en otra rama llegan aquí como resultado inmediato» (sección 6) | **RESTRINGIDO**: en la rama que cierra, el pasado recibe un nonce de prueba de trabajo válido y el detector P12 dispara (exceso 64×). Pero esa rama pesa k/N², y en el conjunto de todas las ramas el canal cuesta **N veces más** que la fuerza bruta (16 384 ejecuciones frente a 64 intentos). No hay cómputo gratis |

### Qué significa, sin rodeos

1. **El canal funciona.** En la rama en la que el bucle se cierra, el mensaje
   del futuro está en el pasado, íntegro. Eso no es una metáfora: es el
   resultado de un circuito que puede ejecutarse.
2. **No se puede usar para cambiar el pasado.** Quien vive en t0 no puede saber
   en qué rama está hasta que llega t1. Antes de eso, lo que tiene es ruido
   indistinguible (E7b). Es el teorema de no señalización, y el mecanismo lo
   respeta por construcción.
3. **Las paradojas no ocurren.** La historia contradictoria no tiene amplitud
   (E7c). P-CTC la excluye, al estilo de Novikov. Las CTC de Deutsch, que son
   la base de la regla del fork del artículo, la resuelven con una mezcla. Las
   dos son autoconsistentes y solo dan predicciones distintas donde hubiera una
   CTC real, y nadie ha observado ninguna.
4. **Alguien paga siempre (sección 7), y paga en medida de Born.** Al simular
   la postselección hay que descartar las ramas que no cierran, y el precio
   crece como 4ⁿ para un mensaje o N² para una búsqueda. Solo una CTC física
   postseleccionaría gratis, y entonces se podría resolver PP (Aaronson 2005:
   PostBQP = PP). Esa CTC no se ha observado.

### Hallazgo sobre P6b

El artículo deduce P6b («por no clonación, la información es clásica»). Con este
mecanismo, la deducción no se sostiene: el mismo circuito transporta estados
cuánticos con fidelidad 1 y no deja ninguna copia en t1 (E7a,
`no_queda_copia_en_t1`). P6b sigue siendo válido como **restricción de diseño**
del canal (`channel.py` no acepta `QuantumState`), pero la no clonación no la
impone.

### Correrlo en hardware real

```
python -m bbu qasm mensaje 101     # 3 bits de t1 a t0 (9 qubits)
python -m bbu qasm abuelo          # la paradoja del abuelo (3 qubits)
python -m bbu qasm bootstrap 2     # el bucle sin autor (6 qubits)
```

La salida es OpenQASM 2.0 estándar, que acepta cualquier procesador cuántico
con esa entrada (por ejemplo, IBM Quantum Composer). La postselección consiste
en quedarse solo con los disparos que indica el último comentario, igual que en
el experimento con fotones. Qué se espera ver:

* **mensaje**: en los disparos conservados, B reproduce el mensaje. La fracción
  conservada ronda 4⁻ⁿ.
* **abuelo**: la fracción conservada tiende a 0. Lo que quede es ruido del
  equipo, y esa es la señal: la historia paradójica no se produce.
* **bootstrap**: la fracción conservada ronda 1/2ⁿ y B sale uniforme.

Un resultado de hardware que se aparte de esto más allá del ruido del equipo no
refutaría a Lloyd et al. (su experimento ya se hizo), pero sí a esta
implementación. Las primeras candidatas serían la convención de qubits o la
exportación.

## 2. Hacia el futuro: cápsulas temporales

Un fichero guardado ya viaja al futuro, pero no ofrece ninguna garantía sobre
cuándo se lee. La cápsula de Rivest, Shamir y Wagner (1996) sí la ofrece: el
mensaje **no puede leerse antes de tiempo**, tampoco por quien lo escribió.

* El emisor elige n = p·q y deriva la clave de x_T = a^(2^T) mod n. Como
  conoce φ(n), calcula x_T con unas mil multiplicaciones y después desecha p y
  q.
* Sin p y q, el mejor método conocido es elevar al cuadrado T veces, una tras
  otra. Cada cuadrado necesita el anterior (P2: enlace = causalidad) y el
  paralelismo no acorta la cadena.

```
python -m bbu capsula sellar "mensaje para mi yo de dentro de una hora" --segundos 3600
python -m bbu capsula abrir capsula.json
```

**E8: CORROBORADO.** Con T cuadrados, el mensaje se lee. Con T−1, T/2 o 0, la
etiqueta HMAC lo rechaza. La cápsula en JSON no lleva la trampilla, y al emisor le
basta una cota de 1 054 multiplicaciones para lo que al receptor le cuesta
20 000 cuadrados.

Dos advertencias honestas:

* Que no haya atajo sin factorizar n es una **conjetura**. No está refutada:
  el acertijo LCS35 de Rivest (1999, diseñado para 35 años) se abrió en 2019
  tras unos 3,5 años de cuadrados secuenciales. Se abrió antes por ser más
  rápidas las máquinas, no por un atajo.
* La cápsula mide **tics de cómputo del que la abre, no segundos**. Una máquina
  más rápida la abre antes. Es P5 hecho tangible: el tiempo que cuenta es el
  tiempo propio.

El cuerpo se cifra con un flujo SHA-256 en modo contador más una etiqueta
HMAC-SHA256. No tiene dependencias, basta para el propósito y se declara como
lo que es.

## 3. El sistema completo, en una línea

**Hacia delante, el sistema se comunica hoy, con garantías. Hacia atrás, se
comunica en la rama en la que el bucle se cierra, y no puede usar eso para
cambiar nada ni para obtener cómputo gratis.** Esto es lo más lejos que llega
la física no refutada, y la batería lo comprueba en cada push.

## Referencias

* Aaronson, S. (2005). Quantum computing, postselection, and probabilistic polynomial-time. *Proc. R. Soc. A*, 461, 3473–3482.
* Bennett, C. H., Brassard, G., Crépeau, C., Jozsa, R., Peres, A. y Wootters, W. K. (1993). Teleporting an unknown quantum state via dual classical and Einstein-Podolsky-Rosen channels. *Phys. Rev. Lett.*, 70, 1895.
* Deutsch, D. (1991). Quantum mechanics near closed timelike lines. *Phys. Rev. D*, 44, 3197.
* Friedman, J. et al. (1990). Cauchy problem in spacetimes with closed timelike curves. *Phys. Rev. D*, 42, 1915.
* Lloyd, S., Maccone, L., Garcia-Patron, R., Giovannetti, V. y Shikano, Y. (2011). Quantum mechanics of time travel through post-selected teleportation. *Phys. Rev. D*, 84, 025007.
* Lloyd, S., Maccone, L., Garcia-Patron, R., Giovannetti, V., Shikano, Y., Pirandola, S., Rozema, L. A., Darabi, A., Soudagar, Y., Shalm, L. K. y Steinberg, A. M. (2011). Closed timelike curves via postselection: theory and experimental test of consistency. *Phys. Rev. Lett.*, 106, 040403.
* Rivest, R. L., Shamir, A. y Wagner, D. A. (1996). Time-lock puzzles and timed-release crypto. MIT/LCS/TR-684.
* Svetlichny, G. (2011). Time travel: Deutsch vs. teleportation. *Int. J. Theor. Phys.*, 50, 3903–3914.
