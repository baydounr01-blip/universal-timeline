# Universo de Bloques Ramificados

Implementación ejecutable y **batería de falsación** del artículo *«Universo
de Bloques Ramificados: una teoría discreta del tiempo con relatividad
emergente, un canal de información entre ramas y libros mayores indexados
por rama»* (Rami Baydoun Nabhan, agosto de 2026).

El repositorio convierte los doce postulados (P1–P12) en código que puede
**corroborar la coherencia del marco o refutarla**: cada afirmación del
artículo está implementada, testeada y sometida a experimentos cuyo
veredicto se **calcula**, no se declara. La batería corre en CI en cada
push; un solo `REFUTADO` inesperado tumba el pipeline.

```
pip install -e ".[test]"
pytest            # coherencia interna: 63 tests, un modulo por postulado
bbu-verify        # bateria de falsacion E1-E6 con evidencia numerica
```

## Qué puede y qué no puede demostrar este repositorio

Dicho sin rodeos, porque de esto depende leer bien los resultados:

* **Sí puede** demostrar que el marco es *internamente coherente*: que los
  postulados no se contradicen entre sí y que el experimento mental del
  millón de bitcoin se comporta exactamente como el artículo afirma
  (la versión ingenua falla tres veces; la refinada no deja rastro).
* **Sí puede** confrontar las partes del marco que tocan datos publicados:
  el desfase de ~38.5 μs/día de los relojes GPS (Ashby 2003), el factor de
  Lorentz, y las cotas de violación de la invariancia de Lorentz por
  dispersión de fotones (GRB 090510). Aquí el marco **puede fallar contra el
  mundo real**, y en parte falla: ver resultados.
* **No puede** demostrar que el universo *sea* un árbol de bloques, ni que
  el canal interbloque *exista*. El canal es un postulado sin mecanismo
  (sección 9 del artículo). Lo que el repo aporta ahí es el **detector**
  (P12): el procedimiento operativo que haría la afirmación contrastable si
  alguien la usara — y cuya ausencia sostenida de señal es evidencia en
  contra.

Corroborar coherencia no es corroborar verdad física. El pipeline verde
significa «el artículo sobrevive a su propia batería»; no significa «el
artículo es verdad».

## Resultados de la batería

| Exp. | Afirmación (sección 8 del artículo) | Veredicto |
|---|---|---|
| E1 | No hay firma en cadena: ningún análisis del libro mayor de origen detecta el gasto ramificado (P7, P12) | **CORROBORADO** — 1000 gastos del mismo UTXO en 1000 ramas; huella del libro de origen idéntica bit a bit |
| E2 | No hay retorno de variables de rama (P9, P10) | **CORROBORADO** — antes de divergir la predicción es casi perfecta (error ~2·10⁻⁸); después, su error es el de un adivino aleatorio (0.39 vs 0.37) |
| E3 | Hay firma fuera de cadena: cómputo acreditado > cómputo de la rama (P12) | **CORROBORADO** — el detector no dispara con el agente honesto (0.5×) y dispara con el usuario del canal (6×), con pruebas de trabajo reales |
| E4a | La dilatación de Lorentz emerge del presupuesto por tic (P5) | **RESTRINGIDO** — la lectura lineal del postulado queda *refutada* (error 13× a β=0.99); solo sobrevive el reparto euclídeo (error < 3·10⁻⁶) |
| E4b | El modelo reproduce los relojes GPS (P5) | **CORROBORADO** — +45.72 −7.21 = **+38.51 μs/día** frente a ~38.5 publicado |
| E4c | Desviaciones de Lorentz cerca de Planck (P5, S8) | **RESTRINGIDO** — la variante lineal está *excluida* por GRB 090510 (E_QG,1 > 9.3·E_Planck); sobrevive solo la supresión cuadrática |
| E5 | El millón de bitcoin: 3 fallos ingenuos + versión refinada coherente (P2, P6–P10) | **CORROBORADO** — incluye reglas de consenso reales: recompensa 3.125 BTC/bloque, ~440 000 bloques (~8.4 años) para juntar 1M reescribiendo historia, puntos de control que lo rechazan, y la propagación de Merkle de P8 con SHA-256d |
| E6 | Solo el protocolo simétrico produce retorno; alguien paga siempre (P11, S7) | **CORROBORADO** — la historia del protocolo «delega» es la vacía; con el simétrico, las 1000 ramas pagan 10⁶ BTC cada una |

`RESTRINGIDO` es un veredicto legítimo y es información nueva: la afirmación
sobrevive solo en forma acotada. `REFUTADO` nunca lo es: significaría que el
modelo contradice al artículo, y el CI lo trataría como fallo.

## Estructura

```
src/bbu/
├── block.py         P1-P3  arbol de bloques, enlace causal por hash, amplitudes
├── observer.py      P4     decoherencia; sin nocion global de "rama real"
├── relativity.py    P5     presupuesto por tic, densidad de tics, GPS, LIV
├── channel.py       P6     canal interbloque: solo bits clasicos, regla del fork
├── ledger.py        P7-P9  libro mayor por rama, herencia, divergencia caotica
├── merkle.py        P8     raiz de Merkle y encadenado SHA-256d estilo Bitcoin
├── bitcoinrules.py  S5     emision, trabajo acumulado, puntos de control
├── returns.py       P10    invariantes de rama vs variables de rama
├── fixedpoint.py    P11    punto fijo de Deutsch; protocolos simetrico/asimetrico
├── signature.py     P12    detector del exceso de computo (la firma observable)
└── experiments/     E1-E6  la bateria de falsacion (python -m bbu verify)
tests/               un modulo de tests por postulado + bateria completa
docs/
├── ARTICULO.md      el articulo integro
└── MAPA_POSTULADOS.md  cada afirmacion → su modulo, sus tests, su experimento
```

## Cómo refutar el marco desde aquí

El repositorio está construido para perder, si tiene que perder:

1. **Encuentra un rastro en cadena.** Modifica E1 para extraer *cualquier*
   bit del libro mayor de origen que cambie con el gasto ramificado. Si
   existe, P7 cae y el CI lo dirá.
2. **Extrae valor de una variable de rama.** Construye en E2 un predictor
   que, tras el tiempo de divergencia, bata al azar usando solo información
   devuelta por la rama hermana. Si existe, P10 cae.
3. **Dispara el detector sin canal.** Encuentra en E3 una estrategia que
   acredite más cómputo del presupuestado sin recibir trabajo externo. Si
   existe, la «única predicción falsable» (P12) no distingue nada.
4. **Rompe el punto fijo.** Define en E6 un protocolo con retorno positivo
   donde ninguna rama pague. Si existe, P11 y la sección 7 caen.
5. **Contra el mundo real:** si la invariancia de Lorentz resulta exacta a
   todas las escalas, P5 debe reformularse (E4c ya excluye su variante
   lineal); y si aparece evidencia en cadena de «monedas gastadas en otra
   realidad», la teoría entera queda refutada por su propia predicción
   negativa.

## Referencias

Las del artículo (ver `docs/ARTICULO.md`), y para los números usados por los
tests: Ashby (2003) *Living Rev. Relativity* 6:1 para el GPS; Vasileiou et
al. (2013) *Phys. Rev. D* 87:122001 para las cotas LIV de GRB 090510;
Nakamoto (2008) y el calendario de emisión de Bitcoin para la sección 5.

## Licencia

MIT — ver `LICENSE`.
