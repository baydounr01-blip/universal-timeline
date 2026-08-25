"""E6 -- Condicion de punto fijo y etica de las copias (P11; seccion 7).

Afirmaciones contrastadas:

  * el protocolo asimetrico ("yo conservo, tu pagas / delega") no es punto
    fijo: su unica historia consistente es la vacia -- nadie computa, nada
    regresa;
  * el protocolo simetrico (cada rama paga su millon y computa) es punto
    fijo y produce retorno;
  * "alguien paga siempre": no existe historia con retorno positivo y gasto
    cero.

Si existiera un protocolo con retorno positivo sin que ninguna rama pagara,
P11 (y la seccion 7 entera) quedaria refutado.
"""

from __future__ import annotations

from ..fixedpoint import (
    Action,
    Protocol,
    is_fixed_point,
    resolve_history,
    someone_always_pays,
)
from .verdict import Outcome, Verdict


def run(branches: int = 1000) -> Verdict:
    symmetric = Protocol(action=Action.PAY_AND_COMPUTE,
                         work_units_per_branch=10, cost_btc_per_branch=1_000_000.0)
    asymmetric = Protocol(action=Action.DELEGATE,
                          work_units_per_branch=10, cost_btc_per_branch=1_000_000.0)

    h_sym = resolve_history(symmetric, branches)
    h_asym = resolve_history(asymmetric, branches)

    checks = {
        "asimetrico_no_es_punto_fijo": not is_fixed_point(asymmetric),
        "historia_asimetrica_vacia": h_asym.empty and h_asym.total_work_returned == 0,
        "simetrico_es_punto_fijo": is_fixed_point(symmetric),
        "historia_simetrica_con_retorno": h_sym.total_work_returned > 0,
        "todas_las_ramas_pagan": h_sym.branches_that_paid == branches,
        "alguien_paga_siempre": someone_always_pays(h_sym) and someone_always_pays(h_asym),
    }
    ok = all(checks.values())
    return Verdict(
        claim="solo el protocolo simetrico produce retorno; la historia del "
              "asimetrico es la vacia; alguien paga siempre",
        postulates="P11,S7",
        outcome=Outcome.CORROBORATED if ok else Outcome.REFUTED,
        evidence={
            **checks,
            "btc_gastados_en_total_historia_simetrica": h_sym.total_btc_spent,
            "trabajo_devuelto_historia_simetrica": h_sym.total_work_returned,
            "trabajo_devuelto_historia_asimetrica": h_asym.total_work_returned,
        },
        notes="bajo el protocolo simetrico la pregunta 'quien es el original' "
              "pierde sentido (P4)",
    )
