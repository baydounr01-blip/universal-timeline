"""P12: la firma fuera de cadena y su detector."""

import pytest

from bbu.returns import find_nonce
from bbu.signature import ComputeAuditor, ProofOfWorkResult

BITS = 14
TARGET = 2 ** (256 - BITS)


def mine(template: bytes) -> ProofOfWorkResult:
    nonce = find_nonce(template, TARGET, max_tries=5_000_000)
    assert nonce is not None
    return ProofOfWorkResult(template, str(nonce).encode(), TARGET)


def test_p12_valid_pow_accredits_its_expected_cost():
    result = mine(b"t0")
    assert result.is_valid()
    assert result.expected_cost_hashes == pytest.approx(2 ** BITS)


def test_p12_invalid_results_accredit_nothing():
    auditor = ComputeAuditor(branch_budget_hashes=1e6)
    fake = ProofOfWorkResult(b"t0", b"nonce-falso", target=1)  # imposible
    assert not auditor.submit(fake)
    assert auditor.accredited_cost == 0.0


def test_p12_agent_within_budget_does_not_trigger_detector():
    auditor = ComputeAuditor(branch_budget_hashes=4.0 * 2 ** BITS)
    auditor.submit(mine(b"t0"))
    assert not auditor.signature_detected()


def test_p12_compute_excess_triggers_detector():
    auditor = ComputeAuditor(branch_budget_hashes=2.0 * 2 ** BITS)
    for i in range(10):   # resultados de 10 'ramas hermanas'
        auditor.submit(mine(f"t{i}".encode()))
    assert auditor.excess_ratio > 3.0
    assert auditor.signature_detected()


def test_p12_budget_must_be_positive():
    auditor = ComputeAuditor(branch_budget_hashes=0.0)
    with pytest.raises(ValueError):
        _ = auditor.excess_ratio
