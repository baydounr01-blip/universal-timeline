"""Experimentos falsables del Universo de Bloques Ramificados.

Cada experimento devuelve un `Verdict` con la afirmacion contrastada, el
resultado (CORROBORADO / REFUTADO / RESTRINGIDO) y la evidencia numerica.
`python -m bbu verify` los ejecuta todos y falla (exit code != 0) si alguna
afirmacion del articulo resulta refutada por su propia implementacion.
"""

from .verdict import Outcome, Verdict

__all__ = ["Outcome", "Verdict"]
