"""P6: canal interbloque.

Un canal de mensajeria entre ramas sujeto a tres condiciones:

  (a) transporta informacion, no magnitudes conservadas;
  (b) por no clonacion, la informacion transportada es clasica;
  (c) autoconsistencia: un mensaje "hacia el pasado" nunca llega al ancestro
      del emisor; llega a una rama hermana nueva, identica al ancestro salvo
      por haber recibido el mensaje (la regla del fork, version en bloques
      del punto fijo de Deutsch 1991).

El canal es un POSTULADO sin mecanismo (seccion 9). Lo que este modulo hace
testeable es su logica interna: que las tres restricciones se cumplen por
construccion y que ninguna operacion del canal puede alterar la linea de
descendencia del emisor.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

from .block import Block, ForkRuleViolation


class NoCloningError(Exception):
    """P6b: un estado cuantico desconocido no puede copiarse ni transmitirse."""


class ConservedQuantityError(Exception):
    """P6a: el canal no transporta energia, materia ni objetos."""


@dataclass
class QuantumState:
    """Marcador de estado cuantico desconocido. Cualquier intento de enviarlo
    por el canal viola el teorema de no clonacion (Wootters y Zurek 1982)."""

    label: str

    def __deepcopy__(self, memo):
        raise NoCloningError(f"no se puede clonar el estado cuantico {self.label!r}")


@dataclass
class ConservedQuantity:
    """Marcador de magnitud conservada (energia, materia, monedas...)."""

    label: str
    amount: float


@dataclass
class Message:
    """Lo unico que cruza el canal: bytes clasicos."""

    payload: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.payload, bytes):
            raise TypeError("el canal solo acepta bytes clasicos (P6a/P6b)")


def _screen_payload(obj: object) -> bytes:
    """Rechaza todo lo que no sea informacion clasica."""
    if isinstance(obj, QuantumState):
        raise NoCloningError(
            f"P6b: el estado cuantico {obj.label!r} no puede cruzar el canal"
        )
    if isinstance(obj, ConservedQuantity):
        raise ConservedQuantityError(
            f"P6a: {obj.label!r} es una magnitud conservada; el canal solo "
            "transporta informacion"
        )
    if isinstance(obj, Message):
        return obj.payload
    if isinstance(obj, bytes):
        return obj
    raise ConservedQuantityError(
        f"P6a: el objeto {type(obj).__name__} no es informacion clasica "
        "serializada; el canal no transporta objetos"
    )


@dataclass
class SendReceipt:
    sibling: Block                 # la rama hermana creada por la regla del fork
    sender_lineage_before: str
    sender_lineage_after: str

    @property
    def sender_history_intact(self) -> bool:
        return self.sender_lineage_before == self.sender_lineage_after


@dataclass
class InterBranchChannel:
    """El canal. `fork_state` permite inyectar como se copia el estado del
    ancestro a la rama hermana (herencia automatica, P8)."""

    log: list[str] = field(default_factory=list)

    def send_to_past(self, sender: Block, target_tick: int, payload: object) -> SendReceipt:
        """Regla del fork (P6c).

        El mensaje NUNCA llega al ancestro del emisor: se crea una rama
        hermana bifurcada en el bloque padre del ancestro objetivo, identica
        a el salvo por haber recibido el mensaje. La linea de descendencia
        del emisor queda intacta (verificado y devuelto en el recibo).
        """
        data = _screen_payload(payload)
        before = sender.lineage_hash()

        ancestor = sender.ancestor_at(target_tick)
        if ancestor.parent is None:
            raise ForkRuleViolation(
                "no se puede bifurcar en el genesis: no hay bloque padre"
            )

        # Herencia automatica (P8): la rama hermana nace con una copia exacta
        # del estado del ancestro...
        inherited_state = copy.deepcopy(ancestor.state)
        # ...salvo por una diferencia: ha recibido el mensaje (P6c). Esa
        # diferencia es el comienzo de la divergencia obligatoria (P9).
        inherited_state["_inbox"] = list(inherited_state.get("_inbox", [])) + [data.hex()]

        siblings = ancestor.parent.branch(
            [(f"msg-{len(self.log)}", inherited_state, 1.0 + 0j)]
        )
        sibling = siblings[0]
        self.log.append(f"send tick={target_tick} -> {sibling.branch_id}")

        after = sender.lineage_hash()
        receipt = SendReceipt(
            sibling=sibling,
            sender_lineage_before=before,
            sender_lineage_after=after,
        )
        # Invariante duro del postulado: si esto fallara, el canal habria
        # cambiado el pasado del emisor, cosa que P6c prohibe.
        assert receipt.sender_history_intact, "la regla del fork ha fallado"
        return receipt

    def receive_from_branch(self, payload: object) -> bytes:
        """Lo unico que puede volver de una rama: bytes clasicos (P6a, P6b).

        La clasificacion invariante/variable de rama (P10) se aplica en el
        modulo `returns`; aqui solo se filtra la naturaleza fisica del envio.
        """
        return _screen_payload(payload)
