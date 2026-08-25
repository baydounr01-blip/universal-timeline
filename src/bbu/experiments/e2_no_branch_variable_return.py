"""E2 -- "No hay retorno de variables de rama" (P9, P10; seccion 8).

Afirmacion contrastada: una prediccion calculada en la rama hermana sobre
SU futuro no tiene valor predictivo sobre el futuro de la rama de origen,
porque el propio gasto ya perturbo la rama y la dinamica diverge (P9).
Si la prediccion conservara valor, P10 quedaria refutado.

Procedimiento: la "economia" de cada rama es un mapa logistico caotico
identico en ambas ramas; el gasto ramificado perturba la condicion inicial
de la rama hermana. La copia observa el futuro de SU rama y lo envia como
prediccion. Se mide el error de esa prediccion contra el futuro real de la
rama de origen, comparado con el error de un adivino aleatorio, en dos
horizontes: antes del tiempo de divergencia (donde debe funcionar: las ramas
aun son casi identicas) y despues (donde no debe funcionar: la rama ya es
otra). El contraste entre ambos horizontes es lo que confirma que es la
DIVERGENCIA (P9), y no un defecto del canal, lo que anula el valor.
"""

from __future__ import annotations

import random
import statistics

from ..ledger import logistic_divergence
from .verdict import Outcome, Verdict


def _trajectory(x0: float, steps: int, r: float = 3.99) -> list[float]:
    xs = [x0]
    for _ in range(steps):
        xs.append(r * xs[-1] * (1.0 - xs[-1]))
    return xs


def run(n_trials: int = 200, horizon_late: int = 60, seed: int = 20260825) -> Verdict:
    rng = random.Random(seed)
    perturbation = 1e-9   # el gasto: minuscule al inicio, macroscopico despues
    horizon_early = 5

    early_err, late_err, random_err = [], [], []
    for _ in range(n_trials):
        x0 = rng.uniform(0.2, 0.8)
        origin = _trajectory(x0, horizon_late)
        sibling = _trajectory(x0 + perturbation, horizon_late)
        # La prediccion de la copia = el futuro de SU rama.
        early_err.append(abs(sibling[horizon_early] - origin[horizon_early]))
        late_err.append(abs(sibling[horizon_late] - origin[horizon_late]))
        random_err.append(abs(rng.uniform(0.0, 1.0) - origin[horizon_late]))

    mean_early = statistics.mean(early_err)
    mean_late = statistics.mean(late_err)
    mean_random = statistics.mean(random_err)

    # La afirmacion sobrevive si: (a) antes de divergir la prediccion es
    # casi perfecta; (b) despues de divergir su error es comparable al azar
    # (mismo orden de magnitud: no mejor que la mitad del error aleatorio).
    works_before_divergence = mean_early < 1e-3
    useless_after_divergence = mean_late > 0.5 * mean_random

    corroborated = works_before_divergence and useless_after_divergence
    return Verdict(
        claim="las predicciones del futuro de la rama no conservan valor tras la divergencia",
        postulates="P9,P10",
        outcome=Outcome.CORROBORATED if corroborated else Outcome.REFUTED,
        evidence={
            "error_medio_antes_de_divergir": round(mean_early, 9),
            "error_medio_tras_divergir": round(mean_late, 4),
            "error_medio_adivino_aleatorio": round(mean_random, 4),
            "horizonte_temprano": horizon_early,
            "horizonte_tardio": horizon_late,
            "perturbacion_del_gasto": perturbation,
        },
        notes="el manana de t' no es el manana de t: el propio gasto ya lo perturbo",
    )


def measured_divergence_profile() -> list[float]:
    """Perfil de divergencia usado por los tests de P9."""
    return logistic_divergence(x0=0.4, perturbation=1e-9, steps=80)
