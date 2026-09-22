"""Mecanismo de P6: CTC postseleccionadas (Lloyd et al. 2011)."""

import math

import pytest

from bbu.pctc import (
    bootstrap,
    bootstrap_circuit,
    closed_loop,
    grandfather,
    grandfather_circuit,
    receiver_density,
    search_through_time,
    send_bits_to_past,
    send_bytes_to_past,
    send_qubit_to_past,
)
from bbu.qsim import max_entry_difference, to_openqasm2


@pytest.mark.parametrize("n", [1, 2, 3])
def test_p6_every_message_arrives_in_the_branch_where_the_loop_closes(n):
    for m in range(1 << n):
        run = send_bits_to_past(m, n)
        assert run.received_if_closed == {m: pytest.approx(1.0)}
        assert run.p_loop_closes == pytest.approx(4.0 ** -n)


def test_p6_bytes_travel_bit_by_bit_and_the_branch_measure_is_tiny():
    text, p = send_bytes_to_past(b"hola")
    assert text == b"hola"
    assert p == pytest.approx(4.0 ** -32)


def test_p6_message_must_fit():
    with pytest.raises(ValueError):
        send_bits_to_past(4, 2)


@pytest.mark.parametrize("theta,phi", [(0.3, 0.0), (math.pi / 2, math.pi / 2), (2.5, -1.9)])
def test_p6b_quantum_states_arrive_without_cloning(theta, phi):
    run = send_qubit_to_past(theta, phi)
    assert run.fidelity == pytest.approx(1.0)
    assert run.p_loop_closes == pytest.approx(0.25)
    # En (A, M) queda |00> sea cual sea psi: ninguna copia sobrevive en t1.
    assert run.residue[0][0] == pytest.approx(1.0)


def test_p6c_no_signaling_the_past_sees_the_same_noise_whatever_is_sent():
    before = receiver_density(None, 2)
    for m in range(4):
        assert max_entry_difference(before, receiver_density(m, 2)) < 1e-12
    assert max_entry_difference(before, [[0.25 if i == j else 0 for j in range(4)]
                                         for i in range(4)]) < 1e-12


def test_p6c_each_bell_branch_is_a_one_time_pad_keyed_in_the_future():
    run = send_bits_to_past(0b101, 3)
    assert len(run.branches) == 64
    for (_z, s), dist in run.branches.items():
        assert set(dist) == {0b101 ^ s}


def test_p6c_grandfather_paradox_has_zero_measure():
    for n in (1, 2, 3):
        run = grandfather(n)
        assert run.fixed_points == []
        assert run.p_loop_closes == 0.0


def test_p6c_bootstrap_closes_but_creates_no_information():
    run = bootstrap(3)
    assert run.p_loop_closes == pytest.approx(1 / 8)
    assert run.received_if_closed == {x: pytest.approx(1 / 8) for x in range(8)}


def test_p6c_only_fixed_points_survive_with_measure_k_over_n_squared():
    run = closed_loop(3, lambda x: (x * x) % 8, "cuadrado")
    assert run.fixed_points == [0, 1]
    assert run.p_loop_closes == pytest.approx(2 / 64)
    assert set(run.received_if_closed) == {0, 1}


def test_gate_level_circuits_match_the_oracle_versions():
    assert grandfather_circuit().norm2() == 0.0            # la rama no existe
    st = bootstrap_circuit(2)
    assert st.distribution([2, 3]) == {x: pytest.approx(0.25) for x in range(4)}
    assert "cx q[2],q[4];" in to_openqasm2(bootstrap_circuit(2))


def test_p10_search_through_time_only_returns_solutions_at_a_price():
    run = search_through_time(5, lambda x: x in (7, 19))
    assert run.solutions == [7, 19]
    assert run.mass_on_solutions == pytest.approx(1.0)
    assert run.p_loop_closes == pytest.approx(2 / 32 ** 2)
    assert run.expected_runs / run.brute_force_expected_trials == pytest.approx(32)


def test_p10_no_solution_means_nothing_comes_back():
    run = search_through_time(4, lambda x: False)
    assert run.p_loop_closes == 0.0
    assert math.isinf(run.expected_runs)
