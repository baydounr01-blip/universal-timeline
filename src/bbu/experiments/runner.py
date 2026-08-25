"""Ejecuta todos los experimentos y emite el veredicto global.

Este es el punto de entrada de "produccion": `python -m bbu verify` corre en
CI en cada push. Un solo REFUTADO inesperado tumba el pipeline: el repositorio
esta construido para que el articulo pueda fallar.
"""

from __future__ import annotations

from . import e1_no_onchain_signature, e2_no_branch_variable_return
from . import e3_offchain_signature, e4_emergent_relativity
from . import e5_million_btc, e6_fixed_point
from .verdict import Outcome, Verdict

# Que resultado declara el articulo para cada afirmacion. RESTRINGIDO es un
# resultado legitimo (la afirmacion sobrevive en forma acotada); REFUTADO
# nunca lo es: significa que el modelo contradice al articulo.
EXPECTED = {
    "E1": Outcome.CORROBORATED,
    "E2": Outcome.CORROBORATED,
    "E3": Outcome.CORROBORATED,
    "E4a": Outcome.CONSTRAINED,
    "E4b": Outcome.CORROBORATED,
    "E4c": Outcome.CONSTRAINED,
    "E5": Outcome.CORROBORATED,
    "E6": Outcome.CORROBORATED,
}


def run_all() -> dict[str, Verdict]:
    return {
        "E1": e1_no_onchain_signature.run(),
        "E2": e2_no_branch_variable_return.run(),
        "E3": e3_offchain_signature.run(),
        "E4a": e4_emergent_relativity.run_kinematic(),
        "E4b": e4_emergent_relativity.run_gps(),
        "E4c": e4_emergent_relativity.run_liv(),
        "E5": e5_million_btc.run(),
        "E6": e6_fixed_point.run(),
    }


def main(verbose: bool = True) -> int:
    verdicts = run_all()
    failures = 0
    lines = []
    lines.append("=" * 78)
    lines.append("UNIVERSO DE BLOQUES RAMIFICADOS -- bateria de falsacion")
    lines.append("=" * 78)
    for key, verdict in verdicts.items():
        status = "ok" if verdict.outcome == EXPECTED[key] else "FALLO"
        if status == "FALLO":
            failures += 1
        lines.append(f"{key:<4} {verdict.summary_line()}   <{status}>")
        if verbose:
            for k, v in verdict.evidence.items():
                lines.append(f"       - {k}: {v}")
            if verdict.notes:
                lines.append(f"       nota: {verdict.notes}")
    lines.append("-" * 78)
    if failures == 0:
        lines.append("Veredicto global: el marco sobrevive a su propia bateria de "
                     "falsacion (lo que corrobora coherencia, no verdad fisica).")
    else:
        lines.append(f"Veredicto global: {failures} afirmacion(es) del articulo "
                     "REFUTADA(S) por su propio modelo.")
    print("\n".join(lines))
    return 0 if failures == 0 else 1
