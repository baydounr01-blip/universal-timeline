"""E8 -- El canal hacia el futuro: capsula temporal RSW (P2, P5).

Afirmacion contrastada: el sistema puede comunicarse hacia delante en el
tiempo con una garantia fisica y no solo de custodia -- el mensaje se
obtiene al completar la cadena de T cuadrados secuenciales, y no con un tic
menos; el emisor, con la trampilla, lo sella en ~log T operaciones.

Lo que este experimento NO demuestra (ni puede): que no exista un atajo sin
factorizar el modulo. Eso es la conjetura de secuencialidad de Rivest,
Shamir y Wagner (1996), abierta y no refutada.

Como refutar esto desde aqui: abrir la capsula de `run` con menos de T
cuadrados, o recuperar el mensaje a partir de su JSON sin hacerlos.
"""

from __future__ import annotations

import random

from ..timelock import Capsule, CapsuleError, seal, sequential_squarings, unlock_with
from .verdict import Outcome, Verdict


def _opens_with(capsule: Capsule, squarings: int) -> bool:
    try:
        unlock_with(capsule, sequential_squarings(capsule, squarings))
        return True
    except CapsuleError:
        return False


def run(squarings: int = 20_000, bits: int = 512, seed: int = 2026) -> Verdict:
    message = "mensaje sellado en t0 para quien llegue a t0+T".encode()
    capsule, report = seal(message, squarings, bits=bits, rng=random.Random(seed))
    travelled = Capsule.from_json(capsule.to_json())      # lo que llega al futuro

    opened = unlock_with(travelled, sequential_squarings(travelled))
    early = [squarings - 1, squarings // 2, 0]
    fields = travelled.to_json()
    checks = {
        "con_T_tics_se_lee_el_mensaje": opened == message,
        "con_un_tic_menos_no_abre": not _opens_with(travelled, squarings - 1),
        "a_mitad_de_camino_no_abre": not any(_opens_with(travelled, k) for k in early),
        "la_capsula_no_lleva_la_trampilla": all(
            key not in fields for key in ('"p"', '"q"', '"phi"')),
        "el_emisor_sella_en_log_T": report.shortcut_multiplications < squarings / 10,
    }
    ok = all(checks.values())
    return Verdict(
        claim="hacia el futuro el canal funciona hoy: el mensaje se lee tras "
              "exactamente T tics secuenciales, ni uno menos",
        postulates="P2,P5",
        outcome=Outcome.CORROBORATED if ok else Outcome.REFUTED,
        evidence={
            **checks,
            "tics_T": squarings,
            "multiplicaciones_del_emisor_(cota)": report.shortcut_multiplications,
            "bits_del_modulo": capsule.modulus.bit_length(),
        },
        notes="la capsula mide tiempo propio del que abre (tics de computo), no "
              "segundos: LCS35, pensado para 35 anos, se abrio en ~3.5 (2019) "
              "por cuadrados secuenciales, conforme a la conjetura RSW",
    )
