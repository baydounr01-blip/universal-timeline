"""P4: consenso = decoherencia.

No existe una "cadena mas larga" global que decida que rama es real. Cada
observador tiene por real la rama con la que su propio registro esta
entrelazado; la decoherencia es el mecanismo que fija ese registro. No hay
rama privilegiada.

El modelo: un observador acumula un registro (inmutable una vez escrito) de
los bloques con los que ha interactuado. "Real para el observador" se define
exclusivamente respecto a ese registro. No se ofrece --deliberadamente--
ninguna funcion global `rama_real()`: su ausencia es parte del postulado.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .block import Block


class RecordImmutabilityError(Exception):
    """El registro decoherido de un observador no puede reescribirse."""


@dataclass
class Observer:
    name: str
    _record: list[str] = field(default_factory=list)   # hashes de bloques, orden causal
    _current: Block | None = None

    def decohere(self, block: Block) -> None:
        """Entrelaza el registro del observador con `block` (irreversible).

        La decoherencia fija la rama: el nuevo bloque debe descender del
        ultimo bloque registrado. Registrarse con una rama hermana seria
        reescribir el registro, y eso esta prohibido.
        """
        if self._current is not None:
            if not self._current.is_ancestor_of(block) and block is not self._current:
                raise RecordImmutabilityError(
                    f"{self.name}: el bloque {block.branch_id}@{block.tick} no "
                    f"desciende del registro ya fijado "
                    f"({self._current.branch_id}@{self._current.tick})"
                )
        self._record.append(block.block_hash)
        self._current = block

    @property
    def record(self) -> tuple[str, ...]:
        return tuple(self._record)

    def considers_real(self, block: Block) -> bool:
        """Real *para este observador* = pertenece a su linea de descendencia
        registrada (o desciende de ella). Nocion relativa, nunca global."""
        if self._current is None:
            return False
        if block.block_hash in self._record:
            return True
        return self._current.is_ancestor_of(block) or block.is_ancestor_of(self._current)

    def branch(self) -> Block | None:
        return self._current
