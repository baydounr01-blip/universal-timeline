"""La bateria de falsacion completa: cada experimento debe arrojar el
veredicto que el articulo declara. Un REFUTADO inesperado = el articulo
contradice su propio modelo, y este test lo hace visible en CI."""

from bbu.experiments.runner import EXPECTED, run_all
from bbu.experiments.verdict import Outcome


def test_full_falsification_battery_matches_declared_outcomes():
    verdicts = run_all()
    assert set(verdicts) == set(EXPECTED)
    mismatches = {
        key: (verdict.outcome.value, EXPECTED[key].value)
        for key, verdict in verdicts.items()
        if verdict.outcome != EXPECTED[key]
    }
    assert mismatches == {}


def test_no_claim_is_unfalsifiable():
    """Cada experimento tiene al menos un camino que llevaria a REFUTADO:
    los veredictos se calculan, no se declaran. (Humo: comprobamos que la
    evidencia numerica existe y no esta vacia.)"""
    for key, verdict in run_all().items():
        assert verdict.evidence, f"{key} no aporta evidencia numerica"
        assert verdict.outcome in (Outcome.CORROBORATED, Outcome.CONSTRAINED,
                                   Outcome.REFUTED)
