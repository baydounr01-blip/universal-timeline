"""Reglas de consenso de Bitcoin usadas por el experimento del millon (P8, seccion 5).

El articulo apoya su experimento mental en reglas publicas y verificables del
protocolo (Nakamoto 2008 y el software de referencia). Aqui se implementan
las tres que el argumento necesita:

  * calendario de emision: 50 BTC por bloque, mitad cada 210.000 bloques;
  * regla de la cadena con mas trabajo acumulado (y que una reorganizacion
    borra las transacciones de los bloques sustituidos);
  * puntos de control / trabajo minimo asumido, que hacen inaceptable una
    reescritura profunda aunque presentara mas trabajo.
"""

from __future__ import annotations

from dataclasses import dataclass

INITIAL_SUBSIDY_BTC = 50.0
HALVING_INTERVAL = 210_000
POST_2024_HEIGHT = 840_000   # altura del halving de abril de 2024 (era 3.125)


def subsidy_at_height(height: int) -> float:
    """Recompensa de protocolo del bloque a la altura `height`."""
    halvings = height // HALVING_INTERVAL
    if halvings >= 64:
        return 0.0
    return INITIAL_SUBSIDY_BTC / (2 ** halvings)


def cumulative_subsidy(start_height: int, n_blocks: int) -> float:
    """BTC de recompensa acumulados minando n_blocks desde start_height."""
    total = 0.0
    for h in range(start_height, start_height + n_blocks):
        total += subsidy_at_height(h)
    return total


def blocks_needed_for(amount_btc: float, start_height: int,
                      hard_cap: int = 10_000_000) -> int | None:
    """Bloques que hay que minar (reescribiendo historia desde start_height)
    para acumular `amount_btc` solo con recompensas de protocolo. None si el
    calendario de emision nunca lo alcanza."""
    total = 0.0
    for i in range(hard_cap):
        total += subsidy_at_height(start_height + i)
        if total >= amount_btc:
            return i + 1
    return None


@dataclass
class CompetingChain:
    """Una cadena candidata presentada a un nodo de la rama de origen."""

    fork_height: int          # altura de la bifurcacion respecto a la cadena local
    length: int               # bloques desde la bifurcacion
    work_per_block: float     # trabajo medio por bloque


@dataclass
class NodeView:
    """Vista de un nodo de la rama de origen: cadena local + salvaguardas."""

    tip_height: int
    work_per_block: float
    checkpoint_height: int    # los bloques <= checkpoint no se reorganizan
    minimum_chain_work: float # trabajo minimo asumido por el software

    def local_work_since(self, fork_height: int) -> float:
        return (self.tip_height - fork_height) * self.work_per_block

    def evaluate(self, chain: CompetingChain) -> tuple[bool, str]:
        """Decide si el nodo aceptaria la cadena competidora, y por que."""
        if chain.fork_height < self.checkpoint_height:
            return False, "rechazada: bifurca por debajo de un punto de control"
        total_work = chain.length * chain.work_per_block
        if total_work < self.minimum_chain_work:
            return False, "rechazada: menos trabajo que el minimo asumido"
        if total_work <= self.local_work_since(chain.fork_height):
            return False, "rechazada: menos trabajo acumulado que la cadena local"
        return True, ("aceptada: reorganizacion que borra las transacciones "
                      "locales posteriores a la bifurcacion")
