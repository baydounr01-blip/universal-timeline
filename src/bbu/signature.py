"""P12: firma observable.

En cadena, el gasto ramificado no deja ninguna firma. Fuera de cadena deja
exactamente una: un agente que posee resultados cuyo coste de computo supera
el computo disponible en su rama. Es la unica prediccion falsable del marco
(seccion 8) y este modulo implementa su detector.

El detector es aplicable en el mundo real por el mismo procedimiento: (1)
acotar el computo accesible al agente; (2) estimar el coste de los
resultados que exhibe mediante verificacion (una prueba de trabajo es
autoacreditante: el nonce demuestra ~2^k intentos esperados); (3) declarar
exceso si (2) > (1) con margen estadistico.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field


@dataclass
class ProofOfWorkResult:
    """Un resultado con coste de computo verificable.

    Encontrar `nonce` tal que sha256(template+nonce) < target cuesta en media
    2^256 / target evaluaciones de hash. El resultado en si acredita el gasto.
    """

    template: bytes
    nonce: bytes
    target: int

    def is_valid(self) -> bool:
        digest = hashlib.sha256(self.template + self.nonce).digest()
        return int.from_bytes(digest, "big") < self.target

    @property
    def expected_cost_hashes(self) -> float:
        """Coste esperado en evaluaciones de hash para producir este resultado."""
        return float(2 ** 256) / float(self.target)


@dataclass
class ComputeAuditor:
    """Detector de la firma fuera de cadena.

    `branch_budget_hashes`: computo total disponible en la rama del agente
    (hardware x tiempo transcurrido). Los resultados validos que exhibe el
    agente acumulan coste acreditado; si el coste acreditado supera el
    presupuesto de la rama, hay firma.
    """

    branch_budget_hashes: float
    accredited_cost: float = 0.0
    results: list[ProofOfWorkResult] = field(default_factory=list)

    def submit(self, result: ProofOfWorkResult) -> bool:
        """Registra un resultado exhibido por el agente. Devuelve si es valido."""
        if not result.is_valid():
            return False
        self.results.append(result)
        self.accredited_cost += result.expected_cost_hashes
        return True

    @property
    def excess_ratio(self) -> float:
        """Coste acreditado / presupuesto de la rama."""
        if self.branch_budget_hashes <= 0:
            raise ValueError("el presupuesto de la rama debe ser positivo")
        return self.accredited_cost / self.branch_budget_hashes

    def signature_detected(self, margin: float = 3.0) -> bool:
        """Firma fuera de cadena: exceso con margen (por defecto 3x, para que
        la varianza de la prueba de trabajo no de falsos positivos)."""
        return self.excess_ratio > margin
