"""El simulador que sostiene E7: si las puertas estan mal, E7 no dice nada."""

import math

import pytest

from bbu.qsim import State, max_entry_difference, reg_value, shannon_bits, to_openqasm2


def test_bell_pair_amplitudes():
    st = State(2).h(0).cx(0, 1)
    s = 1 / math.sqrt(2)
    assert set(st.amps) == {0b00, 0b11}
    assert all(abs(a - s) < 1e-15 for a in st.amps.values())


def test_hadamard_is_its_own_inverse_and_amplitudes_cancel():
    st = State(1).h(0).h(0)
    assert st.amps == {0: pytest.approx(1.0)}


def test_ry_and_phase_prepare_the_requested_state():
    theta, phi = 1.1, 0.7
    st = State(1).ry(0, theta).phase(0, phi)
    assert st.amps[0] == pytest.approx(math.cos(theta / 2))
    assert st.amps[1] == pytest.approx(complex(math.cos(phi), math.sin(phi)) * math.sin(theta / 2))


def test_oracle_is_reversible_xor():
    st = State(4)
    st.h(0).h(1)
    st.oracle(lambda x: (x + 1) % 4, [0, 1], [2, 3])
    for idx in st.amps:
        assert reg_value(idx, [2, 3]) == (reg_value(idx, [0, 1]) + 1) % 4
    st.oracle(lambda x: (x + 1) % 4, [0, 1], [2, 3])      # aplicarlo dos veces = identidad
    assert all(reg_value(i, [2, 3]) == 0 for i in st.amps)


def test_postselection_returns_born_probability_and_renormalises():
    st = State(2).h(0).cx(0, 1)
    assert st.postselect([0], 1) == pytest.approx(0.5)
    assert st.norm2() == pytest.approx(1.0)
    assert st.distribution([1]) == {1: pytest.approx(1.0)}


def test_impossible_postselection_is_exactly_zero():
    st = State(1)
    assert st.postselect([0], 1) == 0.0
    assert st.amps == {}


def test_reduced_density_of_half_a_bell_pair_is_maximally_mixed():
    rho = State(2).h(0).cx(0, 1).reduced_density([1])
    assert max_entry_difference(rho, [[0.5, 0], [0, 0.5]]) < 1e-15


def test_shannon_bits():
    assert shannon_bits({0: 0.5, 1: 0.5}) == pytest.approx(1.0)
    assert shannon_bits({3: 1.0}) == 0.0


def test_openqasm_export_and_its_limits():
    st = State(2).h(0).cx(0, 1)
    st.postselect([0], 0)
    text = to_openqasm2(st)
    assert text.startswith("OPENQASM 2.0;")
    assert "cx q[0],q[1];" in text and "c[0]=0" in text
    with pytest.raises(NotImplementedError):
        to_openqasm2(State(2).oracle(lambda x: x, [0], [1]))
    late = State(2).h(0)
    late.postselect([0], 0)
    late.x(1)
    with pytest.raises(NotImplementedError):
        to_openqasm2(late)
