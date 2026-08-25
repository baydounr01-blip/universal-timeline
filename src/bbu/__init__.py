"""bbu: Universo de Bloques Ramificados.

Implementacion ejecutable y testeable de los postulados P1-P12 del articulo
"Universo de Bloques Ramificados" (Baydoun Nabhan, 2026), con una bateria de
experimentos disenados para corroborar la coherencia interna del marco o
refutarla, y para confrontar sus predicciones fisicas con datos publicados.
"""

__version__ = "0.1.0"

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

__all__ = [
    "Block", "CausalityError", "ForkRuleViolation", "PLANCK_TIME_S", "TICKS_PER_SECOND",
    "Observer", "RecordImmutabilityError",
    "ConservedQuantity", "ConservedQuantityError", "InterBranchChannel",
    "Message", "NoCloningError", "QuantumState",
    "BranchLedger", "DoubleSpendError", "UnknownCoinError", "BTC_MAX_SUPPLY",
    "BranchReturn", "ReturnClass",
    "Action", "History", "Protocol", "is_fixed_point", "resolve_history",
    "ComputeAuditor", "ProofOfWorkResult",
]
