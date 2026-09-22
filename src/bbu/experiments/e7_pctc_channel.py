"""E7 -- El canal P6 con mecanismo: CTC postseleccionadas (Lloyd et al. 2011).

La seccion 9 del articulo admite que P6 es "un postulado sin mecanismo".
Aqui se le pone uno que no esta refutado (teleportacion postseleccionada,
probada con fotones en Phys. Rev. Lett. 106:040403) y se contrasta cada
afirmacion del articulo sobre el canal contra ese mecanismo:

  E7a  el mensaje de t1 esta en t0 en la rama en la que el bucle se cierra,
       sin clonar nada (P6a, P6b, P6c);
  E7b  sin esa rama -- es decir, sin conocer el futuro -- el pasado ve ruido
       identico para cualquier mensaje: el pasado no cambia (seccion 2);
  E7c  solo existen historias autoconsistentes: el abuelo tiene medida 0 y
       el bootstrap no crea informacion (seccion 2, P6c);
  E7d  el computo "llega del futuro" solo en una rama de medida k/N^2: la
       seccion 6 sobrevive restringida y P12 se ve donde debe verse.

Como refutar esto desde aqui: encontrar un mensaje para el que la matriz
densidad del receptor en E7b dependa del mensaje (senalizacion al pasado),
o una f sin puntos fijos con medida de cierre > 0 en E7c.
"""

from __future__ import annotations

import math

from ..pctc import (
    bootstrap,
    closed_loop,
    grandfather,
    receiver_density,
    search_through_time,
    send_bits_to_past,
    send_bytes_to_past,
    send_qubit_to_past,
)
from ..qsim import max_entry_difference, shannon_bits
from ..signature import ComputeAuditor, ProofOfWorkResult
from .verdict import Outcome, Verdict

TOL = 1e-12


def run_message(n: int = 3) -> Verdict:
    runs = [send_bits_to_past(m, n) for m in range(1 << n)]
    qubits = [send_qubit_to_past(t, p) for t, p in
              [(0.0, 0.0), (math.pi, 0.0), (math.pi / 2, 0.0),
               (math.pi / 2, math.pi / 2), (1.1, 0.7), (2.5, -1.9)]]
    text, p_text = send_bytes_to_past(b"hola")
    residues = [q.residue for q in qubits]
    checks = {
        "todos_los_mensajes_llegan_en_la_rama_que_cierra":
            all(abs(r.fidelity - 1) < TOL for r in runs),
        "medida_de_la_rama_que_cierra_es_4^-n":
            all(abs(r.p_loop_closes - 4.0 ** -n) < TOL for r in runs),
        "estados_cuanticos_llegan_con_fidelidad_1":
            all(abs(q.fidelity - 1) < TOL for q in qubits),
        "no_queda_copia_en_t1":
            max(max_entry_difference(residues[0], r) for r in residues) < TOL,
        "bytes_llegan_intactos": text == b"hola",
    }
    ok = all(checks.values())
    return Verdict(
        claim="el canal P6 tiene mecanismo no refutado: en la rama en la que el "
              "bucle se cierra, t0 lee exactamente lo que t1 envio, sin clonar nada",
        postulates="P6,P3",
        outcome=Outcome.CORROBORATED if ok else Outcome.REFUTED,
        evidence={
            **checks,
            "bits_por_mensaje": n,
            "medida_por_bit": runs[0].p_loop_closes ** (1 / n),
            "medida_de_la_rama_para_'hola'_(32_bits)": p_text,
        },
        notes="el mismo circuito transporta estados cuanticos sin clonarlos: bajo "
              "este mecanismo P6b es una restriccion de diseno, no una consecuencia "
              "de la no clonacion",
    )


def run_no_signaling(n: int = 3) -> Verdict:
    before = receiver_density(None, n)
    after = [receiver_density(m, n) for m in range(1 << n)]
    dim = 1 << n
    uniform = [[(1 / dim if i == j else 0) + 0j for j in range(dim)] for i in range(dim)]
    diffs = [max_entry_difference(before, rho) for rho in after]
    runs = [send_bits_to_past(m, n) for m in range(1 << n)]
    # Lectura de Everett: en la rama (z, s) el receptor tenia m XOR s.
    pad = all(
        set(dist) == {r.message ^ s} for r in runs for (z, s), dist in r.branches.items()
    )
    checks = {
        "t1_no_cambia_lo_que_t0_puede_ver": max(diffs) < TOL,
        "t0_ve_ruido_uniforme": max_entry_difference(before, uniform) < TOL,
        "cada_rama_es_una_libreta_de_un_solo_uso": pad,
        "ramas_de_bell_equiprobables": all(
            abs(sum(d.values()) - 4.0 ** -n) < TOL
            for r in runs for d in r.branches.values()),
    }
    ok = all(checks.values())
    return Verdict(
        claim="no senalizacion: sin la rama postseleccionada (sin conocer el futuro) "
              "el pasado ve lo mismo mande lo que mande el futuro; nada cambia en t0",
        postulates="P6c,S2",
        outcome=Outcome.CORROBORATED if ok else Outcome.REFUTED,
        evidence={
            **checks,
            "max_diferencia_densidad_receptor": max(diffs),
            "ramas_de_bell_por_mensaje": len(runs[0].branches),
        },
        notes="el mensaje esta en t0 en todas las ramas, cifrado con una clave "
              "(el resultado de Bell) que solo existe en t1",
    )


def run_self_consistency() -> Verdict:
    abuelo = [grandfather(n) for n in (1, 2, 3)]
    boot = [bootstrap(n) for n in (1, 2, 3)]
    # Funciones arbitrarias de 3 bits: medida de cierre = k/N^2, y la salida
    # es uniforme sobre los puntos fijos.
    families = {
        "doble_mod_8": lambda x: (2 * x) % 8,
        "cuadrado_mod_8": lambda x: (x * x) % 8,
        "rotacion": lambda x: ((x << 1) | (x >> 2)) & 7,
        "constante_5": lambda x: 5,
    }
    generic = {name: closed_loop(3, f, name) for name, f in families.items()}
    generic_ok = all(
        abs(r.p_loop_closes - len(r.fixed_points) / 64) < TOL
        and set(r.received_if_closed) == set(r.fixed_points)
        for r in generic.values())
    entropies = [shannon_bits(b.received_if_closed) for b in boot]
    checks = {
        "abuelo_tiene_medida_cero": all(g.p_loop_closes == 0.0 for g in abuelo),
        "bootstrap_cierra_con_medida_1/N": all(
            abs(b.p_loop_closes - 1 / (1 << b.n)) < TOL for b in boot),
        "bootstrap_no_crea_informacion": all(
            abs(h - b.n) < 1e-9 for h, b in zip(entropies, boot)),
        "solo_sobreviven_puntos_fijos_con_medida_k/N^2": generic_ok,
    }
    ok = all(checks.values())
    return Verdict(
        claim="autoconsistencia: solo existen las historias que no se contradicen; "
              "la paradoja del abuelo no ocurre y el bootstrap no crea contenido",
        postulates="P6c,S2",
        outcome=Outcome.CORROBORATED if ok else Outcome.REFUTED,
        evidence={
            **checks,
            "medida_abuelo": [g.p_loop_closes for g in abuelo],
            "entropia_bootstrap_bits": [round(h, 12) for h in entropies],
            "puntos_fijos": {k: r.fixed_points for k, r in generic.items()},
        },
        notes="P-CTC excluye la historia paradojica (Novikov); Deutsch la mezcla "
              "(la regla del fork). Ambas son autoconsistentes; difieren solo "
              "donde hay CTC de verdad, que nadie ha observado",
    )


def _pow_predicate(template: bytes, target: int):
    return lambda x: ProofOfWorkResult(template, x.to_bytes(4, "big"), target).is_valid()


def run_compute_return(n: int = 8, template: bytes = b"bbu-e7d",
                       target: int = 2 ** 256 // 64) -> Verdict:
    run = search_through_time(n, _pow_predicate(template, target))
    k, size = len(run.solutions), run.size
    cost = ProofOfWorkResult(template, b"", target).expected_cost_hashes

    # En la rama que cierra, el agente exhibe un nonce valido habiendo hecho
    # UNA evaluacion (coherente) del predicado: el detector P12 dispara.
    received = max(run.received_if_closed, key=run.received_if_closed.get)
    auditor = ComputeAuditor(branch_budget_hashes=1.0)
    auditor.submit(ProofOfWorkResult(template, received.to_bytes(4, "big"), target))

    # Sobre todas las ramas, pesadas por Born: computo acreditado por ejecucion.
    accredited_per_run_channel = run.p_loop_closes * cost
    accredited_per_trial_brute = (k / size) * cost
    checks = {
        "la_rama_que_cierra_solo_contiene_soluciones":
            k > 0 and abs(run.mass_on_solutions - 1) < TOL,
        "medida_de_cierre_es_k/N^2": abs(run.p_loop_closes - k / size ** 2) < TOL,
        "firma_P12_en_la_rama_que_cierra": auditor.signature_detected(),
        "sin_ganancia_sobre_todas_las_ramas": accredited_per_run_channel <= 1.0,
        "el_canal_cuesta_N_veces_la_fuerza_bruta": abs(
            run.expected_runs / run.brute_force_expected_trials - size) < 1e-6,
    }
    survives_in_branch = (checks["la_rama_que_cierra_solo_contiene_soluciones"]
                          and checks["firma_P12_en_la_rama_que_cierra"])
    no_net_gain = (checks["sin_ganancia_sobre_todas_las_ramas"]
                   and checks["el_canal_cuesta_N_veces_la_fuerza_bruta"])
    # Sobrevive en la rama pero sin ganancia neta: la afirmacion queda acotada.
    if not survives_in_branch:
        outcome = Outcome.REFUTED
    elif no_net_gain:
        outcome = Outcome.CONSTRAINED
    else:
        outcome = Outcome.CORROBORATED
    return Verdict(
        claim="anos de computo en otra rama llegan aqui como resultado inmediato "
              "(seccion 6, P10-P12)",
        postulates="P10-P12",
        outcome=outcome,
        evidence={
            **checks,
            "espacio_de_nonces_N": size,
            "soluciones_k": k,
            "nonce_recibido_del_futuro": received,
            "medida_de_la_rama_que_cierra": run.p_loop_closes,
            "exceso_P12_en_esa_rama": auditor.excess_ratio,
            "ejecuciones_esperadas_via_canal": run.expected_runs,
            "intentos_esperados_fuerza_bruta": run.brute_force_expected_trials,
            "computo_acreditado_por_ejecucion_canal": accredited_per_run_channel,
            "computo_acreditado_por_intento_fuerza_bruta": accredited_per_trial_brute,
        },
        notes="el resultado llega en la rama que cierra, pero esa rama pesa k/N^2: "
              "la postseleccion simulada cuesta N veces mas que calcular. Solo una "
              "CTC real (no observada) postseleccionaria gratis -- Aaronson 2005: "
              "PostBQP = PP",
    )
