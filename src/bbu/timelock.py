"""El canal hacia delante: capsulas temporales (Rivest, Shamir y Wagner 1996).

Hacia el pasado el canal solo existe en la rama postseleccionada (`pctc`).
Hacia el futuro funciona hoy, en cualquier ordenador, y con una garantia que
un simple fichero guardado no tiene: el mensaje no puede leerse ANTES de su
momento, ni siquiera por quien lo escribio.

Mecanismo (puzzle de cuadrados repetidos):

  * el emisor elige n = p*q y una base a; la clave del mensaje sale de
    x_T = a^(2^T) mod n;
  * conociendo phi(n) = (p-1)(q-1), el emisor calcula x_T en ~log(n)
    multiplicaciones (2^T mod phi(n)) y luego DESTRUYE p y q;
  * sin ellos, el mejor metodo conocido es elevar al cuadrado T veces, una
    tras otra: cada cuadrado necesita el anterior (P2, enlace = causalidad)
    y ningun paralelismo acorta la cadena.

Que no exista atajo sin factorizar n es la conjetura de secuencialidad de
RSW (1996), no refutada: el acertijo LCS35 de Rivest (1999, pensado para 35
anos) se abrio en 2019 tras ~3.5 anos de cuadrados secuenciales en una CPU
comun, conforme a la conjetura, no contra ella.

Leccion de P5 que la capsula hace tangible: mide tics de computo secuencial
del que la abre, no segundos. Una maquina mas rapida la abre antes, igual
que un reloj en otra region de densidad de tics marca otro tiempo propio.

El cifrado del cuerpo es un flujo SHA-256 en modo contador con etiqueta
HMAC-SHA256: sin dependencias, suficiente para el proposito y declarado como
lo que es.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import random
import secrets
import time
from dataclasses import dataclass
from typing import Callable

_DOMAIN = b"bbu-capsula-v1"
_SMALL_PRIMES = [p for p in range(3, 2000) if all(p % d for d in range(2, int(p ** 0.5) + 1))]


class CapsuleError(Exception):
    """La etiqueta no cuadra: capsula abierta antes de tiempo o manipulada."""


def _is_probable_prime(n: int, rng: random.Random, rounds: int = 40) -> bool:
    if n < 2:
        return False
    for p in _SMALL_PRIMES:
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for _ in range(rounds):
        x = pow(rng.randrange(2, n - 1), d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def _random_prime(bits: int, rng: random.Random) -> int:
    while True:
        c = rng.getrandbits(bits) | (1 << (bits - 1)) | (1 << (bits - 2)) | 1
        if _is_probable_prime(c, rng):
            return c


def _keystream(key: bytes, length: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < length:
        out += hashlib.sha256(key + counter.to_bytes(8, "big")).digest()
        counter += 1
    return bytes(out[:length])


def _key_from(x: int, modulus: int, salt: bytes) -> bytes:
    width = (modulus.bit_length() + 7) // 8
    return hashlib.sha256(_DOMAIN + salt + x.to_bytes(width, "big")).digest()


@dataclass(frozen=True)
class Capsule:
    """Lo que viaja al futuro. No contiene p, q ni phi(n): la trampilla se
    destruye al sellar."""

    modulus: int
    base: int
    squarings: int          # T: tics secuenciales que exige abrirla
    salt: bytes
    ciphertext: bytes
    tag: bytes
    sealed_at: str = ""
    squarings_per_second_at_seal: float = 0.0

    def to_json(self) -> str:
        return json.dumps({
            "formato": "bbu-capsula-v1",
            "n": hex(self.modulus), "a": hex(self.base), "T": self.squarings,
            "sal": self.salt.hex(), "cifrado": self.ciphertext.hex(),
            "etiqueta": self.tag.hex(), "sellada": self.sealed_at,
            "cuadrados_por_segundo_al_sellar": self.squarings_per_second_at_seal,
        }, indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "Capsule":
        d = json.loads(text)
        if d.get("formato") != "bbu-capsula-v1":
            raise CapsuleError("formato de capsula desconocido")
        return cls(modulus=int(d["n"], 16), base=int(d["a"], 16), squarings=int(d["T"]),
                   salt=bytes.fromhex(d["sal"]), ciphertext=bytes.fromhex(d["cifrado"]),
                   tag=bytes.fromhex(d["etiqueta"]), sealed_at=d.get("sellada", ""),
                   squarings_per_second_at_seal=float(d.get("cuadrados_por_segundo_al_sellar", 0.0)))


@dataclass(frozen=True)
class SealReport:
    """Cuanto le costo al emisor: multiplicaciones modulares del atajo."""

    shortcut_multiplications: int
    squarings_required_to_open: int


def seal(message: bytes, squarings: int, bits: int = 2048,
         rng: random.Random | None = None, rate: float = 0.0) -> tuple[Capsule, SealReport]:
    """Sella `message` para que solo se lea tras `squarings` cuadrados
    secuenciales. `rng` permite pruebas deterministas; por defecto se usa la
    fuente criptografica del sistema."""
    if squarings < 1:
        raise ValueError("una capsula necesita al menos un tic")
    rng = rng or secrets.SystemRandom()
    p = _random_prime(bits // 2, rng)
    q = _random_prime(bits // 2, rng)
    while q == p:
        q = _random_prime(bits // 2, rng)
    n = p * q
    phi = (p - 1) * (q - 1)
    base = rng.randrange(2, n - 1)
    # El atajo del emisor: 2^T mod phi(n), y una sola exponenciacion.
    e = pow(2, squarings, phi)
    x = pow(base, e, n)
    del p, q, phi       # la trampilla no sale de aqui: la capsula no la lleva
    salt = rng.getrandbits(128).to_bytes(16, "big")
    key = _key_from(x, n, salt)
    ct = bytes(m ^ k for m, k in zip(message, _keystream(key, len(message))))
    tag = hmac.new(key, salt + ct, hashlib.sha256).digest()
    capsule = Capsule(modulus=n, base=base, squarings=squarings, salt=salt,
                      ciphertext=ct, tag=tag,
                      sealed_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                      squarings_per_second_at_seal=rate)
    # Coste del atajo: dos exponenciaciones por cuadrados y multiplicaciones.
    cost = 2 * (squarings.bit_length() + e.bit_length())
    return capsule, SealReport(shortcut_multiplications=cost,
                               squarings_required_to_open=squarings)


def unlock_with(capsule: Capsule, x: int) -> bytes:
    """Abre con un valor candidato de x_T. Si no es el correcto, la etiqueta
    lo delata y no se entrega nada."""
    key = _key_from(x, capsule.modulus, capsule.salt)
    expected = hmac.new(key, capsule.salt + capsule.ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, capsule.tag):
        raise CapsuleError("la etiqueta no cuadra: faltan tics o la capsula fue alterada")
    return bytes(c ^ k for c, k in zip(capsule.ciphertext, _keystream(key, len(capsule.ciphertext))))


def sequential_squarings(capsule: Capsule, count: int | None = None,
                         progress: Callable[[int, int], None] | None = None) -> int:
    """El unico camino conocido sin la trampilla: `count` cuadrados, uno
    detras de otro (por defecto, los T de la capsula)."""
    total = capsule.squarings if count is None else count
    x, n = capsule.base, capsule.modulus
    step = max(1, total // 100)
    for i in range(total):
        x = x * x % n
        if progress is not None and (i + 1) % step == 0:
            progress(i + 1, total)
    return x


def open_capsule(capsule: Capsule,
                 progress: Callable[[int, int], None] | None = None) -> bytes:
    return unlock_with(capsule, sequential_squarings(capsule, progress=progress))


def calibrate(bits: int = 2048, seconds: float = 0.5) -> float:
    """Cuadrados por segundo de ESTA maquina con un modulo de `bits` bits.
    Sirve para traducir segundos deseados en T; el tiempo real de apertura
    depende de la maquina que abra (P5: tiempo propio, no tiempo global)."""
    n = secrets.randbits(bits) | (1 << (bits - 1)) | 1
    x = secrets.randbelow(n - 2) + 2
    done, start = 0, time.perf_counter()
    while time.perf_counter() - start < seconds:
        for _ in range(1000):
            x = x * x % n
        done += 1000
    return done / (time.perf_counter() - start)
