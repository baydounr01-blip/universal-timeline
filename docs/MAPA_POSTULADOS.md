# Mapa de postulados: articulo → codigo → tests → experimentos

Cada afirmacion del articulo tiene una direccion en el repositorio. Si una
afirmacion no aparece aqui, no esta implementada (y eso es un hueco, no una
virtud).

| Postulado | Afirmacion | Modulo | Tests | Experimento |
|---|---|---|---|---|
| **P1** | El tiempo es una secuencia discreta de bloques; el tic es el tiempo de Planck | `bbu/block.py` | `test_p01_p03_blocks.py::test_p1_*` | — |
| **P2** | Enlace = causalidad; cada instante anterior es un ancestro | `bbu/block.py` (`ancestor_at`, `verify_chain`) | `test_p01_p03_blocks.py::test_p2_*` | E5 (fallo 1) |
| **P3** | Ramificacion con amplitudes; ramas hermanas comparten ancestros, nunca descendientes | `bbu/block.py` (`branch`) | `test_p01_p03_blocks.py::test_p3_*` | — |
| **P4** | Consenso = decoherencia; no hay rama privilegiada | `bbu/observer.py` | `test_p04_observer.py` | — |
| **P5** | Relatividad emergente de un presupuesto por tic; gravedad = densidad de tics | `bbu/relativity.py` | `test_p05_relativity.py` | E4a, E4b, E4c |
| **P6a** | El canal solo transporta informacion | `bbu/channel.py` (`_screen_payload`) | `test_p06_channel.py::test_p6a_*` | E5 (fallo 3) |
| **P6b** | Solo informacion clasica (no clonacion) | `bbu/channel.py` (`QuantumState`) | `test_p06_channel.py::test_p6b_*` | — |
| **P6c** | Regla del fork: el mensaje nunca llega al ancestro del emisor | `bbu/channel.py` (`send_to_past`) | `test_p06_channel.py::test_p6c_*` | E5 (refinada) |
| **P7** | La propiedad es de la pareja (moneda, rama) | `bbu/ledger.py` (`spend`) | `test_p07_p09_ledger.py::test_p7_*` | E1 |
| **P8** | Herencia automatica; "el mismo bloque con otra coinbase" no existe | `bbu/ledger.py` (`inherit`), `bbu/merkle.py` | `test_p07_p09_ledger.py::test_p8_*` | E1, E5 |
| **P9** | Divergencia obligatoria y rapida tras el gasto | `bbu/ledger.py` (`logistic_divergence`) | `test_p07_p09_ledger.py::test_p9_*` | E2 |
| **P10** | Solo los invariantes de rama tienen valor de retorno | `bbu/returns.py` | `test_p10_returns.py` | E2 |
| **P11** | Punto fijo: solo el protocolo simetrico produce retorno | `bbu/fixedpoint.py` | `test_p11_fixedpoint.py` | E6 |
| **P12** | Unica firma: exceso de computo fuera de cadena | `bbu/signature.py` | `test_p12_signature.py` | E3 |
| **S5** | El experimento del millon: 3 fallos ingenuos + version refinada | `bbu/bitcoinrules.py` + E5 | `test_experiments.py` | E5 |
| **S7** | Alguien paga siempre; solo el protocolo simetrico es estable | `bbu/fixedpoint.py` | `test_p11_fixedpoint.py` | E6 |
| **S8** | Tres predicciones (dos negativas, una positiva) + LIV cerca de Planck | experimentos | `test_experiments.py` | E1, E2, E3, E4c |
| **M6←** | Mecanismo de P6 hacia el pasado: CTC postseleccionadas (Lloyd et al. 2011) | `bbu/pctc.py`, `bbu/qsim.py` | `test_m6_pctc.py`, `test_qsim.py` | E7a, E7b, E7c |
| **M6←, S6** | El computo de otra rama llega como resultado inmediato | `bbu/pctc.py` (`search_through_time`) + `bbu/signature.py` | `test_m6_pctc.py::test_p10_*` | E7d |
| **M6→** | Mecanismo de P6 hacia el futuro: capsula RSW; P2 (cada tic necesita el anterior), P5 (tiempo propio) | `bbu/timelock.py` | `test_timelock.py`, `test_cli.py` | E8 |

## Resultados no triviales que produjo la implementacion

1. **La lectura ingenua de P5 esta refutada.** "Lo que gasta en desplazarse
   no lo gasta en evolucionar", leido como resta lineal (tasa interna =
   1 − β), da un factor de dilatacion de ~10.0 a β = 0.9 donde Lorentz exige
   ~2.294. El postulado solo sobrevive si el presupuesto se reparte en norma
   euclidea (tasa interna = √(1 − β²)): entonces el error frente a Lorentz es
   < 3·10⁻⁶ con 2·10⁶ tics. E4a lo documenta como RESTRINGIDO.

2. **El dato del GPS sale bien.** Densidad de tics (gravedad) + presupuesto
   euclideo (velocidad orbital) reproducen +45.7 −7.2 = +38.5 μs/dia
   (Ashby 2003) sin usar las formulas de la relatividad como entrada.

3. **La prediccion LIV de la seccion 8 ya esta parcialmente decidida.** La
   variante con correccion lineal en E/E_Planck esta excluida por GRB 090510
   (E_QG,1 > 9.3·E_Planck); sobrevive la supresion cuadratica. E4c:
   RESTRINGIDO.

4. **El modelo de densidad de tics diverge de la RG en campo fuerte**
   (>10 % a φ = −0.3c²), exactamente donde la seccion 9 lo declara
   heuristica. `test_tick_density_diverges_from_gr_in_strong_field`
   documenta la frontera.

5. **Con mecanismo, el computo del futuro no sale gratis.** En la rama en la
   que el bucle P-CTC se cierra, el pasado recibe un nonce valido y el
   detector P12 dispara. Pero esa rama pesa k/N², y en el conjunto de ramas el
   canal cuesta N veces mas que la fuerza bruta. La seccion 6 sobrevive solo
   condicionada a la rama. E7d: RESTRINGIDO.

6. **P6b no se deduce de la no clonacion.** El mismo circuito transporta
   estados cuanticos con fidelidad 1 sin dejar copia. P6b queda como
   restriccion de diseno del canal, no como consecuencia (E7a).
