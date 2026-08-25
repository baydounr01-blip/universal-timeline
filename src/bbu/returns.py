"""P10: regla de retorno. Invariantes de rama frente a variables de rama.

Solo tiene valor de retorno lo que no depende de la rama que lo calculo:

  * Invariantes de rama: teoremas, factorizaciones, disenos, salidas de
    programas ejecutados sobre datos que ya existian en t-1 (incluidos
    nonces validos para la siguiente plantilla de bloque del emisor).
    Propiedad clave: son VERIFICABLES en la rama de origen con datos de la
    rama de origen.

  * Variables de rama: predicciones sobre el futuro de la rama que las
    produjo. El manana de t' no es el manana de t; el propio gasto ya lo ha
    perturbado. No son verificables en origen mas que esperando el futuro de
    origen, y para entonces ya han fallado.

La distincion operativa que implementa este modulo: un retorno es invariante
si y solo si viene acompanado de un procedimiento de verificacion ejecutable
con datos que la rama de origen ya poseia en t-1.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Callable


class ReturnClass(Enum):
    BRANCH_INVARIANT = "invariante de rama"
    BRANCH_VARIABLE = "variable de rama"


@dataclass
class BranchReturn:
    """Un retorno del canal: bytes + (opcionalmente) su verificador local."""

    payload: bytes
    # Verificador que SOLO usa `origin_data`: datos que ya existian en t-1 en
    # la rama de origen. Si no hay verificador local, el retorno depende del
    # futuro de alguna rama y es una variable de rama.
    verifier: Callable[[bytes, dict], bool] | None = None

    def classify(self) -> ReturnClass:
        if self.verifier is None:
            return ReturnClass.BRANCH_VARIABLE
        return ReturnClass.BRANCH_INVARIANT

    def value_in_origin(self, origin_data: dict) -> bool:
        """Valor de retorno en la rama de origen.

        Invariante verificado -> True (vale). Todo lo demas -> False. Una
        'prediccion' no ejecuta nada aqui: su verificacion exigiria el futuro
        de la rama de origen, que no esta en origin_data.
        """
        if self.classify() is ReturnClass.BRANCH_VARIABLE:
            return False
        assert self.verifier is not None
        return self.verifier(self.payload, origin_data)


# --- Ejemplos canonicos del articulo -----------------------------------------

def factorization_return(n: int, p: int, q: int) -> BranchReturn:
    """Factorizar un numero que ya existia en t-1: invariante de rama."""

    def verify(payload: bytes, origin_data: dict) -> bool:
        a_s, b_s = payload.decode().split(",")
        a, b = int(a_s), int(b_s)
        return a * b == origin_data["n"] and a > 1 and b > 1

    return BranchReturn(payload=f"{p},{q}".encode(), verifier=verify)


def nonce_return(nonce: int) -> BranchReturn:
    """Un nonce valido para la siguiente plantilla de bloque del emisor:
    la plantilla existia en t-1, luego el nonce es un invariante de rama."""

    def verify(payload: bytes, origin_data: dict) -> bool:
        template: bytes = origin_data["block_template"]
        target: int = origin_data["target"]
        digest = hashlib.sha256(template + payload).digest()
        return int.from_bytes(digest, "big") < target

    return BranchReturn(payload=str(nonce).encode(), verifier=verify)


def price_prediction_return(predicted_price: float) -> BranchReturn:
    """'El precio manana sera X': variable de rama. Sin verificador local."""
    return BranchReturn(payload=str(predicted_price).encode(), verifier=None)


def find_nonce(template: bytes, target: int, max_tries: int = 1_000_000) -> int | None:
    """Trabajo que una rama hermana puede hacer y devolver (ver P12: el coste
    de este bucle es exactamente lo que mide la firma fuera de cadena)."""
    for nonce in range(max_tries):
        payload = str(nonce).encode()
        digest = hashlib.sha256(template + payload).digest()
        if int.from_bytes(digest, "big") < target:
            return nonce
    return None
