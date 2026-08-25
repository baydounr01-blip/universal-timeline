"""P1 (tiempo discreto), P2 (enlace = causalidad), P3 (ramificacion)."""

import math

import pytest

from bbu.block import (
    Block,
    CausalityError,
    PLANCK_TIME_S,
    TICKS_PER_SECOND,
)


def make_line(n=5):
    b = Block(tick=0, branch_id="raiz", state={"n": 0})
    blocks = [b]
    for i in range(1, n):
        b = b.extend({"n": i})
        blocks.append(b)
    return blocks


# ------------------------------------------------------------------ P1

def test_p1_ticks_are_integers():
    blocks = make_line()
    assert [b.tick for b in blocks] == [0, 1, 2, 3, 4]


def test_p1_non_consecutive_tick_is_a_causality_error():
    genesis = Block(tick=0, branch_id="raiz", state={})
    with pytest.raises(CausalityError):
        Block(tick=5, branch_id="raiz", state={}, parent=genesis)


def test_p1_a_second_groups_about_1e43_planck_ticks():
    assert math.isclose(PLANCK_TIME_S, 5.391247e-44)
    assert 1e43 < TICKS_PER_SECOND < 2e43


# ------------------------------------------------------------------ P2

def test_p2_every_previous_instant_is_an_ancestor():
    blocks = make_line(6)
    present = blocks[-1]
    for t in range(6):
        assert present.ancestor_at(t) is blocks[t]
        assert blocks[t].is_ancestor_of(present)


def test_p2_chain_verifies_and_detects_ancestor_tampering():
    blocks = make_line(4)
    present = blocks[-1]
    assert present.verify_chain()
    blocks[1].state["n"] = 999   # alterar un ancestro rompe el enlace causal
    assert not present.verify_chain()


def test_p2_the_future_is_not_an_ancestor():
    blocks = make_line(3)
    with pytest.raises(CausalityError):
        blocks[0].ancestor_at(2)


# ------------------------------------------------------------------ P3

def test_p3_branching_requires_normalized_amplitudes():
    genesis = Block(tick=0, branch_id="raiz", state={})
    with pytest.raises(ValueError):
        genesis.branch([("a", {}, 1.0 + 0j), ("b", {}, 1.0 + 0j)])


def test_p3_fan_of_successors_with_amplitudes():
    genesis = Block(tick=0, branch_id="raiz", state={})
    amp = 1.0 / math.sqrt(2.0)
    t, t_prime = genesis.branch([("t", {"x": 1}, amp), ("t'", {"x": 2}, amp)])
    assert genesis.children == [t, t_prime]
    assert math.isclose(t.born_probability(), 0.5)


def test_p3_sibling_branches_share_ancestors_never_descendants():
    genesis = Block(tick=0, branch_id="raiz", state={})
    amp = 1.0 / math.sqrt(2.0)
    t, t_prime = genesis.branch([("t", {}, amp), ("t'", {}, amp)])
    t2 = t.extend({})
    tp2 = t_prime.extend({})
    assert t2.is_sibling_branch_of(tp2)
    assert t2.common_ancestor(tp2) is genesis
    descendants_of_t2 = {id(t2)}
    assert not any(id(b) in descendants_of_t2 for b in tp2.lineage())


def test_p3_an_observer_lives_in_a_single_line_of_descent():
    blocks = make_line(5)
    lineage = blocks[-1].lineage()
    assert lineage == blocks
    for a, b in zip(lineage, lineage[1:]):
        assert b.parent is a
