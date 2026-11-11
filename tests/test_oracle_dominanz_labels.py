"""Orakel-Test: das Label-Verfahren gegen einen unabhängigen Rechenweg (ORACLE-PLAYBOOK §2 und §5, DEMO-PLAYBOOK §12).

Orakel: Tiefensuche über **alle** Routen mit eigenem Stapel; jede Route wird von vorn nachgerechnet (Zeit, Last, Fenster, Kosten), ohne Labels, ohne Dominanz und
ohne Funktion aus dem Kern der Demo. Das Orakel selbst ist am Handbeispiel geprüft (52 Routen, bester Wert −22 bei 6-2-3-5) und an einer zweiten Aufzählung über
alle Permutationen (`itertools.permutations`) auf kleinen Instanzen. Geprüft werden das Hauptergebnis, die angezeigten Zähler (erzeugte Labels ohne Dominanz) und die
Trennschärfe: Die zu grobe Regel „nur Kosten“ muss vom Orakel abweichen, sonst taugt die Prüfung nichts."""

import itertools

import pytest

import dml_algorithm as A
import dml_scenario as S

EPS = 1e-9


def simulate(inst, pi, route):
    """Zeit, Last und Kosten einer Route von vorn; None, wenn ein Zeitfenster oder die Kapazität verletzt ist (ohne Rückkehr)."""
    time, load, cost, at = 0, 0, 0, 0
    for j in route:
        arrive = time + (inst.service if at != 0 else 0) + inst.d[at][j]
        load += inst.demand[j]
        if arrive > inst.due[j] + EPS or load > inst.capacity:
            return None
        time = max(arrive, inst.ready[j])
        cost += inst.d[at][j] - pi[j]
        at = j
    return time, cost, at


def oracle(inst, pi):
    """(beste reduzierte Kosten oder 0, Zahl der zulässigen Teilrouten) durch Tiefensuche mit eigenem Stapel."""
    best, partial = 0, 0
    stack = [()]
    while stack:
        route = stack.pop()
        if route:
            sim = simulate(inst, pi, route)
            if sim is None:
                continue
            partial += 1
            time, cost, at = sim
            if time + inst.service + inst.d[at][0] <= inst.horizon + EPS:
                best = min(best, cost + inst.d[at][0])
        stack.extend(route + (j,) for j in range(1, inst.n + 1) if j not in route)
    return best, partial


def cases(n=7):
    for seed in range(60):
        for width in (30, 80, 200):
            yield seed, width, S.make_instance(n, seed, width), S.random_duals(n, seed)


def test_oracle_on_the_hand_example(hand):
    inst, pi = hand
    best, partial = oracle(inst, pi)
    assert best == -22 and partial + 1 == 53


def test_oracle_agrees_with_a_permutation_enumeration_on_small_instances():
    for seed in range(15):
        inst = S.make_instance(5, seed, 80)
        pi = S.random_duals(5, seed)
        best = 0
        for k in range(1, 6):
            for perm in itertools.permutations(range(1, 6), k):
                sim = simulate(inst, pi, perm)
                if sim and sim[0] + inst.service + inst.d[sim[2]][0] <= inst.horizon + EPS:
                    best = min(best, sim[1] + inst.d[sim[2]][0])
        assert oracle(inst, pi)[0] == pytest.approx(best, abs=1e-9)


def test_full_rule_equals_the_oracle_in_all_180_cases_and_so_does_no_dominance():
    for seed, width, inst, pi in cases():
        ref, _ = oracle(inst, pi)
        for rule in ("voll", "keine"):
            res = A.price(inst, pi, inst.n, A.RULES[rule])
            assert res.value == pytest.approx(ref, abs=1e-6), (seed, width, rule)
            if res.route:
                assert simulate(inst, pi, res.route) is not None
                assert A.route_value(inst, pi, res.route) == pytest.approx(res.value, abs=1e-9)


def test_selectivity_cost_only_rule_must_differ_from_the_oracle_in_some_cases():
    """Trennschärfe: ohne diese Gegenprobe könnte der Vergleich oben für jede Regel bestehen."""
    differing = sum(1 for _, _, inst, pi in cases() if abs(A.price(inst, pi, inst.n, A.RULES["kosten"]).value - oracle(inst, pi)[0]) > 1e-6)
    assert differing > 0


def test_number_of_labels_without_dominance_equals_feasible_partial_routes_plus_start():
    for seed, width, inst, pi in cases():
        assert A.price(inst, pi, inst.n, None).generated == oracle(inst, pi)[1] + 1, (seed, width)


def test_alive_labels_do_not_dominate_each_other_under_the_full_rule():
    """Unabhängige Invariante: Am Ende gibt es am selben Kunden keine zwei lebenden Labels, von denen eines das andere in allen vier Größen übertrifft."""
    for seed in range(20):
        inst = S.make_instance(8, seed, 80)
        pi = S.random_duals(8, seed)
        res = A.price(inst, pi, 8, A.RULES["voll"])
        alive = [lab for lab, dead in zip(res.labels, res.dead) if not dead]
        for a, b in itertools.permutations(alive, 2):
            if a.node != b.node:
                continue
            assert not (a.cost <= b.cost + EPS and a.time <= b.time + EPS and a.load <= b.load and a.mem & ~b.mem == 0), (seed, a, b)


def test_ng_memory_full_rule_equals_no_dominance_in_all_180_cases():
    """Bezug für k = 3: Ergebnis ohne Dominanz (exakt für k = 3), die volle Regel darf nicht abweichen."""
    for seed, width, inst, pi in cases():
        assert A.price(inst, pi, 3, A.RULES["voll"]).value == pytest.approx(A.price(inst, pi, 3, None).value, abs=1e-6), (seed, width)


def test_non_elementary_value_is_never_above_the_elementary_one():
    for seed, width, inst, pi in list(cases())[:60]:
        assert A.price(inst, pi, 1, A.RULES["voll"]).value <= oracle(inst, pi)[0] + 1e-6


def test_oracle_on_instances_without_triangle_inequality_matches_the_full_rule():
    for seed in range(300):
        inst, pi = S.make_general_instance(seed)
        assert A.price(inst, pi, inst.n, A.RULES["voll"]).value == pytest.approx(oracle(inst, pi)[0], abs=1e-6), seed
