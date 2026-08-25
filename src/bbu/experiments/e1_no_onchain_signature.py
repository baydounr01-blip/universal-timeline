"""E1 -- "No hay firma en cadena" (P7, P12; seccion 8).

Afirmacion contrastada: ningun analisis de la cadena de bloques de la rama
de origen puede detectar gasto ramificado. Si el gasto en ramas hermanas
dejara CUALQUIER rastro en el libro mayor de origen, la teoria quedaria
refutada.

Procedimiento: se construye el libro mayor de la rama de origen, se toma su
huella (hash del conjunto UTXO y de la historia), se ejecutan N gastos
ramificados del mismo millon en N ramas hermanas heredadas, y se vuelve a
tomar la huella. Cualquier diferencia = REFUTADO.
"""

from __future__ import annotations

from ..ledger import BranchLedger
from .verdict import Outcome, Verdict

MILLION_BTC_UTXO = "utxo:1M"


def build_origin_ledger() -> BranchLedger:
    ledger = BranchLedger(branch_id="t")
    ledger.utxo[MILLION_BTC_UTXO] = True
    for i in range(100):  # otras monedas de la economia
        ledger.utxo[f"utxo:{i}"] = True
    ledger.history.append("bloque:base")
    return ledger


def run(n_branches: int = 1000) -> Verdict:
    origin = build_origin_ledger()
    before_utxo = origin.snapshot_hash()
    before_history = tuple(origin.history)

    spent_in_branches = 0
    for i in range(n_branches):
        sibling = origin.inherit(new_branch_id=f"t'/{i}")
        # Herencia automatica (P8): el millon existe en la rama hermana...
        assert sibling.is_unspent(MILLION_BTC_UTXO)
        # ...y alli se gasta (P7): mismo utxo_id, otra rama.
        sibling.spend(MILLION_BTC_UTXO, memo=f"gasto ramificado {i}")
        spent_in_branches += 1

    after_utxo = origin.snapshot_hash()
    after_history = tuple(origin.history)

    untouched = (before_utxo == after_utxo
                 and before_history == after_history
                 and origin.is_unspent(MILLION_BTC_UTXO))

    return Verdict(
        claim="ningun analisis en cadena de la rama de origen detecta el gasto ramificado",
        postulates="P7,P12",
        outcome=Outcome.CORROBORATED if untouched else Outcome.REFUTED,
        evidence={
            "gastos_ramificados": spent_in_branches,
            "huella_utxo_antes": before_utxo[:16],
            "huella_utxo_despues": after_utxo[:16],
            "millon_intacto_en_origen": origin.is_unspent(MILLION_BTC_UTXO),
        },
        notes="el mismo UTXO se gasto una vez por rama hermana; el libro de "
              "origen no registra nada porque nada se movio en el",
    )
