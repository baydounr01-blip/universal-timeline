"""CLI: python -m bbu verify [-q]  /  bbu-verify [-q]"""

import sys

from .experiments.runner import main as run_verify


def main() -> int:
    args = [a for a in sys.argv[1:]]
    quiet = "-q" in args
    args = [a for a in args if a != "-q"]
    if not args or args[0] in {"verify", "--verify"}:
        return run_verify(verbose=not quiet)
    print("uso: python -m bbu verify [-q]")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
