"""P5: relatividad emergente. Estos tests son la parte del repo que confronta
el marco con numeros publicados: si fallan, la seccion 2 del articulo cae."""

import math

import pytest

from bbu.relativity import (
    C,
    clock_rate_gr,
    clock_rate_model,
    gps_daily_offset,
    internal_rate,
    liv_verdict,
    lorentz_gamma,
    measured_dilation,
    simulate_proper_ticks,
)


def test_gamma_reference_values():
    assert math.isclose(lorentz_gamma(0.0), 1.0)
    assert math.isclose(lorentz_gamma(0.8), 1.0 / 0.6, rel_tol=1e-12)
    with pytest.raises(ValueError):
        lorentz_gamma(1.0)


def test_euclidean_budget_reproduces_lorentz_dilation():
    for beta in [0.1, 0.5, 0.9, 0.99]:
        gamma = lorentz_gamma(beta)
        measured = measured_dilation(beta, 2_000_000, "euclidean")
        assert abs(measured - gamma) / gamma < 1e-3


def test_linear_budget_is_refuted_by_lorentz():
    """La lectura ingenua del postulado (tasa = 1 - beta) NO reproduce la
    dilatacion relativista: queda refutada. Este test protege el resultado."""
    beta = 0.9
    gamma = lorentz_gamma(beta)                       # ~2.294
    measured = measured_dilation(beta, 2_000_000, "linear")  # ~10.0
    assert abs(measured - gamma) / gamma > 0.5


def test_at_rest_no_dilation_in_either_variant():
    for combination in ("linear", "euclidean"):
        assert simulate_proper_ticks(0.0, 1000, combination) == 1000


def test_proper_time_emerges_as_discrete_count():
    internal = simulate_proper_ticks(0.8, 1000, "euclidean")
    assert internal == int(1000 * internal_rate(0.8, "euclidean"))


def test_tick_density_matches_gr_in_weak_field():
    """Campo debil (Tierra, Sol): el modelo 1/(1+d) y la RG coinciden a
    primer orden en phi/c^2."""
    for phi in [-6.3e7, -1.9e9]:   # superficie terrestre, superficie solar
        assert math.isclose(clock_rate_model(phi), clock_rate_gr(phi),
                            rel_tol=1e-8)


def test_tick_density_diverges_from_gr_in_strong_field():
    """En campo fuerte las dos formulas difieren: el modelo es una heuristica
    (seccion 9), y este test documenta donde deja de valer."""
    phi_strong = -0.3 * C * C
    model = clock_rate_model(phi_strong)
    gr = clock_rate_gr(phi_strong)
    assert abs(model - gr) / gr > 0.1


def test_gps_daily_offset_matches_ashby_2003():
    budget = gps_daily_offset()
    assert 44.5 < budget.gravitational_us < 46.5      # publicado: ~ +45.7
    assert -7.7 < budget.kinematic_us < -6.7          # publicado: ~ -7.2
    assert 38.0 < budget.net_us < 39.0                # publicado: ~ +38.5


def test_liv_linear_variant_is_excluded_by_photon_bounds():
    v = liv_verdict()
    assert v["linear_variant_excluded"] is True
    assert v["quadratic_variant_excluded"] is False
