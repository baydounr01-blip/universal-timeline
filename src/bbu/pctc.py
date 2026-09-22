"""Mecanismo del canal P6: curvas temporales cerradas por postseleccion.

El articulo deja P6 como "un postulado sin mecanismo" (seccion 9). Este
modulo le da uno tomado de fisica que nadie ha refutado:

  * Teoria: CTC postseleccionadas o P-CTC (Lloyd, Maccone, Garcia-Patron,
    Giovannetti, Shikano 2011, Phys. Rev. D 84:025007; Svetlichny 2011).
    Un sistema que "vuelve al pasado" equivale a teletransportarlo (Bennett
    et al. 1993) hacia el extremo antiguo de un par entrelazado y quedarse
    solo con la rama en la que la medida de Bell da |Phi+>.
  * Experimento: Lloyd et al. (2011), Phys. Rev. Lett. 106:040403,
    simularon ese circuito con fotones e ilustraron como queda resuelta la
    paradoja del abuelo. No hay ningun resultado que lo contradiga: es
    mecanica cuantica ordinaria con una postseleccion.

Traduccion al marco de bloques:

  t0  se crea el par (A, B). B es el registro que lee el receptor del
      pasado. Leerlo entonces o despues da igual: nada vuelve a tocarlo.
  t1  el emisor prepara su mensaje en M y mide (A, M) en la base de Bell.
      Hay 4^n ramas (P3). En la unica en la que sale |Phi+>^n el receptor
      tenia en t0 exactamente lo que el emisor mando en t1: el bucle se
      cerro. En las demas el mensaje llego cifrado con un Pauli que solo se
      conoce en t1 -- para bits clasicos, una libreta de un solo uso cuya
      clave se genera en el futuro.

Por eso el canal funciona y no permite cambiar el pasado: la rama en la que
el mensaje llego solo se identifica despues de enviarlo (no senalizacion,
seccion 2), y las historias contradictorias tienen amplitud cero
(autoconsistencia, P6c). Lo que el canal cuesta se paga en medida de Born.

Que la lectura "el sistema viajo al pasado" sea la correcta es la parte
interpretativa de la teoria, no refutada pero tampoco forzada por los datos;
lo que si es experimental es el circuito, y ese es el que se simula aqui y
se exporta a OpenQASM para correrlo en hardware real.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

from .qsim import State, reg_value


@dataclass(frozen=True)
class Loop:
    """Registros de un bucle de n qubits: A (entra en la CTC en t1),
    B (sale de ella en t0: lo que lee el receptor), M (el emisor en t1)."""

    n: int

    @property
    def a(self) -> list[int]:
        return list(range(self.n))

    @property
    def b(self) -> list[int]:
        return list(range(self.n, 2 * self.n))

    @property
    def m(self) -> list[int]:
        return list(range(2 * self.n, 3 * self.n))


def open_loop(n: int) -> tuple[State, Loop]:
    """t0: n pares de Bell (A_i, B_i). B queda en manos del pasado."""
    loop = Loop(n)
    st = State(3 * n)
    for a, b in zip(loop.a, loop.b):
        st.h(a).cx(a, b)
    return st, loop


def bell_measure(st: State, loop: Loop) -> None:
    """t1: medida de Bell de (A_i, M_i) como circuito. Tras ella, A_i lleva la
    parte de fase (Z) y M_i la parte de inversion (X) del resultado; |Phi+>
    es A_i = M_i = 0."""
    for a, m in zip(loop.a, loop.m):
        st.cx(a, m).h(a)


def close_loop(st: State, loop: Loop) -> float:
    """t1: medida de Bell y postseleccion sobre |Phi+>^n. Devuelve la medida
    de Born de la rama en la que el bucle se cierra."""
    bell_measure(st, loop)
    return st.postselect(loop.a + loop.m, 0)


def _branch_table(st: State, loop: Loop) -> dict[tuple[int, int], dict[int, float]]:
    """Lectura de Everett sin postseleccion: para cada resultado de Bell
    (z, s) en t1, que tenia el receptor en t0 y con que peso."""
    total = st.norm2()
    table: dict[tuple[int, int], dict[int, float]] = {}
    for i, amp in st.amps.items():
        key = (reg_value(i, loop.a), reg_value(i, loop.m))
        dist = table.setdefault(key, {})
        b = reg_value(i, loop.b)
        dist[b] = dist.get(b, 0.0) + abs(amp) ** 2 / total
    return table


# ---------------------------------------------------------------- mensajes
@dataclass
class MessageRun:
    """Un mensaje de n bits enviado desde t1 hacia t0."""

    message: int
    n: int
    p_loop_closes: float                       # medida de la rama que cierra
    received_if_closed: dict[int, float]       # lo que lee t0 en esa rama
    received_without_future: dict[int, float]  # lo que lee t0 sin saber t1
    branches: dict[tuple[int, int], dict[int, float]] = field(repr=False)
    state: State = field(repr=False)

    @property
    def fidelity(self) -> float:
        """Probabilidad de que, en la rama que cierra, t0 lea el mensaje."""
        return self.received_if_closed.get(self.message, 0.0)


def send_bits_to_past(message: int, n: int) -> MessageRun:
    if not 0 <= message < 1 << n:
        raise ValueError(f"el mensaje {message} no cabe en {n} bits")
    st, loop = open_loop(n)
    for i, m in enumerate(loop.m):          # t1: el emisor escribe el mensaje
        if (message >> i) & 1:
            st.x(m)
    bell_measure(st, loop)
    without_future = st.distribution(loop.b)
    branches = _branch_table(st, loop)
    p = st.postselect(loop.a + loop.m, 0)
    return MessageRun(
        message=message, n=n, p_loop_closes=p,
        received_if_closed=st.distribution(loop.b) if p > 0 else {},
        received_without_future=without_future,
        branches=branches, state=st,
    )


def receiver_density(message: int | None, n: int):
    """Matriz densidad de B (el receptor en t0) sin postseleccionar.

    `message=None` es el estado antes de que el emisor exista (solo t0);
    con un mensaje, es el estado tras todo lo que ocurre en t1, promediado
    sobre sus ramas -- que es todo lo que alguien en t0 puede conocer.
    """
    st, loop = open_loop(n)
    if message is not None:
        for i, m in enumerate(loop.m):
            if (message >> i) & 1:
                st.x(m)
        bell_measure(st, loop)
    return st.reduced_density(loop.b)


def send_bytes_to_past(payload: bytes) -> tuple[bytes, float]:
    """Envia bytes de t1 a t0 bit a bit (cada bit es un bucle independiente,
    de modo que la simulacion factoriza y es exacta). Devuelve lo que lee el
    receptor en la rama que cierra y la medida de Born de esa rama:
    4^-(8 * len(payload)). Para 'hola' son ~5e-20: el canal funciona, pero
    la rama en la que un mensaje largo llega es de medida despreciable."""
    bits_out = []
    log_p = 0.0
    for byte in payload:
        for k in range(8):
            run = send_bits_to_past((byte >> k) & 1, 1)
            if run.p_loop_closes == 0:
                return b"", 0.0
            log_p += math.log(run.p_loop_closes)
            bits_out.append(max(run.received_if_closed, key=run.received_if_closed.get))
    out = bytes(sum(bits_out[8 * j + k] << k for k in range(8))
                for j in range(len(payload)))
    return out, math.exp(log_p)


@dataclass
class QubitRun:
    p_loop_closes: float
    fidelity: float            # <psi| rho_B |psi> en la rama que cierra
    residue: list[list[complex]] = field(repr=False)   # estado de (A, M) tras cerrar
    state: State = field(repr=False)


def send_qubit_to_past(theta: float, phi: float) -> QubitRun:
    """Estado cuantico |psi> = cos(theta/2)|0> + e^{i phi} sin(theta/2)|1>
    enviado de t1 a t0. En la rama que cierra, B = |psi> exactamente, y en
    (A, M) no queda nada que dependa de psi: se transporta sin clonarse."""
    st, loop = open_loop(1)
    st.ry(loop.m[0], theta).phase(loop.m[0], phi)
    p = close_loop(st, loop)
    psi = [complex(math.cos(theta / 2)),
           complex(math.cos(phi), math.sin(phi)) * math.sin(theta / 2)]
    rho = st.reduced_density(loop.b)
    fid = sum((psi[i].conjugate() * rho[i][j] * psi[j]).real
              for i in range(2) for j in range(2))
    return QubitRun(p_loop_closes=p, fidelity=fid,
                    residue=st.reduced_density(loop.a + loop.m), state=st)


# ------------------------------------------------------- bucles causales
@dataclass
class LoopRun:
    """Bucle causal: lo que el emisor manda en t1 depende de lo que el
    receptor leyo en t0. Solo sobreviven los puntos fijos de f."""

    name: str
    n: int
    fixed_points: list[int]
    p_loop_closes: float
    received_if_closed: dict[int, float]
    state: State = field(repr=False)


def closed_loop(n: int, f: Callable[[int], int], name: str = "f") -> LoopRun:
    """t0: el receptor lee B. Su registro persiste hasta t1, donde el emisor
    manda f(B). El oraculo |b>|m> -> |b>|m XOR f(b)> es exactamente eso."""
    st, loop = open_loop(n)
    st.oracle(f, loop.b, loop.m, name)
    p = close_loop(st, loop)
    size = 1 << n
    return LoopRun(
        name=name, n=n,
        fixed_points=[x for x in range(size) if f(x) == x],
        p_loop_closes=p,
        received_if_closed=st.distribution(loop.b) if p > 0 else {},
        state=st,
    )


def grandfather(n: int = 1) -> LoopRun:
    """Paradoja del abuelo: el emisor manda lo contrario de lo que recibio."""
    mask = (1 << n) - 1
    return closed_loop(n, lambda x: x ^ mask, "abuelo")


def bootstrap(n: int = 1) -> LoopRun:
    """Paradoja del bootstrap: el emisor manda justo lo que recibio. Nadie
    escribio nunca el mensaje; ¿de donde sale su contenido?"""
    return closed_loop(n, lambda x: x, "bootstrap")


# ------------------------------------------------ computo desde el futuro
@dataclass
class SearchRun:
    """Busqueda por punto fijo: 'si lo que recibiste es solucion, reenvialo;
    si no, manda el siguiente candidato'. Los puntos fijos son exactamente
    las soluciones, asi que en la rama que cierra el pasado recibe una."""

    n: int
    solutions: list[int]
    p_loop_closes: float
    mass_on_solutions: float
    received_if_closed: dict[int, float] = field(repr=False)

    @property
    def size(self) -> int:
        return 1 << self.n

    @property
    def expected_runs(self) -> float:
        """Ejecuciones del circuito hasta que el bucle cierra (una evaluacion
        coherente del predicado por ejecucion)."""
        return math.inf if self.p_loop_closes == 0 else 1 / self.p_loop_closes

    @property
    def brute_force_expected_trials(self) -> float:
        k = len(self.solutions)
        return math.inf if k == 0 else self.size / k


def search_through_time(n: int, predicate: Callable[[int], bool]) -> SearchRun:
    size = 1 << n
    run = closed_loop(n, lambda x: x if predicate(x) else (x + 1) % size, "busqueda")
    solutions = run.fixed_points
    mass = sum(run.received_if_closed.get(x, 0.0) for x in solutions)
    return SearchRun(n=n, solutions=solutions, p_loop_closes=run.p_loop_closes,
                     mass_on_solutions=mass, received_if_closed=run.received_if_closed)


# ------------------------------------------------------ circuitos reales
def message_circuit(message: int, n: int) -> State:
    """El circuito de E7a, listo para `to_openqasm2`."""
    return send_bits_to_past(message, n).state


def grandfather_circuit() -> State:
    """Paradoja del abuelo con puertas estandar (CX + X en vez del oraculo)."""
    st, loop = open_loop(1)
    st.cx(loop.b[0], loop.m[0]).x(loop.m[0])
    close_loop(st, loop)
    return st


def bootstrap_circuit(n: int = 1) -> State:
    st, loop = open_loop(n)
    for b, m in zip(loop.b, loop.m):
        st.cx(b, m)
    close_loop(st, loop)
    return st
