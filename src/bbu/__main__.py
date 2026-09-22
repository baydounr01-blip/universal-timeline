"""CLI.

  bbu-verify [-q]                               bateria de falsacion E1-E8
  python -m bbu verify [-q]                     lo mismo
  python -m bbu qasm mensaje 101                circuito E7a (bits de t1 a t0)
  python -m bbu qasm abuelo                     paradoja del abuelo (E7c)
  python -m bbu qasm bootstrap [n]              bucle del bootstrap (E7c)
  python -m bbu capsula sellar "texto" --segundos 3600 [-o capsula.json]
  python -m bbu capsula abrir capsula.json
"""

import argparse
import sys

from .experiments.runner import main as run_verify


def _qasm(args: argparse.Namespace) -> int:
    from .pctc import bootstrap_circuit, grandfather_circuit, message_circuit
    from .qsim import to_openqasm2

    if args.kind == "mensaje":
        bits = args.arg or "1"
        if set(bits) - {"0", "1"}:
            print("el mensaje son bits, p. ej. 101", file=sys.stderr)
            return 2
        n = len(bits)
        st = message_circuit(int(bits[::-1], 2), n)
        note = (f"E7a: el mensaje {bits} sale de t1 (q[{2 * n}]..) y aparece en t0 (q[{n}]..).\n"
                f"En los disparos conservados, c[{n}]..c[{2 * n - 1}] = {bits} (bit 0 primero).\n"
                f"Fraccion ideal de disparos conservados: 4^-{n}.")
    elif args.kind == "abuelo":
        st = grandfather_circuit()
        note = ("E7c: el emisor manda lo contrario de lo que recibio el pasado.\n"
                "Fraccion ideal de disparos conservados: 0 (solo el ruido del equipo).")
    else:
        n = int(args.arg or 1)
        st = bootstrap_circuit(n)
        note = (f"E7c: el emisor reenvia lo que recibio. Fraccion ideal: 1/{1 << n};\n"
                "el contenido que llega es uniforme: el bucle no crea informacion.")
    header = ("Canal P6 por CTC postseleccionada (Lloyd et al. 2011, PRL 106:040403).\n"
              "Registros: A = q[0..n-1], B = q[n..2n-1] (t0), M = q[2n..3n-1] (t1).\n" + note)
    print(to_openqasm2(st, comment=header), end="")
    return 0


def _capsula(args: argparse.Namespace) -> int:
    from .timelock import Capsule, CapsuleError, calibrate, open_capsule, seal

    if args.action == "sellar":
        rate = calibrate(args.bits)
        squarings = max(1, int(rate * args.segundos))
        capsule, _ = seal(args.texto.encode("utf-8"), squarings, bits=args.bits, rate=rate)
        with open(args.o, "w", encoding="utf-8") as fh:
            fh.write(capsule.to_json() + "\n")
        print(f"sellada en {args.o}: T = {squarings} cuadrados secuenciales "
              f"(~{args.segundos:g} s en esta maquina, a {rate:,.0f}/s).\n"
              "Una maquina mas rapida la abrira antes: la capsula mide tics, no segundos.")
        return 0
    with open(args.texto, encoding="utf-8") as fh:
        capsule = Capsule.from_json(fh.read())

    def progress(done: int, total: int) -> None:
        print(f"\r{done / total:6.1%}  ({done}/{total} tics)", end="", file=sys.stderr, flush=True)

    try:
        message = open_capsule(capsule, progress=progress)
    except CapsuleError as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 1
    print(file=sys.stderr)
    print(message.decode("utf-8", errors="replace"))
    return 0


def main() -> int:
    argv = sys.argv[1:]
    if not argv or argv[0] in {"verify", "--verify", "-q"}:
        return run_verify(verbose="-q" not in argv)

    parser = argparse.ArgumentParser(prog="python -m bbu")
    sub = parser.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("qasm", help="exporta un circuito del canal a OpenQASM 2.0")
    q.add_argument("kind", choices=["mensaje", "abuelo", "bootstrap"])
    q.add_argument("arg", nargs="?", help="bits del mensaje, o n del bootstrap")
    c = sub.add_parser("capsula", help="mensajes al futuro (RSW 1996)")
    c.add_argument("action", choices=["sellar", "abrir"])
    c.add_argument("texto", help="texto a sellar, o fichero de capsula a abrir")
    c.add_argument("--segundos", type=float, default=60.0)
    c.add_argument("--bits", type=int, default=2048)
    c.add_argument("-o", default="capsula.json")
    args = parser.parse_args(argv)
    return _qasm(args) if args.cmd == "qasm" else _capsula(args)


if __name__ == "__main__":
    raise SystemExit(main())
