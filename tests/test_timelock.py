"""El canal hacia el futuro: capsulas RSW."""

import json
import random

import pytest

from bbu.timelock import (
    Capsule,
    CapsuleError,
    open_capsule,
    seal,
    sequential_squarings,
    unlock_with,
)


def sealed(message=b"para t0+T", t=5_000, seed=7):
    return seal(message, t, bits=256, rng=random.Random(seed))


def test_capsule_opens_after_exactly_t_squarings():
    capsule, report = sealed()
    assert open_capsule(capsule) == b"para t0+T"
    assert report.squarings_required_to_open == 5_000


@pytest.mark.parametrize("k", [0, 1, 2_500, 4_999, 5_001])
def test_capsule_does_not_open_with_the_wrong_number_of_ticks(k):
    capsule, _ = sealed()
    with pytest.raises(CapsuleError):
        unlock_with(capsule, sequential_squarings(capsule, k))


def test_sender_shortcut_is_logarithmic():
    _, report = sealed(t=100_000)
    assert report.shortcut_multiplications < 1_000


def test_capsule_survives_the_trip_as_json_and_carries_no_trapdoor():
    capsule, _ = sealed()
    text = capsule.to_json()
    assert set(json.loads(text)) == {"formato", "n", "a", "T", "sal", "cifrado", "etiqueta",
                                     "sellada", "cuadrados_por_segundo_al_sellar"}
    assert open_capsule(Capsule.from_json(text)) == b"para t0+T"


def test_tampering_is_detected():
    capsule, _ = sealed()
    flipped = bytes([capsule.ciphertext[0] ^ 1]) + capsule.ciphertext[1:]
    forged = Capsule(**{**capsule.__dict__, "ciphertext": flipped})
    with pytest.raises(CapsuleError):
        open_capsule(forged)


def test_two_capsules_of_the_same_message_differ():
    a, _ = sealed(seed=1)
    b, _ = sealed(seed=2)
    assert a.modulus != b.modulus and a.ciphertext != b.ciphertext


def test_unknown_format_is_rejected():
    with pytest.raises(CapsuleError):
        Capsule.from_json('{"formato": "otro"}')


def test_zero_ticks_is_not_a_capsule():
    with pytest.raises(ValueError):
        seal(b"x", 0, bits=256, rng=random.Random(0))
