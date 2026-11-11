"""Eigenschaftstests (ORACLE-PLAYBOOK §5.2): Aussagen über das Verfahren, die ohne bekanntes Ergebnis gelten müssen.

- Umnummerieren der Kunden ändert das Ergebnis der vollen Regel nicht (Wert, Route bis auf die Namen).
- Alle Längen, Zeiten, Fenster und Dualpreise mit demselben Faktor 2 multipliziert: dieselbe Route, doppelter Wert.
- Mit Dominanz entstehen nie mehr Labels als ohne.
- „keine Dominanz“ und „volle Dominanz“ liefern denselben besten Wert.
- Eine zusätzliche Option (ein weiterer Kunde mit sehr kleinem Dualpreis) verschlechtert den besten Wert nie.
- Gleicher Eingang, gleiches Ergebnis (Reproduzierbarkeit)."""

import random

import pytest

import dml_algorithm as A
import dml_scenario as S
from dml_scenario import Instance


def _cases(count=30, n=7):
    for seed in range(count):
        width = (30, 80, 200)[seed % 3]
        yield seed, S.make_instance(n, seed + 700, width), S.random_duals(n, seed + 700)


def _permute(inst, pi, perm):
    """Kunde i heißt danach perm[i] (perm ist eine Permutation von 1..n, perm[0] = 0 für das Depot)."""
    n = inst.n
    inv = [0] * (n + 1)
    for old, new in enumerate(perm):
        inv[new] = old

    def pick(values):
        return tuple(values[inv[new]] for new in range(n + 1))

    d = tuple(tuple(inst.d[inv[a]][inv[b]] for b in range(n + 1)) for a in range(n + 1))
    return Instance(n, pick(inst.points), d, pick(inst.demand), pick(inst.ready), pick(inst.due), inst.service, inst.horizon, inst.capacity), pick(pi)


def test_renumbering_customers_does_not_change_the_full_rule_result():
    rng = random.Random(3)
    for seed, inst, pi in _cases():
        perm = [0] + rng.sample(range(1, inst.n + 1), inst.n)
        inst2, pi2 = _permute(inst, pi, perm)
        a = A.price(inst, pi, inst.n, A.RULES["voll"])
        b = A.price(inst2, pi2, inst2.n, A.RULES["voll"])
        assert b.value == pytest.approx(a.value, abs=1e-9), seed
        if b.route:
            assert A.route_value(inst, pi, _undo(b.route, perm)) == pytest.approx(a.value, abs=1e-9), seed
        else:
            assert a.value == 0, seed


def _undo(route, perm):
    inv = {new: old for old, new in enumerate(perm)}
    return [inv[j] for j in route]


def test_scaling_lengths_times_and_dual_prices_by_two_keeps_the_route():
    for seed, inst, pi in _cases():
        scaled = Instance(inst.n, inst.points, tuple(tuple(2 * x for x in row) for row in inst.d), inst.demand, tuple(2 * x for x in inst.ready),
                          tuple(2 * x for x in inst.due), 2 * inst.service, 2 * inst.horizon, inst.capacity)
        a = A.price(inst, pi, inst.n, A.RULES["voll"])
        b = A.price(scaled, tuple(2 * x for x in pi), inst.n, A.RULES["voll"])
        assert b.route == a.route and b.value == pytest.approx(2 * a.value, abs=1e-9), seed
        assert b.generated == a.generated


def test_dominance_never_creates_more_labels_than_no_dominance():
    for seed, inst, pi in _cases(60):
        none = A.price(inst, pi, inst.n, None).generated
        for name, rule in A.RULES.items():
            assert A.price(inst, pi, inst.n, rule).generated <= none, (seed, name)


def test_a_rule_with_more_conditions_dominates_only_where_the_coarser_rule_does():
    """Die Bedingungen der Regeln bilden eine Kette (nur Kosten, + Zeit, + Zeit und Last, voll): Was die strengere Regel dominiert, dominiert auch die gröbere."""
    rng = random.Random(11)
    chain = ["voll", "kosten_zeit_last", "kosten_zeit", "kosten"]
    seen = [0] * len(chain)
    for _ in range(500):
        a = A.Label(rng.randint(0, 5), rng.randint(-5, 5), rng.randint(0, 3), rng.randint(0, 15), 1, -1)
        b = A.Label(rng.randint(0, 5), rng.randint(-5, 5), rng.randint(0, 3), rng.randint(0, 15), 1, -1)
        flags = [A.dominates(a, b, A.RULES[name]) for name in chain]
        assert all(flags[i] <= flags[i + 1] for i in range(len(flags) - 1)), (a, b, flags)
        for i, f in enumerate(flags):
            seen[i] += f
    assert seen[0] > 0 and seen[0] < seen[-1]      # die Stichprobe trennt die Regeln (nicht alle Zahlen gleich)


def test_no_dominance_and_full_dominance_give_the_same_best_value():
    for seed, inst, pi in _cases(60, n=8):
        a, b = A.price(inst, pi, inst.n, None), A.price(inst, pi, inst.n, A.RULES["voll"])
        assert b.value == pytest.approx(a.value, abs=1e-9), seed


def test_an_additional_option_never_worsens_the_best_value():
    """Ein zusätzlicher Kunde ganz am Rand mit Dualpreis 0 ist nutzlos, aber eine zulässige Option mehr: der beste Wert wird nie schlechter."""
    for seed, inst, pi in _cases(20, n=6):
        n = inst.n
        d = [list(row) + [60.0] for row in inst.d] + [[60.0] * (n + 1) + [0.0]]
        bigger = Instance(n + 1, inst.points + ((0.0, 0.0),), tuple(tuple(r) for r in d), inst.demand + (5,), inst.ready + (0.0,), inst.due + (inst.horizon,),
                          inst.service, inst.horizon, inst.capacity)
        a = A.price(inst, pi, n, A.RULES["voll"]).value
        b = A.price(bigger, pi + (0.0,), n + 1, A.RULES["voll"]).value
        assert b <= a + 1e-9, seed


def test_same_input_same_output():
    inst, pi = S.make_instance(9, 5, 80), S.random_duals(9, 5)
    assert A.price(inst, pi, 9, A.RULES["voll"], trace=True) == A.price(inst, pi, 9, A.RULES["voll"], trace=True)


def test_result_does_not_depend_on_the_hash_seed_of_the_process():
    """DEMO-PLAYBOOK §1d: dasselbe Szenario in zwei Prozessen mit verschiedenem PYTHONHASHSEED gibt dasselbe Ergebnis."""
    import os
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    code = ("import sys; sys.path.insert(0, sys.argv[1]); import dml_algorithm as A, dml_scenario as S; "
            "i, p = S.make_instance(9, 5, 80), S.random_duals(9, 5); r = A.price(i, p, 9, A.RULES['voll']); "
            "print(r.value, r.route, r.generated, r.dominated)")
    outs = []
    for hash_seed in ("1", "2"):
        env = {**os.environ, "PYTHONHASHSEED": hash_seed}
        outs.append(subprocess.run([sys.executable, "-c", code, str(root)], capture_output=True, text=True, env=env, check=True, timeout=120).stdout)
    assert outs[0] == outs[1] and outs[0].strip()
