"""P10: regla de retorno -- invariantes de rama si, variables de rama no."""

import hashlib

from bbu.returns import (
    BranchReturn,
    ReturnClass,
    factorization_return,
    find_nonce,
    nonce_return,
    price_prediction_return,
)


def test_p10_factorization_is_branch_invariant_and_verifies_in_origin():
    n = 101 * 103
    ret = factorization_return(n, 101, 103)
    assert ret.classify() is ReturnClass.BRANCH_INVARIANT
    assert ret.value_in_origin({"n": n}) is True


def test_p10_wrong_factorization_has_no_value():
    ret = factorization_return(101 * 103, 7, 11)
    assert ret.value_in_origin({"n": 101 * 103}) is False


def test_p10_price_prediction_is_branch_variable_with_zero_return_value():
    ret = price_prediction_return(1_234_567.89)
    assert ret.classify() is ReturnClass.BRANCH_VARIABLE
    assert ret.value_in_origin({"n": 42}) is False


def test_p10_nonce_for_senders_template_is_branch_invariant():
    """El ejemplo del articulo: un nonce valido para la siguiente plantilla
    de bloque de la cadena del emisor. La plantilla existia en t-1."""
    template = b"plantilla-del-emisor"
    target = 2 ** (256 - 12)
    nonce = find_nonce(template, target)
    assert nonce is not None
    ret = nonce_return(nonce)
    assert ret.classify() is ReturnClass.BRANCH_INVARIANT
    assert ret.value_in_origin({"block_template": template, "target": target})


def test_p10_invalid_nonce_has_no_value():
    template = b"plantilla-del-emisor"
    target = 2 ** (256 - 12)
    bad = 0
    digest = hashlib.sha256(template + str(bad).encode()).digest()
    assume_bad = int.from_bytes(digest, "big") >= target
    if assume_bad:  # (probabilidad ~1 - 2^-12)
        assert not nonce_return(bad).value_in_origin(
            {"block_template": template, "target": target}
        )


def test_p10_a_return_without_local_verifier_never_has_value():
    ret = BranchReturn(payload=b"el hash del bloque 900001 sera ...")
    assert ret.classify() is ReturnClass.BRANCH_VARIABLE
    assert ret.value_in_origin({}) is False
