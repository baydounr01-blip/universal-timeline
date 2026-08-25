"""Soporte de P8: raiz de Merkle y cabecera de bloque al estilo Bitcoin.

P8 afirma: cualquier intento de reconstruir "el mismo bloque" con cambios
--por ejemplo, minar con otra direccion en la transaccion coinbase-- altera
la raiz de Merkle, con ella el hash del bloque y con el todos los bloques
posteriores. Este modulo implementa lo minimo para que esa afirmacion sea un
test y no una frase: arbol de Merkle sobre SHA-256d y encadenado de
cabeceras.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


def sha256d(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def merkle_root(tx_hashes: list[bytes]) -> bytes:
    """Raiz de Merkle al estilo Bitcoin (duplica el ultimo nodo si es impar)."""
    if not tx_hashes:
        raise ValueError("un bloque debe contener al menos la coinbase")
    level = list(tx_hashes)
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        level = [sha256d(level[i] + level[i + 1]) for i in range(0, len(level), 2)]
    return level[0]


@dataclass(frozen=True)
class LedgerBlockHeader:
    prev_hash: bytes
    merkle: bytes

    @property
    def block_hash(self) -> bytes:
        return sha256d(self.prev_hash + self.merkle)


def build_chain(prev: bytes, blocks_txs: list[list[bytes]]) -> list[LedgerBlockHeader]:
    """Encadena cabeceras a partir de listas de transacciones serializadas."""
    headers: list[LedgerBlockHeader] = []
    for txs in blocks_txs:
        header = LedgerBlockHeader(
            prev_hash=prev,
            merkle=merkle_root([sha256d(tx) for tx in txs]),
        )
        headers.append(header)
        prev = header.block_hash
    return headers
