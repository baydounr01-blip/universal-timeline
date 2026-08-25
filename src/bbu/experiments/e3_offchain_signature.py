"""E3 -- "Hay firma fuera de cadena" (P12; seccion 8).

Afirmacion contrastada: si el canal existe y alguien lo usa, existira un
agente que posee resultados cuyo coste de computo supera el computo
disponible en su rama, y ese exceso es detectable. Y su contrapartida: un
agente SIN canal no puede disparar el detector (si pudiera, el detector no
seria una firma de nada).

Procedimiento: dos agentes con el mismo presupuesto de computo en su rama.
El agente A (sin canal) solo exhibe el trabajo que su presupuesto permite.
El agente B (con canal) recibe de m ramas hermanas trabajo verificable
--pruebas de trabajo reales, computadas de verdad en este proceso, jugando
cada una el papel de una rama-- y lo exhibe todo. El detector debe: no
disparar con A, disparar con B.
"""

from __future__ import annotations

from ..returns import find_nonce
from ..signature import ComputeAuditor, ProofOfWorkResult
from .verdict import Outcome, Verdict

# Objetivo modesto para que el experimento corra en CI: ~2^18 hashes por
# resultado en media (target = 2^256 / 2^18).
DIFFICULTY_BITS = 18
TARGET = 2 ** (256 - DIFFICULTY_BITS)


def _mine(template: bytes) -> ProofOfWorkResult:
    nonce = find_nonce(template, TARGET, max_tries=50_000_000)
    assert nonce is not None, "no se encontro nonce; subir max_tries"
    return ProofOfWorkResult(template=template, nonce=str(nonce).encode(), target=TARGET)


def run(sibling_branches: int = 12) -> Verdict:
    # Presupuesto de la rama: computo para ~2 resultados de esta dificultad.
    branch_budget = 2.0 * (2 ** DIFFICULTY_BITS)

    # Agente A: sin canal. Exhibe lo que su presupuesto da de si (1 resultado).
    honest = ComputeAuditor(branch_budget_hashes=branch_budget)
    honest.submit(_mine(b"plantilla-del-emisor:0"))

    # Agente B: con canal. m ramas hermanas computan cada una su resultado
    # (aqui: computados realmente, uno por rama simulada) y lo devuelven como
    # invariante de rama (P10). B exhibe la suma.
    channel_user = ComputeAuditor(branch_budget_hashes=branch_budget)
    for i in range(sibling_branches):
        channel_user.submit(_mine(f"plantilla-del-emisor:{i}".encode()))

    honest_flagged = honest.signature_detected()
    channel_flagged = channel_user.signature_detected()

    corroborated = (not honest_flagged) and channel_flagged
    return Verdict(
        claim="el uso del canal deja una firma medible: computo acreditado > computo de la rama",
        postulates="P12",
        outcome=Outcome.CORROBORATED if corroborated else Outcome.REFUTED,
        evidence={
            "presupuesto_rama_hashes": branch_budget,
            "exceso_agente_sin_canal": round(honest.excess_ratio, 2),
            "exceso_agente_con_canal": round(channel_user.excess_ratio, 2),
            "detector_dispara_sin_canal": honest_flagged,
            "detector_dispara_con_canal": channel_flagged,
            "ramas_hermanas": sibling_branches,
        },
        notes="la ausencia sostenida de este exceso en el mundo real es "
              "evidencia contra la existencia del canal (seccion 8)",
    )
