"""P11: condicion de punto fijo; seccion 7 (alguien paga siempre)."""

from bbu.fixedpoint import (
    Action,
    Protocol,
    is_fixed_point,
    resolve_history,
    someone_always_pays,
)


def protocols():
    sym = Protocol(Action.PAY_AND_COMPUTE, work_units_per_branch=5,
                   cost_btc_per_branch=1_000_000.0)
    asym = Protocol(Action.DELEGATE, work_units_per_branch=5,
                    cost_btc_per_branch=1_000_000.0)
    return sym, asym


def test_p11_delegating_protocol_is_not_a_fixed_point():
    _, asym = protocols()
    assert not is_fixed_point(asym)


def test_p11_the_only_consistent_history_of_delegation_is_empty():
    _, asym = protocols()
    h = resolve_history(asym, branches=100)
    assert h.empty
    assert h.total_work_returned == 0
    assert h.total_btc_spent == 0.0


def test_p11_symmetric_protocol_is_a_fixed_point_with_return():
    sym, _ = protocols()
    assert is_fixed_point(sym)
    h = resolve_history(sym, branches=100)
    assert h.branches_that_paid == 100
    assert h.total_work_returned == 500


def test_p11_someone_always_pays():
    sym, asym = protocols()
    assert someone_always_pays(resolve_history(sym, 10))
    assert someone_always_pays(resolve_history(asym, 10))


def test_p11_no_free_lunch_return_scales_with_branches_that_pay():
    sym, _ = protocols()
    h10 = resolve_history(sym, 10)
    h1000 = resolve_history(sym, 1000)
    assert h1000.total_work_returned == 100 * h10.total_work_returned
    assert h1000.total_btc_spent == 100 * h10.total_btc_spent
