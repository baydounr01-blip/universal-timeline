"""E5 -- El experimento mental del millon de bitcoin (seccion 5).

La version ingenua debe fallar TRES veces por razones internas de la teoria,
y la version refinada debe ser coherente. Cada fallo y cada invariante de la
seccion 5 se ejecuta aqui. Si la version ingenua funcionara, o la refinada
dejara rastro en origen, el articulo quedaria refutado por su propio modelo.
"""

from __future__ import annotations

from ..bitcoinrules import (
    POST_2024_HEIGHT,
    CompetingChain,
    NodeView,
    blocks_needed_for,
    subsidy_at_height,
)
from ..block import Block
from ..channel import InterBranchChannel
from ..ledger import BranchLedger, UnknownCoinError
from ..merkle import build_chain, sha256d
from ..returns import factorization_return
from .verdict import Outcome, Verdict

MILLION = 1_000_000.0
MILLION_UTXO = "utxo:1M"


# --------------------------------------------------------------------------
# Fallo 1: "minar en el propio t-1" no existe como operacion.
# --------------------------------------------------------------------------

def naive_failure_1() -> dict:
    """Cualquier cambio en el padre, o contradice el registro que conduce al
    presente (detectable: la cadena deja de verificar), o es una rama nueva."""
    genesis = Block(tick=0, branch_id="raiz", state={"epoch": "genesis"})
    t_minus_1 = genesis.extend({"ledger": "1M en tu direccion"})
    t = t_minus_1.extend({"ledger": "tu presente"})

    assert t.verify_chain()

    # Intento A: reescribir el estado del propio t-1 ("minar alli").
    t_minus_1.state["ledger"] = "2M en tu direccion"
    contradiction_detected = not t.verify_chain()
    t_minus_1.state["ledger"] = "1M en tu direccion"  # restaurar
    assert t.verify_chain()

    # Intento B: construir "el mismo t-1 pero con mas monedas". Sale un
    # bloque con otro hash colgando del abuelo: una rama hermana, no el padre.
    rewritten = Block(tick=1, branch_id="raiz/reintento", parent=genesis,
                      state={"ledger": "2M en tu direccion"})
    is_a_new_branch = (rewritten.block_hash != t_minus_1.block_hash
                       and not rewritten.is_ancestor_of(t)
                       and rewritten.is_sibling_branch_of(t))

    return {
        "reescribir_el_padre_contradice_el_registro": contradiction_detected,
        "minar_de_nuevo_crea_rama_hermana_no_el_padre": is_a_new_branch,
    }


# --------------------------------------------------------------------------
# Fallo 2: minar en una rama hermana deja las monedas atrapadas alli.
# --------------------------------------------------------------------------

def naive_failure_2(n_branches: int = 50) -> dict:
    origin = BranchLedger(branch_id="t")
    origin.utxo["utxo:base"] = True

    trapped = 0
    for i in range(n_branches):
        sibling = origin.inherit(f"t'/{i}")
        sibling.utxo[f"utxo:minado-en-t'{i}"] = True   # el millon minado alli
        assert sibling.is_unspent(f"utxo:minado-en-t'{i}")
        trapped += 1

    # En la rama de origen esas monedas no existen: gastarlas es imposible.
    unknown_in_origin = 0
    for i in range(n_branches):
        try:
            origin.spend(f"utxo:minado-en-t'{i}")
        except UnknownCoinError:
            unknown_in_origin += 1

    return {
        "ramas_con_millon_atrapado": trapped,
        "gastos_imposibles_en_origen": unknown_in_origin,
        "monedas_visibles_en_origen": origin.total_unspent(),
    }


# --------------------------------------------------------------------------
# Fallo 3: traerlas por el canal.
# --------------------------------------------------------------------------

def naive_failure_3() -> dict:
    results: dict = {}

    # (a) Las claves privadas viajan (son bytes), pero en origen no controlan
    #     ningun UTXO: la cadena de t' es otra cadena.
    channel = InterBranchChannel()
    keys = channel.receive_from_branch(b"claves-privadas-de-utxos-de-t'")
    origin = BranchLedger(branch_id="t")
    try:
        origin.spend("utxo:de-la-cadena-de-t'")
        keys_control_something = True
    except UnknownCoinError:
        keys_control_something = False
    results["las_claves_llegan_pero_no_controlan_nada"] = (
        isinstance(keys, bytes) and not keys_control_something
    )

    # (b) Los bloques de t' son una cadena competidora. Un nodo de origen
    #     la rechaza sin mas trabajo acumulado desde la bifurcacion, y las
    #     reescrituras profundas chocan con puntos de control y trabajo
    #     minimo asumido.
    node = NodeView(tip_height=910_000, work_per_block=1.0,
                    checkpoint_height=900_000, minimum_chain_work=3_000.0)
    shallow = CompetingChain(fork_height=905_000, length=4_000, work_per_block=1.0)
    accepted_shallow, reason_shallow = node.evaluate(shallow)
    deep = CompetingChain(fork_height=1, length=2_000_000, work_per_block=1.0)
    accepted_deep, reason_deep = node.evaluate(deep)
    results["cadena_con_menos_trabajo"] = reason_shallow
    results["reescritura_profunda"] = reason_deep
    results["ambas_rechazadas"] = (not accepted_shallow) and (not accepted_deep)

    # (c) Incluso una reorganizacion aceptada solo renta la recompensa de
    #     protocolo: 3.125 BTC/bloque desde 2024, no un millon.
    results["recompensa_actual_btc_por_bloque"] = subsidy_at_height(POST_2024_HEIGHT)
    blocks = blocks_needed_for(MILLION, start_height=POST_2024_HEIGHT)
    results["bloques_de_reescritura_para_1M"] = blocks
    if blocks is not None:
        results["anios_de_bloques_a_10_min"] = round(blocks * 10 / (60 * 24 * 365), 1)

    # (d) P8: "el mismo bloque con otra coinbase" no existe. Cambiar una
    #     transaccion cambia la raiz de Merkle, el hash del bloque y todos
    #     los posteriores.
    txs = [[b"coinbase->direccion-original", b"tx1"], [b"coinbase2", b"tx2"]]
    txs_alt = [[b"coinbase->OTRA-direccion", b"tx1"], [b"coinbase2", b"tx2"]]
    chain = build_chain(sha256d(b"antes"), txs)
    chain_alt = build_chain(sha256d(b"antes"), txs_alt)
    results["cambiar_coinbase_cambia_todos_los_hashes"] = all(
        a.block_hash != b.block_hash for a, b in zip(chain, chain_alt)
    )
    return results


# --------------------------------------------------------------------------
# Version refinada: coherente.
# --------------------------------------------------------------------------

def refined_version(n_messages: int = 100) -> dict:
    # El arbol de bloques: genesis -> t-1 -> t. El agente vive en t.
    genesis = Block(tick=0, branch_id="raiz", state={})
    t_minus_1 = genesis.extend({"quien": "tu, con el millon"})
    t = t_minus_1.extend({"quien": "tu y tu libro mayor"})

    origin_ledger = BranchLedger(branch_id="t")
    origin_ledger.utxo[MILLION_UTXO] = True
    before = origin_ledger.snapshot_hash()
    lineage_before = t.lineage_hash()

    channel = InterBranchChannel()
    returned_bits: list[bytes] = []
    branch_spends = 0

    n = 9_223_372_036_854_775_783 * 9_223_372_036_854_775_643  # existia en t-1
    for i in range(n_messages):
        # El mensaje va "a t-1": por la regla del fork llega a una rama
        # hermana t' donde una copia lo recibe (P6c).
        receipt = channel.send_to_past(
            sender=t, target_tick=1,
            payload=f"protocolo simetrico: factoriza n y paga tu millon".encode(),
        )
        assert receipt.sender_history_intact          # el pasado de t, intacto
        assert receipt.sibling.is_sibling_branch_of(t)

        # Herencia automatica (P8): la copia tiene el mismo millon, y lo
        # gasta en SU libro mayor (P7).
        sibling_ledger = origin_ledger.inherit(receipt.sibling.branch_id)
        sibling_ledger.spend(MILLION_UTXO, memo="compra de computo")
        branch_spends += 1

        # Solo regresa informacion clasica (P6a/P6b) e invariante (P10).
        ret = factorization_return(
            n, 9_223_372_036_854_775_783, 9_223_372_036_854_775_643
        )
        returned_bits.append(channel.receive_from_branch(ret.payload))
        assert ret.value_in_origin({"n": n})

    after = origin_ledger.snapshot_hash()
    return {
        "gastos_del_mismo_millon": branch_spends,
        "libro_de_origen_intacto": before == after,
        "linea_del_emisor_intacta": t.lineage_hash() == lineage_before,
        "millon_sin_gastar_en_origen": origin_ledger.is_unspent(MILLION_UTXO),
        "retornos_clasicos_verificados": len(returned_bits),
    }


def run() -> Verdict:
    f1 = naive_failure_1()
    f2 = naive_failure_2()
    f3 = naive_failure_3()
    refined = refined_version()

    naive_fails_three_times = (
        all(f1.values())
        and f2["gastos_imposibles_en_origen"] == f2["ramas_con_millon_atrapado"]
        and f3["las_claves_llegan_pero_no_controlan_nada"]
        and f3["ambas_rechazadas"]
        and f3["cambiar_coinbase_cambia_todos_los_hashes"]
    )
    refined_coherent = (
        refined["libro_de_origen_intacto"]
        and refined["linea_del_emisor_intacta"]
        and refined["millon_sin_gastar_en_origen"]
        and refined["gastos_del_mismo_millon"] == refined["retornos_clasicos_verificados"]
    )

    ok = naive_fails_three_times and refined_coherent
    return Verdict(
        claim="la version ingenua falla tres veces; la refinada gasta el mismo millon "
              "en N ramas sin dejar rastro en origen y solo regresa informacion",
        postulates="P2,P6-P10",
        outcome=Outcome.CORROBORATED if ok else Outcome.REFUTED,
        evidence={"fallo_1": f1, "fallo_2": f2, "fallo_3": f3, "refinada": refined},
        notes="el gasto ramificado no multiplica monedas; multiplica poder de "
              "compra de informacion",
    )
