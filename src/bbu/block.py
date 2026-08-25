"""P1-P3: tiempo discreto, enlace = causalidad, ramificacion.

El universo se modela como un arbol de bloques. Cada bloque contiene el
estado completo (el vector de estado) en un tic discreto (P1). Cada bloque
enlaza a su padre mediante un hash del estado del padre: ese enlace ES la
relacion causal (P2). Un bloque no tiene un sucesor sino un abanico de
sucesores con amplitudes (P3, formulacion de estados relativos de Everett).

El hash aqui es SHA-256 sobre una serializacion canonica del bloque. El
articulo aclara que en la ontologia el "hash" es la condicion de ser la
evolucion unitaria del predecesor; usar un hash criptografico real hace la
condicion *verificable* en los tests: cualquier alteracion de un ancestro
rompe la cadena de enlaces de forma detectable (se usa tambien en P8).
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field

# P1: el tic fundamental es el tiempo de Planck, no el segundo.
PLANCK_TIME_S = 5.391247e-44  # s (CODATA)
TICKS_PER_SECOND = 1.0 / PLANCK_TIME_S  # ~1.85e43: "un segundo agrupa ~1e43 tics"


class ForkRuleViolation(Exception):
    """Intento de alterar un ancestro directo del observador (prohibido por P6c)."""


class CausalityError(Exception):
    """Violacion de la estructura causal (enlace roto, tic no monotono...)."""


def _canonical_hash(payload: dict) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


@dataclass
class Block:
    """Un bloque = el estado completo del universo en un tic (P1)."""

    tick: int                      # P1: indice discreto de tiempo
    branch_id: str                 # P3: identificador de la linea de descendencia
    state: dict                    # vector de estado (representacion clasica del modelo)
    parent: "Block | None" = None  # P2: enlace causal
    amplitude: complex = 1.0 + 0j  # P3: amplitud de esta rama respecto al padre
    children: list["Block"] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.parent is not None and self.tick != self.parent.tick + 1:
            raise CausalityError(
                f"tic no consecutivo: padre={self.parent.tick}, hijo={self.tick}"
            )
        self.parent_hash = self.parent.block_hash if self.parent else "GENESIS"

    @property
    def block_hash(self) -> str:
        """P2: el hash compromete estado, tic, rama y el hash del padre."""
        return _canonical_hash(
            {
                "tick": self.tick,
                "branch_id": self.branch_id,
                "state": self.state,
                "parent_hash": self.parent_hash,
            }
        )

    # ------------------------------------------------------------------ P3
    def branch(self, outcomes: list[tuple[str, dict, complex]]) -> list["Block"]:
        """Ramifica: crea el abanico de sucesores posibles con amplitudes.

        `outcomes` es una lista de (sufijo_de_rama, estado, amplitud). Las
        amplitudes deben estar normalizadas: sum |a|^2 = 1.
        """
        norm = sum(abs(a) ** 2 for _, _, a in outcomes)
        if not math.isclose(norm, 1.0, rel_tol=1e-9):
            raise ValueError(f"amplitudes no normalizadas: sum|a|^2={norm}")
        new_children = []
        for suffix, state, amplitude in outcomes:
            child = Block(
                tick=self.tick + 1,
                branch_id=f"{self.branch_id}/{suffix}",
                state=state,
                parent=self,
                amplitude=amplitude,
            )
            self.children.append(child)
            new_children.append(child)
        return new_children

    def extend(self, state: dict, suffix: str = "0") -> "Block":
        """Sucesor unico (amplitud 1): evolucion sin ramificacion apreciable."""
        return self.branch([(suffix, state, 1.0 + 0j)])[0]

    # ------------------------------------------------------------------ P2
    def lineage(self) -> list["Block"]:
        """La linea de descendencia: del genesis a este bloque."""
        chain: list[Block] = []
        node: Block | None = self
        while node is not None:
            chain.append(node)
            node = node.parent
        return list(reversed(chain))

    def lineage_hash(self) -> str:
        """Huella de toda la historia que conduce a este bloque."""
        return _canonical_hash({"chain": [b.block_hash for b in self.lineage()]})

    def ancestor_at(self, tick: int) -> "Block":
        """P2: cada instante anterior es, por construccion, un ancestro."""
        if tick > self.tick:
            raise CausalityError(f"el tic {tick} no es anterior a {self.tick}")
        node: Block = self
        while node.tick > tick:
            assert node.parent is not None, "cadena rota antes del genesis"
            node = node.parent
        return node

    def is_ancestor_of(self, other: "Block") -> bool:
        return any(b is self for b in other.lineage())

    def is_sibling_branch_of(self, other: "Block") -> bool:
        """Ramas hermanas: comparten ancestros, nunca descendientes (P3)."""
        if self.is_ancestor_of(other) or other.is_ancestor_of(self):
            return False
        return self.common_ancestor(other) is not None

    def common_ancestor(self, other: "Block") -> "Block | None":
        mine = {id(b) for b in self.lineage()}
        for b in reversed(other.lineage()):
            if id(b) in mine:
                return b
        return None

    def verify_chain(self) -> bool:
        """P2: verifica que cada enlace de la linea de descendencia es valido."""
        for block in self.lineage():
            expected = block.parent.block_hash if block.parent else "GENESIS"
            if block.parent_hash != expected:
                return False
        return True

    def born_probability(self) -> float:
        """|amplitud acumulada|^2 de esta linea desde el genesis.

        (El porque estas cantidades se comportan como probabilidades para un
        observador queda abierto en el articulo, seccion 9.)
        """
        p = 1.0
        for block in self.lineage():
            p *= abs(block.amplitude) ** 2
        return p
