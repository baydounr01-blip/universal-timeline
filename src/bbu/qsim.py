"""Simulador cuantico exacto (vector de estado disperso, Python puro).

Lo justo para el mecanismo del canal P6 (`pctc`): puertas H, X, Z, CX, RY,
fase, oraculos clasicos reversibles |x>|y> -> |x>|y XOR f(x)>, postseleccion
y matrices densidad reducidas. Sin dependencias, para que la bateria siga
corriendo con `pip install -e .` y nada mas.

Convencion: el qubit q es el bit q del indice de la base (little-endian,
la de Qiskit). Un registro es una lista de qubits; su valor entero lee el
primer qubit de la lista como bit menos significativo.

Cada puerta queda registrada en `ops`, de modo que el mismo circuito que se
simula aqui se puede exportar a OpenQASM 2.0 (`to_openqasm2`) y ejecutar en
un procesador cuantico real: la postseleccion se hace alli descartando los
disparos cuyo resultado no es el pedido, igual que en el experimento con
fotones de Lloyd et al. (2011).
"""

from __future__ import annotations

import math
from typing import Callable, Sequence

_EPS = 1e-14


def reg_value(index: int, qubits: Sequence[int]) -> int:
    """Valor entero de un registro dentro de un indice de la base."""
    return sum(((index >> q) & 1) << i for i, q in enumerate(qubits))


def _with_reg(index: int, qubits: Sequence[int], value: int) -> int:
    for i, q in enumerate(qubits):
        if (value >> i) & 1:
            index |= 1 << q
        else:
            index &= ~(1 << q)
    return index


class State:
    """Vector de estado de `n` qubits, disperso: {indice: amplitud}."""

    def __init__(self, n_qubits: int) -> None:
        self.n = n_qubits
        self.amps: dict[int, complex] = {0: 1.0 + 0j}
        self.ops: list[tuple] = []

    def copy(self) -> "State":
        other = State(self.n)
        other.amps = dict(self.amps)
        other.ops = list(self.ops)
        return other

    # ------------------------------------------------------------ puertas
    def _map(self, fn: Callable[[int, complex], list[tuple[int, complex]]]) -> None:
        new: dict[int, complex] = {}
        for idx, amp in self.amps.items():
            for j, a in fn(idx, amp):
                new[j] = new.get(j, 0j) + a
        self.amps = {j: a for j, a in new.items() if abs(a) > _EPS}

    def x(self, q: int) -> "State":
        self.ops.append(("x", q))
        self._map(lambda i, a: [(i ^ (1 << q), a)])
        return self

    def z(self, q: int) -> "State":
        self.ops.append(("z", q))
        self._map(lambda i, a: [(i, -a if (i >> q) & 1 else a)])
        return self

    def phase(self, q: int, phi: float) -> "State":
        """diag(1, e^{i phi}); en OpenQASM 2.0, u1(phi)."""
        self.ops.append(("u1", q, phi))
        w = complex(math.cos(phi), math.sin(phi))
        self._map(lambda i, a: [(i, a * w if (i >> q) & 1 else a)])
        return self

    def h(self, q: int) -> "State":
        self.ops.append(("h", q))
        s = 1 / math.sqrt(2)
        bit = 1 << q

        def f(i: int, a: complex) -> list[tuple[int, complex]]:
            sign = -1 if i & bit else 1
            return [(i & ~bit, a * s), (i | bit, a * s * sign)]

        self._map(f)
        return self

    def ry(self, q: int, theta: float) -> "State":
        """Rotacion Y: |0> -> cos(t/2)|0> + sin(t/2)|1>."""
        self.ops.append(("ry", q, theta))
        c, s = math.cos(theta / 2), math.sin(theta / 2)
        bit = 1 << q

        def f(i: int, a: complex) -> list[tuple[int, complex]]:
            if i & bit:
                return [(i & ~bit, -s * a), (i, c * a)]
            return [(i, c * a), (i | bit, s * a)]

        self._map(f)
        return self

    def cx(self, control: int, target: int) -> "State":
        self.ops.append(("cx", control, target))
        self._map(lambda i, a: [(i ^ (1 << target), a) if (i >> control) & 1 else (i, a)])
        return self

    def oracle(self, f: Callable[[int], int], inputs: Sequence[int],
               outputs: Sequence[int], name: str = "f") -> "State":
        """|x>|y> -> |x>|y XOR f(x)>. Unitario para cualquier f: es la forma
        reversible estandar de evaluar una funcion clasica."""
        self.ops.append(("oracle", name))
        width = 1 << len(outputs)

        def g(i: int, a: complex) -> list[tuple[int, complex]]:
            fx = f(reg_value(i, inputs))
            if not 0 <= fx < width:
                raise ValueError(f"f(x)={fx} no cabe en {len(outputs)} qubits")
            return [(_with_reg(i, outputs, reg_value(i, outputs) ^ fx), a)]

        self._map(g)
        return self

    # --------------------------------------------------------- medida
    def norm2(self) -> float:
        return sum(abs(a) ** 2 for a in self.amps.values())

    def distribution(self, qubits: Sequence[int]) -> dict[int, float]:
        """Probabilidades de Born del registro (sin tocar el estado)."""
        total = self.norm2()
        out: dict[int, float] = {}
        for i, a in self.amps.items():
            v = reg_value(i, qubits)
            out[v] = out.get(v, 0.0) + abs(a) ** 2 / total
        return out

    def postselect(self, qubits: Sequence[int], value: int) -> float:
        """Proyecta el registro sobre `value` y renormaliza. Devuelve la
        probabilidad de Born de ese resultado (0.0 si es imposible: entonces
        el estado queda vacio, no hay historia que renormalizar)."""
        self.ops.append(("postselect", tuple(qubits), value))
        total = self.norm2()
        kept = {i: a for i, a in self.amps.items() if reg_value(i, qubits) == value}
        p = sum(abs(a) ** 2 for a in kept.values()) / total
        if p <= _EPS:
            self.amps = {}
            return 0.0
        k = 1 / math.sqrt(p * total)
        self.amps = {i: a * k for i, a in kept.items()}
        return p

    def reduced_density(self, qubits: Sequence[int]) -> list[list[complex]]:
        """Matriz densidad reducida del registro (traza parcial del resto)."""
        dim = 1 << len(qubits)
        mask = 0
        for q in qubits:
            mask |= 1 << q
        total = self.norm2()
        groups: dict[int, dict[int, complex]] = {}
        for i, a in self.amps.items():
            groups.setdefault(i & ~mask, {})[reg_value(i, qubits)] = a
        rho = [[0j] * dim for _ in range(dim)]
        for comp in groups.values():
            for r, ar in comp.items():
                for c, ac in comp.items():
                    rho[r][c] += ar * ac.conjugate() / total
        return rho


def max_entry_difference(rho: list[list[complex]], sigma: list[list[complex]]) -> float:
    """max |rho_ij - sigma_ij|. Es 0 si y solo si las dos matrices densidad son
    iguales, que es lo unico que necesita la comprobacion de no senalizacion:
    ninguna medida sobre el registro distingue dos estados iguales."""
    dim = len(rho)
    return max(abs(rho[i][j] - sigma[i][j]) for i in range(dim) for j in range(dim))


def shannon_bits(dist: dict[int, float]) -> float:
    return -sum(p * math.log2(p) for p in dist.values() if p > 0)


def to_openqasm2(state: State, measure: Sequence[int] | None = None,
                 comment: str = "") -> str:
    """Exporta el circuito registrado a OpenQASM 2.0.

    Las postselecciones no son puertas: se traducen en un comentario que dice
    que disparos conservar. Todos los qubits se miden al final (o los de
    `measure`), que es como se postselecciona en hardware real.
    """
    lines = ["OPENQASM 2.0;", 'include "qelib1.inc";']
    for c in comment.strip().splitlines():
        lines.append(f"// {c}".rstrip())
    lines += [f"qreg q[{state.n}];", f"creg c[{state.n}];"]
    keep: list[str] = []
    for op in state.ops:
        kind = op[0]
        if keep and kind != "postselect":
            raise NotImplementedError(
                "hay puertas despues de una postseleccion: en hardware real la "
                "postseleccion se hace al final, descartando disparos")
        if kind in ("h", "x", "z"):
            lines.append(f"{kind} q[{op[1]}];")
        elif kind == "cx":
            lines.append(f"cx q[{op[1]}],q[{op[2]}];")
        elif kind in ("ry", "u1"):
            lines.append(f"{kind}({op[2]!r}) q[{op[1]}];")
        elif kind == "postselect":
            qubits, value = op[1], op[2]
            keep += [f"c[{q}]={(value >> i) & 1}" for i, q in enumerate(qubits)]
        else:
            raise NotImplementedError(
                f"la operacion {kind!r} no tiene traduccion directa a OpenQASM 2.0; "
                "descomponla en puertas antes de exportar")
    for q in (range(state.n) if measure is None else measure):
        lines.append(f"measure q[{q}] -> c[{q}];")
    if keep:
        lines.append("// postseleccion: conserva solo los disparos con " + ", ".join(keep))
    return "\n".join(lines) + "\n"
