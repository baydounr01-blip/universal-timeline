"""P11: condicion de punto fijo (Deutsch 1991).

El mensaje llega a una rama donde una copia del emisor lo recibe. Para que
algo regrese, esa copia tiene que ejecutar el plan y pagar. La copia ES el
emisor en t-1, con sus mismos valores: ejecutara exactamente lo que el
emisor ejecutaria al recibir el mensaje.

Consecuencia: un protocolo asimetrico ("yo conservo, tu pagas / delega en
tus sub-ramas") no es un punto fijo: cada copia delega, nadie paga, nadie
computa y la unica historia consistente es la vacia. Solo un protocolo
simetrico (cada rama paga y computa) produce retorno.

La cota de Aaronson y Watrous (2009) --CTCs deutschianas = PSPACE-- acota lo
que puede obtenerse encontrando estos puntos fijos: mucho, pero no cualquier
cosa. Aqui se refleja con un limite de profundidad de recursion: el esquema
no da acceso a computo ilimitado gratis, da acceso al computo que las ramas
consistentes efectivamente pagan.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Action(Enum):
    PAY_AND_COMPUTE = "paga y computa su parte"
    DELEGATE = "conserva sus monedas y delega en sus sub-ramas"


@dataclass(frozen=True)
class Protocol:
    """Un protocolo es la regla de decision que viaja en el mensaje.

    `action` es lo que hace quien lo recibe. Por P11, quien lo recibe es una
    copia del emisor: si el emisor no ejecutaria la accion al recibir el
    mensaje, la copia tampoco -- eso es exactamente lo que se comprueba en
    `is_fixed_point`.
    """

    action: Action
    work_units_per_branch: int   # computo que aporta cada rama que paga
    cost_btc_per_branch: float   # lo que paga cada rama que ejecuta


@dataclass
class History:
    """Una historia consistente: quien pago, quien computo, que regreso."""

    branches_that_paid: int
    total_work_returned: int
    total_btc_spent: float

    @property
    def empty(self) -> bool:
        return self.branches_that_paid == 0


def is_fixed_point(protocol: Protocol) -> bool:
    """Un protocolo es punto fijo si la copia (= el emisor en t-1) lo
    ejecutaria al recibirlo. DELEGATE nunca lo es: el emisor que envia
    DELEGATE esta revelando que el, al recibirlo, tampoco pagaria."""
    return protocol.action is Action.PAY_AND_COMPUTE


def resolve_history(protocol: Protocol, branches: int, depth: int = 1,
                    max_depth: int = 64) -> History:
    """Itera el mapa de Deutsch hasta la unica historia autoconsistente.

    `branches` es el numero de mensajes enviados (una rama hermana por
    mensaje, P6c). `max_depth` refleja la cota PSPACE: la recursion de
    sub-ramas es finita, no un pozo infinito de computo gratis.
    """
    if depth > max_depth:
        # Regreso infinito: ninguna rama de profundidad finita ejecuta nada.
        return History(0, 0, 0.0)

    if protocol.action is Action.DELEGATE:
        # Cada copia razona igual que el emisor: tambien delega. Nadie paga.
        # La unica historia consistente es la vacia.
        sub = resolve_history(protocol, branches, depth + 1, max_depth)
        assert sub.empty, "una copia habria hecho lo que el emisor no haria"
        return History(0, 0, 0.0)

    # PAY_AND_COMPUTE: cada rama paga su parte, computa y recibe de sus
    # sub-ramas lo mismo que ella entrega hacia arriba (protocolo simetrico).
    return History(
        branches_that_paid=branches,
        total_work_returned=branches * protocol.work_units_per_branch,
        total_btc_spent=branches * protocol.cost_btc_per_branch,
    )


def someone_always_pays(history: History) -> bool:
    """Seccion 7: si algo regreso, alguien pago. No hay retorno gratis."""
    return history.total_work_returned == 0 or history.total_btc_spent > 0
