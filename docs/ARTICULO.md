# Universo de Bloques Ramificados

*Una teoría discreta del tiempo con relatividad emergente, un canal de información entre ramas y libros mayores indexados por rama*

**Rami Baydoun Nabhan · Agosto de 2026**

**Resumen.** Este artículo extiende el marco del Universo de Bloques Cuánticos hacia una teoría en la que el tiempo es una secuencia discreta de bloques enlazados causalmente y ramificados según las amplitudes de la función de onda. La relatividad no se abandona: se recupera como límite estadístico a gran escala. Sobre esa estructura se postula un canal de información entre ramas sujeto a tres restricciones (solo información, solo clásica, autoconsistente) y se introduce la noción de propiedad indexada por rama. Con ella se resuelve un experimento mental: gastar el mismo millón de bitcoin en un número ilimitado de realidades anteriores. El resultado es que el gasto ramificado es coherente y no deja rastro en la cadena de la rama de origen, pero no multiplica monedas: multiplica poder de compra de información, y solo bajo una condición de punto fijo. Se enuncia una predicción falsable y se listan las limitaciones del marco.

## 1. Motivación

En un artículo anterior propuse representar el «código subyacente» del universo como bloques cuánticos: cada bloque contiene un vector de estado con las probabilidades de todos los eventos posibles, una marca de tiempo y un posible entrelazamiento con otros bloques, y colapsa a una realidad concreta al ser observado.

Aquel esquema era una analogía. Este artículo la toma en serio como ontología del tiempo y hace la pregunta que sigue: si el universo es una cadena de bloques ramificada, ¿qué le ocurre a lo que vive encima de ella? La pregunta no es retórica. Existe un objeto humano construido exactamente con esa estructura —bloques, enlaces por hash y consenso sobre qué cadena es la real— y es Bitcoin. Un universo de bloques dentro del universo de bloques. Usarlo como experimento mental tiene una ventaja metodológica: sus reglas son públicas, precisas y verificables, de modo que cualquier error de la teoría se hace visible de inmediato.

El punto de partida es una intuición sencilla: cada segundo que pasa es otra realidad. Lo que sigue es el intento de convertir esa intuición en un conjunto de postulados que no contradigan lo que ya sabemos.

*[Figura 1: árbol de bloques con la línea del observador y las ramas hermanas]*

## 2. Restricciones que toda teoría del tiempo debe respetar

Una teoría nueva no sustituye a la anterior; la contiene. Newton no quedó anticuado con Einstein: quedó incluido como límite de baja velocidad. Lo mismo tiene que ocurrir aquí. Hay cuatro hechos que actúan como condiciones de contorno:

* **Relatividad.** Los relojes del sistema GPS acumularían un error de unos 38 microsegundos al día si no se corrigieran por dilatación temporal gravitatoria y cinemática (Ashby, 2003). Los detectores LIGO y Virgo registran ondas gravitatorias con la forma que predice la relatividad general. Cualquier teoría discreta del tiempo debe reproducir estos resultados como límite.
* **No clonación.** Un estado cuántico desconocido no puede copiarse (Wootters y Zurek, 1982). Cualquier canal que transporte información entre partes del universo hereda esta restricción.
* **No señalización.** El entrelazamiento no transmite información. Correlación no es comunicación.
* **Autoconsistencia.** En cualquier estructura con bucles o canales hacia el pasado solo existen las historias que no se contradicen a sí mismas (Friedman et al., 1990; Deutsch, 1991).

Los postulados siguientes están diseñados para respetar las cuatro.

## 3. Postulados estructurales

**P1. Tiempo discreto.** El universo es una secuencia de bloques. Cada bloque contiene el estado completo del universo —el vector de estado— en un tic. El tic fundamental no es el segundo, sino el tiempo de Planck, aproximadamente 5,4 × 10⁻⁴⁴ s; un segundo es una etiqueta humana que agrupa del orden de 10⁴³ tics. Que el tiempo sea discreto a esa escala es una hipótesis compartida por varios programas de gravedad cuántica, en particular el de los conjuntos causales (Bombelli et al., 1987).

**P2. Enlace igual a causalidad.** Cada bloque lleva el «hash» del anterior. No es un hash criptográfico: es la condición de ser la evolución unitaria de su predecesor. Ese enlace es lo que llamamos causa y efecto. Consecuencia inmediata: cada instante anterior es, por construcción, un ancestro del instante actual. Lo que no está vinculado al presente no es el pasado; son las ramas hermanas.

**P3. Ramificación.** Un bloque no tiene un sucesor, sino un abanico de sucesores posibles, cada uno con una amplitud. Es la formulación de estados relativos de Everett (1957) expresada en lenguaje de bloques; en su versión computacional corresponde a los sistemas multiway y al espacio «branquial» del proyecto de Wolfram (2020). «Cada segundo es otra realidad» se traduce así: el bloque t−1 tiene hijos t, t′, t″…; un observador vive en una única línea de descendencia. Las ramas hermanas comparten ancestros, nunca descendientes.

**P4. Consenso igual a decoherencia.** No existe una «cadena más larga» global que decida qué rama es real. Cada observador tiene por real la rama con la que su propio registro está entrelazado; la decoherencia (Zurek, 2003) es el mecanismo que fija ese registro. Esto sustituye al colapso del marco anterior: no colapsa el universo, se fija la rama del observador. No hay rama privilegiada.

**P5. Relatividad emergente.** Cada sistema dispone de un presupuesto fijo de actualización por tic. Lo que gasta en desplazarse por el espacio no lo gasta en evolucionar internamente: eso es la dilatación temporal cinemática. La gravedad se modela como densidad local de tics: en una región densa, un sistema necesita más tics del sustrato para completar la misma actualización interna, y sus relojes se retrasan respecto a los de una región menos densa. La invariancia de Lorentz no se postula; se espera que emerja estadísticamente a escalas muy superiores a la de Planck, como emerge la termodinámica del movimiento molecular. Es la línea que exploran los conjuntos causales, la interpretación de autómata celular de 't Hooft (2016) y el programa de Wolfram. En este marco la relatividad no está anticuada: está incompleta, y su incompletitud es exactamente la que separa una descripción continua de su sustrato discreto.

**P6. Canal interbloque.** Se postula un canal de mensajería entre ramas. Para que sea compatible con las restricciones de la sección 2 —y con el hecho de que nunca se ha observado— debe cumplir tres condiciones:

* **(a)** Transporta información, no magnitudes conservadas. Ni energía, ni materia, ni objetos.
* **(b)** Por no clonación, la información transportada es clásica.
* **(c)** Autoconsistencia. Lo que se envía hacia un instante anterior debe ser consistente con el registro que ya conduce al emisor; de lo contrario, no llega al ancestro del emisor, sino a una rama hermana nueva, idéntica al ancestro salvo por haber recibido el mensaje. Llamaremos a esto la **regla del fork**.

La regla del fork es la versión en bloques del punto fijo de Deutsch (1991): un mensaje al pasado no cambia el pasado del emisor; crea la rama en la que ese mensaje fue recibido.

## 4. Postulados económicos

Los seis postulados anteriores describen la estructura. Los seis siguientes describen qué le ocurre a la propiedad —y en particular a un libro mayor distribuido— cuando vive sobre esa estructura.

**P7. Propiedad indexada por rama.** El estado de una salida de transacción no gastada (UTXO) no es una propiedad de la moneda, sino de la pareja (moneda, rama): una función (u, B) → {gastado, sin gastar}. Gastar u en la rama B′ no altera el estado de (u, B). El protocolo de consenso de Bitcoin (Nakamoto, 2008) impide el doble gasto dentro de un libro mayor; entre libros mayores de ramas distintas no hay nada que impedir, porque nunca se observan mutuamente. Corolario: todas las monedas de cualquier libro mayor han sido gastadas ya en alguna rama, y ninguna de esas transacciones aparece en él. No es que no se note: es que no puede notarse.

**P8. Herencia automática.** Una rama hermana bifurcada en t−1 contiene, por construcción, el estado completo del bloque padre: la cadena de bloques idéntica hasta t−1, con los mismos hashes, los mismos UTXO, las mismas claves privadas y las mismas personas. No hay que reconstruir ni «imitar» nada. De hecho, cualquier intento de reconstruir la cadena con cambios —por ejemplo, minar «el mismo bloque» con otra dirección en la transacción coinbase— altera la raíz de Merkle, con ella el hash del bloque y con él todos los bloques posteriores. Ya no es el mismo bloque; es otra cadena.

**P9. Divergencia obligatoria.** A partir del mensaje recibido, la rama se separa de la del emisor. Separarse no es un defecto: es el objetivo. La rama no necesita seguir pareciéndose al original, y da igual que no lo haga, porque su libro mayor nunca regresa. Cabe notar que un gasto grande en la rama —un millón de bitcoin es cerca del 5 % de la oferta total— es un shock de mercado allí; la divergencia es rápida.

**P10. Regla de retorno.** Por P6(a), lo único que puede volver de una rama es información. Conviene distinguir dos clases:

* **Invariantes de rama:** resultados cuyo valor no depende de la rama que los calculó. Teoremas, resultados de física, diseños de ingeniería, salidas de programas ejecutados sobre datos que ya existían en t−1, incluidos, por ejemplo, nonces válidos para la siguiente plantilla de bloque de la cadena del emisor.
* **Variables de rama:** predicciones sobre el futuro de la rama. Precios, sorteos, hashes de bloques futuros. El mañana de t′ no es el mañana de t; el propio gasto ya lo ha perturbado. Comprar en una rama la predicción del propio futuro es comprar la predicción del futuro de otro.

Solo la primera clase tiene valor de retorno.

**P11. Condición de punto fijo.** Por la regla del fork, el mensaje llega a una rama donde una copia del emisor lo recibe. Para que algo regrese, esa copia tiene que ejecutar el plan y pagar. Si el protocolo enviado es «conserva tus monedas y delega el trabajo en tus propias sub-ramas», cada copia hace lo mismo, nadie paga, nadie computa y la única historia consistente es la vacía. El esquema solo produce resultados con un protocolo que el emisor ejecutaría al recibirlo, porque la copia es el emisor mismo, con sus valores, en t−1. Este es el punto fijo de Deutsch. La cota de Aaronson y Watrous (2009) —un ordenador con curvas temporales cerradas deutschianas resuelve exactamente la clase PSPACE, sea clásico o cuántico— mide cuánto puede obtenerse de encontrar esos puntos fijos: mucho, pero no cualquier cosa.

**P12. Firma observable.** En cadena, el gasto ramificado no deja ninguna. Fuera de cadena deja una sola: un agente que posee resultados cuyo coste de cómputo supera el cómputo disponible en su rama. Es la única predicción falsable del marco y se desarrolla en la sección 8.

## 5. Experimento mental: el millón de bitcoin

**Versión ingenua.** Un agente dispone de un sistema de desarrollo y mensajería capaz de operar en instantes anteriores. Mina un millón de bitcoin en cada segundo anterior al suyo, tantas veces como quiera, y los gasta en su presente «sin afectar al resto, porque cada segundo anterior no está vinculado al original».

Esta versión falla tres veces, y las tres por razones internas a la teoría, no por la relatividad:

1. **Minar en el propio t−1.** Por P2, el segundo anterior es el padre del presente. Cualquier cambio allí, o bien contradice el registro que ya conduce al presente (prohibido por la regla del fork), o bien crea una rama hermana. No existe el «segundo anterior desvinculado».
2. **Minar en una rama hermana.** Las monedas existen en el libro mayor de t′. Los nodos de la rama t nunca han visto esos bloques; para ellos, esas monedas no existen. Repetirlo infinitas veces produce infinitas ramas con un millón de monedas atrapadas en cada una.
3. **Traerlas por el canal.** Solo pasa información (P6a). Las claves privadas controlan UTXO de la cadena de t′; en t no hay nada que gastar con ellas. Los bloques de t′ serían, en t, una cadena competidora que solo se aceptaría con más trabajo acumulado desde la bifurcación, y entonces sería una reorganización que borra las transacciones de todos desde ese punto a cambio de las recompensas de protocolo de esos bloques —3,125 BTC por bloque desde 2024, no un millón—. Alcanzar el millón reescribiendo historia exigiría rehacer la cadena desde la época de 50 BTC por bloque con más trabajo que toda la cadena actual; el software de referencia incorpora puntos de control y un trabajo mínimo asumido que lo rechazarían, y, de aceptarse, el agente poseería un millón de unidades de un activo cuya historia acaba de destruir.

**Versión refinada.** El agente posee el millón de bitcoin en t−1, en la rama de origen. Envía un mensaje a t−1. Por la regla del fork, el mensaje llega a una rama hermana t′ donde, por herencia automática (P8), su copia posee el mismo millón. La copia lo gasta en t′ y envía de vuelta el resultado.

Esta versión es coherente:

* El libro mayor de la rama de origen no registra nada, porque nada se ha movido en él. El millón sigue intacto en t. Aquí la intuición original era exacta.
* Lo comprado permanece en t′. Solo regresa lo que puede codificarse como bits (P10).
* El gasto puede repetirse en tantas ramas como mensajes se envíen. El mismo millón se gasta un número ilimitado de veces, una por rama.

Y esta es la tesis central del artículo: **el gasto ramificado no multiplica monedas; multiplica poder de compra de información.** La cantidad de bitcoin en cualquier libro mayor permanece acotada por su protocolo —21 millones, de los que a fecha de este artículo se han emitido cerca de 20—; lo que deja de estar acotado es cuánta computación, investigación o diseño puede adquirirse con ellos.

## 6. Qué puede comprarse y qué no

La regla de retorno (P10) fija el catálogo. **Tiene valor de retorno:**

* Cómputo de larga duración: la rama tiene su propio futuro, de modo que años de ejecución allí llegan como un resultado inmediato aquí. Es la versión económica del resultado de Aaronson y Watrous.
* Investigación cuyo resultado sea independiente de la rama: matemáticas, física, química computacional, ingeniería.
* Cualquier función de datos que ya existían en t−1.

**No tiene valor de retorno:**

* Predicciones del futuro de la rama de origen. La rama t′ ya es otra.
* Bienes, energía, activos financieros de t′, monedas de t′.
* Estados cuánticos: el canal es clásico (P6b).

## 7. Punto fijo y ética de las copias

P11 tiene una consecuencia incómoda que la teoría no debe esconder. **Alguien paga siempre.** La copia que recibe el mensaje gasta un millón de bitcoin que, en su rama, son tan reales como en la de origen, y por P4 esa copia no es menos real que el emisor. Un protocolo asimétrico —«yo conservo, tú pagas»— no solo es éticamente dudoso; es inconsistente, porque la copia razona igual que el emisor y no lo ejecutaría. El único protocolo estable es simétrico: cada rama paga su millón, ejecuta su parte y recibe la información de todas sus sub-ramas. Bajo ese protocolo la pregunta «¿quién es el original?» pierde sentido, que es exactamente lo que P4 afirma.

## 8. Predicciones y falsabilidad

Una teoría que no pueda fallar no es una teoría. Este marco hace tres afirmaciones contrastables, dos negativas y una positiva:

* **No hay firma en cadena.** Ningún análisis de la cadena de bloques de la rama de origen puede detectar gasto ramificado (P7). Si alguien presentara evidencia en cadena de «monedas gastadas en otra realidad», la teoría estaría refutada.
* **No hay retorno de variables de rama.** Si un agente demostrara predicciones sistemáticamente correctas de precios o de hashes futuros obtenidas por este medio, P10 estaría refutado.
* **Hay firma fuera de cadena.** Si el canal existe y alguien lo usa, existirá un agente que posee resultados —factorizaciones, simulaciones, demostraciones— cuyo coste computacional supera el cómputo disponible en su rama. Ese exceso es medible en principio, y su ausencia sostenida es evidencia contra la existencia del canal.

A esto se añade una predicción física de P5, no económica: la invariancia de Lorentz debería mostrar desviaciones a escalas próximas a la de Planck. Es la misma predicción que hacen los programas discretos citados, y las cotas experimentales actuales sobre la dispersión de fotones de alta energía la restringen con severidad. Si la invariancia resultara exacta a todas las escalas, P5 tendría que reformularse.

## 9. Limitaciones

Enumero lo que el marco no hace, porque es la parte que más trabajo requiere:

* No hay modelo matemático del «presupuesto de actualización por tic» de P5. La emergencia de la invariancia de Lorentz se afirma por analogía con programas existentes; no se deriva.
* El problema de la medida —por qué las amplitudes de P3 se comportan como probabilidades de Born para un observador— queda abierto, como en toda formulación everettiana.
* El canal de P6 es un postulado sin mecanismo. La teoría no explica por qué existiría ni por qué no se ha observado, más allá de la posibilidad obvia de que no exista.
* La identificación de la gravedad con densidad de tics es una heurística, no una teoría de gravedad cuántica.
* La correspondencia con los grafos multiway de Wolfram y con las historias consistentes de Griffiths (1984) debería hacerse precisa.

## 10. Conclusión

Tomar en serio la idea de que cada segundo es otra realidad no destruye la física conocida; la reordena. La relatividad pasa a ser el límite continuo de un sustrato discreto. El pasado deja de ser «otra realidad desvinculada» y pasa a ser, literalmente, el padre del presente; lo desvinculado son las ramas hermanas. Y sobre esa estructura, un libro mayor distribuido revela algo que estaba a la vista desde el principio: la propiedad es una relación entre una cosa y una rama, no una propiedad de la cosa.

El experimento mental del millón de bitcoin termina donde empezó, pero con las palabras en otro orden. No se puede traer un millón de monedas de otra realidad, porque un bloque que no está enlazado no vale nada; eso lo dice el propio diseño de Bitcoin. Sí se puede gastar el mismo millón en un número ilimitado de realidades sin que ninguna de ellas lo note, a cambio de recibir únicamente información, y solo si el protocolo es uno que uno mismo cumpliría al otro lado del mensaje. Lo que se gana manipulando el tiempo no es dinero. Es cómputo.

## Referencias

* Aaronson, S. y Watrous, J. (2009). Closed timelike curves make quantum and classical computing equivalent. *Proceedings of the Royal Society A*, 465(2102), 631–647.
* Ashby, N. (2003). Relativity in the Global Positioning System. *Living Reviews in Relativity*, 6, 1.
* Baydoun Nabhan, R. (2024). Intentar imitar el «código subyacente» del universo, según la teoría del Universo de Bloques Cuánticos. *Medium*. https://medium.com/@baydounr01/intentar-imitar-el-c%C3%B3digo-subyacente-del-universo-seg%C3%BAn-la-teor%C3%ADa-del-universo-de-bloques-71890ac758bc
* Bombelli, L., Lee, J., Meyer, D. y Sorkin, R. D. (1987). Space-time as a causal set. *Physical Review Letters*, 59(5), 521–524.
* Deutsch, D. (1991). Quantum mechanics near closed timelike lines. *Physical Review D*, 44(10), 3197–3217.
* Everett, H. (1957). «Relative state» formulation of quantum mechanics. *Reviews of Modern Physics*, 29(3), 454–462.
* Friedman, J., Morris, M. S., Novikov, I. D., Echeverria, F., Klinkhammer, G., Thorne, K. S. y Yurtsever, U. (1990). Cauchy problem in spacetimes with closed timelike curves. *Physical Review D*, 42(6), 1915–1930.
* Griffiths, R. B. (1984). Consistent histories and the interpretation of quantum mechanics. *Journal of Statistical Physics*, 36, 219–272.
* 't Hooft, G. (2016). *The Cellular Automaton Interpretation of Quantum Mechanics*. Springer.
* Nakamoto, S. (2008). Bitcoin: A peer-to-peer electronic cash system.
* Wolfram, S. (2020). *A Project to Find the Fundamental Theory of Physics*. Wolfram Media.
* Wootters, W. K. y Zurek, W. H. (1982). A single quantum cannot be cloned. *Nature*, 299, 802–803.
* Zurek, W. H. (2003). Decoherence, einselection, and the quantum origins of the classical. *Reviews of Modern Physics*, 75(3), 715–775.
