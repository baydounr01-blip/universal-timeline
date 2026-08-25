"""P5: relatividad emergente de un presupuesto de actualizacion por tic.

Cada sistema dispone de un presupuesto fijo de actualizacion por tic del
sustrato. Lo que gasta en desplazarse por el espacio no lo gasta en
evolucionar internamente (dilatacion cinematica). La gravedad se modela como
densidad local de tics (dilatacion gravitatoria).

El articulo AFIRMA que la relatividad debe recuperarse como limite (seccion
2) pero reconoce (seccion 9) que no deriva el modelo del presupuesto. Este
modulo convierte esa carencia en un experimento: implementa DOS variantes de
reparto del presupuesto y las confronta con el factor de Lorentz y con el
dato duro del GPS (~38 us/dia, Ashby 2003).

  * 'linear'   : tasa interna = 1 - beta        (lectura ingenua del postulado)
  * 'euclidean': tasa interna = sqrt(1 - beta^2) (presupuesto en norma euclidea)

Solo la variante euclidea reproduce la dilatacion de Lorentz; la lineal queda
refutada por los tests. Ese resultado ES contenido cientifico del repo: fija
la unica forma viable del postulado P5.

Ademas, P5 predice desviaciones de la invariancia de Lorentz cerca de la
escala de Planck (seccion 8). `liv_verdict()` confronta esa prediccion con
las cotas publicadas de dispersion de fotones de estallidos de rayos gamma.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# --- Constantes fisicas (SI) -------------------------------------------------
C = 2.99792458e8            # m/s
GM_EARTH = 3.986004418e14   # m^3/s^2
R_EARTH = 6.371e6           # m (radio medio; sin correccion de geoide)
R_GPS = 2.656175e7          # m (semieje mayor de la orbita GPS)
SECONDS_PER_DAY = 86400.0
E_PLANCK_GEV = 1.22e19      # energia de Planck en GeV

# Cota observacional sobre violacion lineal de la invariancia de Lorentz
# (dispersion de fotones, GRB 090510; Vasileiou et al. 2013, Phys. Rev. D 87):
# E_QG,1 > 9.3 x E_Planck. Para el termino cuadratico la cota es muchisimo
# mas debil: E_QG,2 > ~1.3e11 GeV << E_Planck.
LIV_LINEAR_BOUND_GEV = 9.3 * E_PLANCK_GEV
LIV_QUADRATIC_BOUND_GEV = 1.3e11


def lorentz_gamma(beta: float) -> float:
    """Referencia continua: gamma = 1/sqrt(1-beta^2)."""
    if not 0.0 <= beta < 1.0:
        raise ValueError("beta debe estar en [0, 1)")
    return 1.0 / math.sqrt(1.0 - beta * beta)


def internal_rate(beta: float, combination: str) -> float:
    """Fraccion del presupuesto por tic que queda para evolucion interna."""
    if combination == "linear":
        return 1.0 - beta
    if combination == "euclidean":
        return math.sqrt(1.0 - beta * beta)
    raise ValueError(f"variante desconocida: {combination}")


def simulate_proper_ticks(beta: float, substrate_ticks: int, combination: str) -> int:
    """Simulacion discreta: cuantas actualizaciones internas completa un
    sistema que se mueve a velocidad beta durante `substrate_ticks` tics.

    El presupuesto se acumula tic a tic (acumulador tipo Bresenham); una
    actualizacion interna se completa cada vez que el acumulador alcanza 1.
    El tiempo propio EMERGE como recuento discreto, no se postula continuo.
    """
    rate = internal_rate(beta, combination)
    acc = 0.0
    internal = 0
    for _ in range(substrate_ticks):
        acc += rate
        if acc >= 1.0:
            internal += 1
            acc -= 1.0
    return internal


def measured_dilation(beta: float, substrate_ticks: int, combination: str) -> float:
    """Factor de dilatacion medido en la simulacion: tics sustrato / tics propios."""
    internal = simulate_proper_ticks(beta, substrate_ticks, combination)
    if internal == 0:
        return math.inf
    return substrate_ticks / internal


# --- Gravedad como densidad de tics ------------------------------------------

def tick_density(phi: float) -> float:
    """Densidad local de tics asociada al potencial gravitatorio phi (<0).

    En una region densa un sistema necesita mas tics del sustrato para la
    misma actualizacion interna. Identificacion de campo debil: d = -phi/c^2.
    """
    return -phi / (C * C)


def clock_rate_model(phi: float) -> float:
    """Tasa de reloj del modelo discreto: 1/(1+d) ~= 1 + phi/c^2 (campo debil)."""
    return 1.0 / (1.0 + tick_density(phi))


def clock_rate_gr(phi: float) -> float:
    """Tasa de reloj de la relatividad general (metrica de Schwarzschild,
    aproximacion estatica): sqrt(1 + 2*phi/c^2)."""
    return math.sqrt(1.0 + 2.0 * phi / (C * C))


@dataclass
class GPSBudget:
    """Desglose del adelanto diario de los relojes GPS respecto al suelo."""

    gravitational_us: float   # adelanto por menor densidad de tics en orbita
    kinematic_us: float       # atraso por gasto de presupuesto en velocidad
    net_us: float


def gps_daily_offset(combination: str = "euclidean") -> GPSBudget:
    """Reproduce el dato de Ashby (2003): ~+45.7 us/dia gravitatorio,
    ~-7.2 us/dia cinematico, neto ~+38.5 us/dia.

    Todo se calcula DESDE el modelo discreto (densidad de tics + reparto de
    presupuesto), no desde las formulas de la relatividad: la comparacion con
    el valor publicado es el test.
    """
    phi_surface = -GM_EARTH / R_EARTH
    phi_orbit = -GM_EARTH / R_GPS

    # Gravitatorio: cociente de tasas de reloj del modelo de densidad de tics.
    grav_ratio = clock_rate_model(phi_orbit) / clock_rate_model(phi_surface)
    gravitational = (grav_ratio - 1.0) * SECONDS_PER_DAY * 1e6

    # Cinematico: presupuesto gastado en la velocidad orbital.
    v_orbit = math.sqrt(GM_EARTH / R_GPS)
    beta = v_orbit / C
    kin_ratio = internal_rate(beta, combination)  # tasa interna del satelite
    kinematic = (kin_ratio - 1.0) * SECONDS_PER_DAY * 1e6

    return GPSBudget(
        gravitational_us=gravitational,
        kinematic_us=kinematic,
        net_us=gravitational + kinematic,
    )


# --- Invariancia de Lorentz cerca de Planck (prediccion fisica de P5) --------

def liv_verdict(model_scale_gev: float = E_PLANCK_GEV) -> dict:
    """Confronta la prediccion "desviaciones cerca de Planck" con las cotas
    experimentales de dispersion de fotones.

    Un sustrato discreto a la escala de Planck con correccion LINEAL en
    energia (v(E) ~= c(1 - E/E_QG) con E_QG ~ E_Planck) esta EXCLUIDO por
    GRB 090510. Una supresion CUADRATICA sigue siendo viable. El resultado
    restringe la forma que puede tomar P5, tal como pide la seccion 8.
    """
    linear_excluded = model_scale_gev < LIV_LINEAR_BOUND_GEV
    quadratic_excluded = model_scale_gev < LIV_QUADRATIC_BOUND_GEV
    return {
        "model_scale_gev": model_scale_gev,
        "linear_bound_gev": LIV_LINEAR_BOUND_GEV,
        "quadratic_bound_gev": LIV_QUADRATIC_BOUND_GEV,
        "linear_variant_excluded": linear_excluded,
        "quadratic_variant_excluded": quadratic_excluded,
    }
