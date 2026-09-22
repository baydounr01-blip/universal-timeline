"""bbu: Universo de Bloques Ramificados.

Implementacion ejecutable y testeable de los postulados P1-P12 del articulo
"Universo de Bloques Ramificados" (Baydoun Nabhan, 2026), con una bateria de
experimentos disenados para corroborar la coherencia interna del marco o
refutarla, y para confrontar sus predicciones fisicas con datos publicados.

Desde 0.2.0 el canal P6 tiene mecanismo: CTC postseleccionadas (`pctc`,
Lloyd et al. 2011) hacia el pasado y capsulas temporales (`timelock`,
Rivest-Shamir-Wagner 1996) hacia el futuro.
"""

__version__ = "0.2.0"

from .block import Block, CausalityError, ForkRuleViolation, PLANCK_TIME_S, TICKS_PER_SECOND
from .observer import Observer, RecordImmutabilityError
from .channel import (
    ConservedQuantity,
    ConservedQuantityError,
    InterBranchChannel,
    Message,
    NoCloningError,
    QuantumState,
)
from .ledger import BranchLedger, DoubleSpendError, UnknownCoinError, BTC_MAX_SUPPLY
from .returns import BranchReturn, ReturnClass
from .fixedpoint import Action, History, Protocol, is_fixed_point, resolve_history
from .signature import ComputeAuditor, ProofOfWorkResult
from .pctc import (
    bootstrap, closed_loop, grandfather, search_through_time,
    send_bits_to_past, send_bytes_to_past, send_qubit_to_past,
)
from .timelock import Capsule, CapsuleError, open_capsule, seal

__all__ = [
    "Block", "CausalityError", "ForkRuleViolation", "PLANCK_TIME_S", "TICKS_PER_SECOND",
    "Observer", "RecordImmutabilityError",
    "ConservedQuantity", "ConservedQuantityError", "InterBranchChannel",
    "Message", "NoCloningError", "QuantumState",
    "BranchLedger", "DoubleSpendError", "UnknownCoinError", "BTC_MAX_SUPPLY",
    "BranchReturn", "ReturnClass",
    "Action", "History", "Protocol", "is_fixed_point", "resolve_history",
    "ComputeAuditor", "ProofOfWorkResult",
    "bootstrap", "closed_loop", "grandfather", "search_through_time",
    "send_bits_to_past", "send_bytes_to_past", "send_qubit_to_past",
    "Capsule", "CapsuleError", "open_capsule", "seal",
]
