"""E4 -- Relatividad emergente (P5; secciones 2, 8 y 9).

Tres confrontaciones con datos y formulas publicadas:

(a) Dilatacion cinematica. El postulado dice "lo que gasta en desplazarse no
    lo gasta en evolucionar". Se simulan tics discretos con dos repartos del
    presupuesto: lineal (1-beta) y euclideo (sqrt(1-beta^2)). Se compara la
    dilatacion medida con el factor de Lorentz. Resultado esperado: la
    variante lineal queda REFUTADA, la euclidea CORROBORADA. El postulado
    sobrevive solo en forma restringida: el presupuesto se reparte en norma
    euclidea (todo se mueve a c a traves del espacio-tiempo).

(b) GPS. Con el modelo de densidad de tics (gravedad) mas el reparto euclideo
    (velocidad orbital) se calcula el adelanto diario de los relojes GPS y se
    compara con el valor publicado (~38.5 us/dia; Ashby 2003). Fallar este
    numero refutaria la pretension de la seccion 2.

(c) Invariancia de Lorentz cerca de Planck. La prediccion de la seccion 8 se
    confronta con las cotas de dispersion de fotones (GRB 090510): la
    variante con correccion lineal en E/E_Planck esta excluida; la
    cuadratica sigue viva. Veredicto: RESTRINGIDO.
"""

from __future__ import annotations

from ..relativity import (
    gps_daily_offset,
    liv_verdict,
    lorentz_gamma,
    measured_dilation,
)
from .verdict import Outcome, Verdict

BETAS = [0.1, 0.3, 0.5, 0.8, 0.9, 0.99]
N_TICKS = 2_000_000
TOLERANCE = 1e-3  # error relativo admisible frente a Lorentz


def _max_rel_error(combination: str) -> float:
    worst = 0.0
    for beta in BETAS:
        gamma = lorentz_gamma(beta)
        measured = measured_dilation(beta, N_TICKS, combination)
        worst = max(worst, abs(measured - gamma) / gamma)
    return worst


def run_kinematic() -> Verdict:
    err_euclidean = _max_rel_error("euclidean")
    err_linear = _max_rel_error("linear")

    euclidean_ok = err_euclidean < TOLERANCE
    linear_fails = err_linear > TOLERANCE  # debe fallar: es la variante ingenua

    if euclidean_ok and linear_fails:
        outcome = Outcome.CONSTRAINED
        notes = ("P5 sobrevive SOLO con reparto euclideo del presupuesto; la "
                 "lectura lineal ingenua del postulado queda refutada por Lorentz")
    elif euclidean_ok:
        outcome = Outcome.CORROBORATED
        notes = "ambas variantes compatibles (inesperado)"
    else:
        outcome = Outcome.REFUTED
        notes = "ninguna variante del presupuesto reproduce a Lorentz"

    return Verdict(
        claim="la dilatacion de Lorentz emerge de un presupuesto discreto por tic",
        postulates="P5",
        outcome=outcome,
        evidence={
            "error_max_variante_euclidea": f"{err_euclidean:.2e}",
            "error_max_variante_lineal": f"{err_linear:.2e}",
            "betas_probadas": BETAS,
            "tics_por_simulacion": N_TICKS,
        },
        notes=notes,
    )


def run_gps() -> Verdict:
    budget = gps_daily_offset()
    # Ashby (2003): +45.7 gravitatorio, -7.2 cinematico, neto ~ +38.5 us/dia.
    ok = (44.5 < budget.gravitational_us < 46.5
          and -7.7 < budget.kinematic_us < -6.7
          and 38.0 < budget.net_us < 39.0)
    return Verdict(
        claim="el modelo discreto reproduce los ~38 us/dia de los relojes GPS (Ashby 2003)",
        postulates="P5",
        outcome=Outcome.CORROBORATED if ok else Outcome.REFUTED,
        evidence={
            "gravitatorio_us_dia": round(budget.gravitational_us, 2),
            "cinematico_us_dia": round(budget.kinematic_us, 2),
            "neto_us_dia": round(budget.net_us, 2),
            "valor_publicado_us_dia": "~38.5",
        },
        notes="calculado desde densidad de tics + presupuesto euclideo, "
              "sin usar las formulas de la relatividad como entrada",
    )


def run_liv() -> Verdict:
    v = liv_verdict()
    # La prediccion "desviaciones cerca de Planck" solo sobrevive en la
    # variante con supresion al menos cuadratica.
    constrained = v["linear_variant_excluded"] and not v["quadratic_variant_excluded"]
    return Verdict(
        claim="P5 predice violacion de Lorentz cerca de Planck; las cotas de fotones la restringen",
        postulates="P5,S8",
        outcome=Outcome.CONSTRAINED if constrained else Outcome.REFUTED,
        evidence={
            "escala_del_modelo_gev": f"{v['model_scale_gev']:.2e}",
            "cota_lineal_gev": f"{v['linear_bound_gev']:.2e}",
            "cota_cuadratica_gev": f"{v['quadratic_bound_gev']:.2e}",
            "variante_lineal_excluida": v["linear_variant_excluded"],
            "variante_cuadratica_excluida": v["quadratic_variant_excluded"],
        },
        notes="tal como admite la seccion 8: si la invariancia resultara exacta "
              "a todas las escalas, P5 tendria que reformularse",
    )
