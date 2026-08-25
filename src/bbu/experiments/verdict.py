from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Outcome(Enum):
    CORROBORATED = "CORROBORADO"   # la afirmacion sobrevive al experimento
    REFUTED = "REFUTADO"           # la afirmacion falla en su propio modelo
    CONSTRAINED = "RESTRINGIDO"    # sobrevive solo en una variante restringida


@dataclass
class Verdict:
    claim: str                       # la afirmacion del articulo, citada
    postulates: str                  # postulados implicados
    outcome: Outcome
    evidence: dict = field(default_factory=dict)
    notes: str = ""

    def summary_line(self) -> str:
        return f"[{self.outcome.value:^12}] {self.postulates:<8} {self.claim}"
