"""P6: canal interbloque -- solo informacion (a), solo clasica (b), regla del
fork (c)."""

import copy

import pytest

from bbu.block import Block, ForkRuleViolation
from bbu.channel import (
    ConservedQuantity,
    ConservedQuantityError,
    InterBranchChannel,
    Message,
    NoCloningError,
    QuantumState,
)


def universe():
    genesis = Block(tick=0, branch_id="raiz", state={})
    t1 = genesis.extend({"epoch": "t-1"})
    t2 = t1.extend({"epoch": "t"})
    return genesis, t1, t2


# ------------------------------------------------------------------ P6a

def test_p6a_conserved_quantities_cannot_cross():
    _, _, t2 = universe()
    channel = InterBranchChannel()
    with pytest.raises(ConservedQuantityError):
        channel.send_to_past(t2, 1, ConservedQuantity("1M BTC", 1_000_000.0))
    with pytest.raises(ConservedQuantityError):
        channel.receive_from_branch(ConservedQuantity("energia", 3.14))


def test_p6a_arbitrary_objects_are_not_information():
    _, _, t2 = universe()
    channel = InterBranchChannel()
    with pytest.raises(ConservedQuantityError):
        channel.send_to_past(t2, 1, {"objeto": "no serializado"})


# ------------------------------------------------------------------ P6b

def test_p6b_quantum_states_cannot_cross_no_cloning():
    _, _, t2 = universe()
    channel = InterBranchChannel()
    psi = QuantumState("psi-desconocido")
    with pytest.raises(NoCloningError):
        channel.send_to_past(t2, 1, psi)
    with pytest.raises(NoCloningError):
        channel.receive_from_branch(psi)


def test_p6b_quantum_states_refuse_deep_copy():
    with pytest.raises(NoCloningError):
        copy.deepcopy(QuantumState("psi"))


def test_p6b_classical_bytes_do_cross():
    channel = InterBranchChannel()
    assert channel.receive_from_branch(b"teorema") == b"teorema"
    assert channel.receive_from_branch(Message(b"nonce=42")) == b"nonce=42"


# ------------------------------------------------------------------ P6c

def test_p6c_message_reaches_a_sibling_never_the_ancestor():
    _, t1, t2 = universe()
    channel = InterBranchChannel()
    receipt = channel.send_to_past(t2, target_tick=1, payload=b"hola pasado")
    sibling = receipt.sibling
    assert sibling is not t1
    assert sibling.tick == t1.tick
    assert sibling.is_sibling_branch_of(t2)
    assert not sibling.is_ancestor_of(t2)


def test_p6c_sender_history_is_never_altered():
    _, _, t2 = universe()
    before = t2.lineage_hash()
    channel = InterBranchChannel()
    for i in range(20):
        receipt = channel.send_to_past(t2, 1, f"mensaje {i}".encode())
        assert receipt.sender_history_intact
    assert t2.lineage_hash() == before
    assert t2.verify_chain()


def test_p6c_sibling_is_identical_except_for_the_message():
    _, t1, t2 = universe()
    channel = InterBranchChannel()
    receipt = channel.send_to_past(t2, 1, b"m")
    state = dict(receipt.sibling.state)
    inbox = state.pop("_inbox")
    assert state == t1.state          # identica al ancestro...
    assert inbox == [b"m".hex()]      # ...salvo por haber recibido el mensaje


def test_p6c_cannot_fork_at_genesis():
    _, _, t2 = universe()
    channel = InterBranchChannel()
    with pytest.raises(ForkRuleViolation):
        channel.send_to_past(t2, 0, b"antes del principio")


def test_p6c_each_message_creates_a_new_branch():
    _, _, t2 = universe()
    channel = InterBranchChannel()
    ids = {channel.send_to_past(t2, 1, b"x").sibling.branch_id for _ in range(10)}
    assert len(ids) == 10
