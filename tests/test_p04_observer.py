"""P4: consenso = decoherencia; no hay rama privilegiada."""

import math

import pytest

import bbu
from bbu.block import Block
from bbu.observer import Observer, RecordImmutabilityError


def split_universe():
    genesis = Block(tick=0, branch_id="raiz", state={})
    amp = 1.0 / math.sqrt(2.0)
    t, t_prime = genesis.branch([("t", {"r": "a"}, amp), ("t'", {"r": "b"}, amp)])
    return genesis, t, t_prime


def test_p4_each_observer_holds_their_own_branch_as_real():
    genesis, t, t_prime = split_universe()
    alice, bob = Observer("alice"), Observer("bob")
    alice.decohere(genesis); alice.decohere(t)
    bob.decohere(genesis); bob.decohere(t_prime)
    assert alice.considers_real(t) and not alice.considers_real(t_prime)
    assert bob.considers_real(t_prime) and not bob.considers_real(t)


def test_p4_decohered_record_cannot_be_rewritten_to_a_sibling():
    genesis, t, t_prime = split_universe()
    alice = Observer("alice")
    alice.decohere(genesis); alice.decohere(t)
    with pytest.raises(RecordImmutabilityError):
        alice.decohere(t_prime)


def test_p4_no_global_real_branch_function_exists():
    """La ausencia de una nocion global de 'rama real' es parte del postulado:
    el paquete no exporta nada que la implemente."""
    forbidden = [name for name in dir(bbu)
                 if "real" in name.lower() or "canonical" in name.lower()]
    assert forbidden == []


def test_p4_record_grows_monotonically_and_is_immutable():
    genesis, t, _ = split_universe()
    alice = Observer("alice")
    alice.decohere(genesis)
    r1 = alice.record
    alice.decohere(t)
    r2 = alice.record
    assert r2[: len(r1)] == r1  # el registro solo crece; nunca se reescribe
