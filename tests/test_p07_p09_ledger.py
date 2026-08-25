"""P7 (propiedad indexada por rama), P8 (herencia automatica),
P9 (divergencia obligatoria)."""

import pytest

from bbu.ledger import (
    BranchLedger,
    DoubleSpendError,
    UnknownCoinError,
    divergence_time,
    logistic_divergence,
)
from bbu.merkle import build_chain, merkle_root, sha256d


def ledger_with_million():
    ledger = BranchLedger(branch_id="t")
    ledger.utxo["utxo:1M"] = True
    ledger.utxo["utxo:otra"] = True
    return ledger


# ------------------------------------------------------------------ P7

def test_p7_spend_is_a_property_of_coin_and_branch():
    origin = ledger_with_million()
    sibling = origin.inherit("t'")
    sibling.spend("utxo:1M")
    assert not sibling.is_unspent("utxo:1M")   # gastado en (u, t')
    assert origin.is_unspent("utxo:1M")        # sin gastar en (u, t)


def test_p7_double_spend_within_a_branch_is_forbidden():
    ledger = ledger_with_million()
    ledger.spend("utxo:1M")
    with pytest.raises(DoubleSpendError):
        ledger.spend("utxo:1M")


def test_p7_across_branches_there_is_nothing_to_forbid():
    origin = ledger_with_million()
    for i in range(100):
        sibling = origin.inherit(f"t'/{i}")
        sibling.spend("utxo:1M")   # el mismo utxo, cien ramas, cien gastos
    assert origin.is_unspent("utxo:1M")


def test_p7_corollary_no_spend_in_another_branch_can_be_noticed():
    """'No es que no se note: es que no puede notarse': el gasto en la rama
    hermana no altera ni un bit del estado observable de la rama de origen."""
    origin = ledger_with_million()
    before = origin.snapshot_hash()
    sibling = origin.inherit("t'")
    sibling.spend("utxo:1M")
    sibling.spend("utxo:otra")
    assert origin.snapshot_hash() == before
    assert origin.history == sibling.history[: len(origin.history)]


def test_p7_coins_from_another_branch_do_not_exist_here():
    origin = BranchLedger(branch_id="t")
    with pytest.raises(UnknownCoinError):
        origin.spend("utxo:minado-en-t'")


# ------------------------------------------------------------------ P8

def test_p8_sibling_inherits_the_complete_state():
    origin = ledger_with_million()
    origin.history.append("bloque:800000")
    sibling = origin.inherit("t'")
    assert sibling.utxo == origin.utxo
    assert sibling.history == origin.history
    assert sibling.snapshot_hash() == origin.snapshot_hash()  # mismos hashes


def test_p8_inheritance_is_a_copy_not_a_view():
    origin = ledger_with_million()
    sibling = origin.inherit("t'")
    sibling.spend("utxo:1M")
    assert origin.is_unspent("utxo:1M")


def test_p8_same_block_with_other_coinbase_does_not_exist():
    """Minar 'el mismo bloque' con otra direccion en la coinbase cambia la
    raiz de Merkle, el hash del bloque y todos los posteriores."""
    prev = sha256d(b"cadena-previa")
    original = build_chain(prev, [[b"coinbase->A", b"tx"], [b"cb2"], [b"cb3"]])
    altered = build_chain(prev, [[b"coinbase->B", b"tx"], [b"cb2"], [b"cb3"]])
    assert original[0].merkle != altered[0].merkle
    for a, b in zip(original, altered):
        assert a.block_hash != b.block_hash   # la alteracion se propaga a TODOS


def test_p8_merkle_root_is_deterministic_and_order_sensitive():
    txs = [sha256d(b"a"), sha256d(b"b"), sha256d(b"c")]
    assert merkle_root(txs) == merkle_root(list(txs))
    assert merkle_root(txs) != merkle_root(list(reversed(txs)))
    with pytest.raises(ValueError):
        merkle_root([])


# ------------------------------------------------------------------ P9

def test_p9_divergence_grows_from_microscopic_perturbation():
    dists = logistic_divergence(x0=0.4, perturbation=1e-9, steps=80)
    assert dists[0] == pytest.approx(1e-9)
    assert max(dists) > 0.1   # la perturbacion del gasto se hace macroscopica


def test_p9_bigger_spend_diverges_faster():
    small = divergence_time(x0=0.4, perturbation=1e-12)
    big = divergence_time(x0=0.4, perturbation=1e-3)
    assert big < small


def test_p9_divergence_is_permanent_not_transient():
    """La rama no vuelve a parecerse de forma estable al original: pasado el
    tiempo de divergencia, la distancia media se mantiene macroscopica."""
    dists = logistic_divergence(x0=0.4, perturbation=1e-9, steps=500)
    t_div = divergence_time(x0=0.4, perturbation=1e-9)
    tail = dists[t_div:]
    assert sum(tail) / len(tail) > 0.05
