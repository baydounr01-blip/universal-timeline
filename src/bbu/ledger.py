"""P7-P9: propiedad indexada por rama, herencia automatica, divergencia.

P7. El estado de un UTXO no es una propiedad de la moneda sino de la pareja
    (moneda, rama): (u, B) -> {gastado, sin gastar}. Gastar u en B' no altera
    (u, B). Dentro de un libro mayor, el consenso impide el doble gasto;
    entre libros mayores de ramas distintas no hay nada que impedir.

P8. Una rama hermana bifurcada en t-1 hereda el estado completo: la misma
    cadena, los mismos hashes, los mismos UTXO, las mismas claves.

P9. A partir del mensaje recibido la rama diverge de la del emisor, y un
    gasto grande (1M BTC ~ 5% de la oferta) acelera la divergencia.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

BTC_MAX_SUPPLY = 21_000_000.0


class DoubleSpendError(Exception):
    """Doble gasto DENTRO de la misma rama: lo unico que el consenso prohibe."""


class UnknownCoinError(Exception):
    """La moneda no existe en el libro mayor de esta rama."""


def _utxo_snapshot_hash(utxo: dict[str, bool]) -> str:
    data = json.dumps(utxo, sort_keys=True).encode()
    return hashlib.sha256(data).hexdigest()


@dataclass
class BranchLedger:
    """El libro mayor DE UNA RAMA. No existe un libro mayor global (P4/P7)."""

    branch_id: str
    utxo: dict[str, bool] = field(default_factory=dict)  # utxo_id -> sin_gastar
    history: list[str] = field(default_factory=list)     # transacciones registradas

    # ------------------------------------------------------------------ P8
    def inherit(self, new_branch_id: str) -> "BranchLedger":
        """Herencia automatica: la rama hermana nace con una copia exacta.

        Mismos UTXO, misma historia, mismos hashes. No hay que reconstruir
        nada; la copia es constitutiva de la bifurcacion.
        """
        return BranchLedger(
            branch_id=new_branch_id,
            utxo=dict(self.utxo),
            history=list(self.history),
        )

    # ------------------------------------------------------------------ P7
    def spend(self, utxo_id: str, memo: str = "") -> None:
        """Gasta (utxo_id, ESTA rama). No toca ninguna otra pareja (u, B)."""
        if utxo_id not in self.utxo:
            raise UnknownCoinError(
                f"{utxo_id!r} no existe en el libro mayor de {self.branch_id!r}: "
                "las monedas de otra rama no existen aqui"
            )
        if not self.utxo[utxo_id]:
            raise DoubleSpendError(
                f"doble gasto de {utxo_id!r} dentro de la rama {self.branch_id!r}"
            )
        self.utxo[utxo_id] = False
        self.history.append(f"spend:{utxo_id}:{memo}")

    def is_unspent(self, utxo_id: str) -> bool:
        return self.utxo.get(utxo_id, False)

    def balance(self, coins: dict[str, float]) -> float:
        """Suma del valor de los UTXO sin gastar (valores dados por `coins`)."""
        return sum(v for u, v in coins.items() if self.utxo.get(u, False))

    def snapshot_hash(self) -> str:
        """Huella del estado del libro mayor: la 'firma en cadena' de P12 se
        buscaria comparando estas huellas antes y despues del gasto ramificado."""
        return _utxo_snapshot_hash(self.utxo)

    def total_unspent(self) -> int:
        return sum(1 for v in self.utxo.values() if v)


# ---------------------------------------------------------------------- P9

def logistic_divergence(x0: float, perturbation: float, steps: int,
                        r: float = 3.99) -> list[float]:
    """Distancia entre dos trayectorias del mapa logistico: la rama original
    (x0) y la perturbada por el gasto (x0 + perturbation).

    Modelo minimo de "shock de mercado": dinamica caotica en la que una
    perturbacion del orden del gasto se amplifica exponencialmente. Devuelve
    |x_t - y_t| para t = 0..steps.
    """
    if not 0.0 < x0 < 1.0 or not 0.0 < x0 + perturbation < 1.0:
        raise ValueError("las condiciones iniciales deben quedar en (0, 1)")
    x, y = x0, x0 + perturbation
    distances = [abs(y - x)]
    for _ in range(steps):
        x = r * x * (1.0 - x)
        y = r * y * (1.0 - y)
        distances.append(abs(y - x))
    return distances


def divergence_time(x0: float, perturbation: float, threshold: float = 0.1,
                    r: float = 3.99, max_steps: int = 10_000) -> int:
    """Pasos hasta que la rama es macroscopicamente distinta (P9): primera t
    con |x_t - y_t| >= threshold. Un gasto mayor (perturbacion mayor)
    diverge antes."""
    dists = logistic_divergence(x0, perturbation, max_steps, r)
    for t, d in enumerate(dists):
        if d >= threshold:
            return t
    return max_steps
