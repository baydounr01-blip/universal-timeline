"""La linea de comandos: el circuito que se exporta es el que se simula."""

import sys

import pytest

from bbu.__main__ import main


def run_cli(monkeypatch, capsys, *argv):
    monkeypatch.setattr(sys, "argv", ["bbu", *argv])
    code = main()
    return code, capsys.readouterr()


@pytest.mark.parametrize("argv", [("qasm", "mensaje", "101"), ("qasm", "abuelo"),
                                  ("qasm", "bootstrap", "2")])
def test_qasm_export(monkeypatch, capsys, argv):
    code, out = run_cli(monkeypatch, capsys, *argv)
    assert code == 0
    assert out.out.startswith("OPENQASM 2.0;")
    assert "// postseleccion: conserva solo los disparos con" in out.out


def test_qasm_rejects_non_binary_messages(monkeypatch, capsys):
    code, _ = run_cli(monkeypatch, capsys, "qasm", "mensaje", "12")
    assert code == 2


def test_capsule_round_trip(monkeypatch, capsys, tmp_path):
    path = tmp_path / "c.json"
    code, _ = run_cli(monkeypatch, capsys, "capsula", "sellar", "hola, futuro",
                      "--segundos", "0.01", "--bits", "256", "-o", str(path))
    assert code == 0 and path.exists()
    code, out = run_cli(monkeypatch, capsys, "capsula", "abrir", str(path))
    assert code == 0
    assert out.out.strip() == "hola, futuro"
