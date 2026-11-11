"""Kern gegen Handrechnung am Handbeispiel (tests/conftest.py) und je Einheit an handgebauten Labels (DEMO-PLAYBOOK §1b).

Die Zahlen der Label-Zählungen je Regel stammen aus einem unabhängigen Skript der Planung (hand_02.py, ohne den Kern dieser Demo; Rohausgabe run_hand_02.log);
alles, was sich in der Hand rechnen lässt, steht als Rechnung da."""

import pytest

import dml_algorithm as A
import dml_scenario as S
from dml_algorithm import Label


def test_conftest_table_equals_the_scenario_module(hand):
    inst, pi = hand
    ref = S.hand_instance()
    assert inst == ref and pi == S.HAND_DUALS


def test_distances_are_manhattan_distances_of_the_grid(hand):
    inst, _ = hand
    assert inst.d[0][6] == abs(5 - 1) + abs(5 - 7)          # Depot (5,5) zu Kunde 6 (1,7)
    assert inst.d[6][2] == abs(1 - 1) + abs(7 - 9)          # (1,7) zu (1,9)
    assert inst.d[2][3] == 1 and inst.d[3][5] == abs(1 - 5) + abs(10 - 10) and inst.d[5][0] == abs(5 - 5) + abs(10 - 5)
    assert all(inst.d[i][j] == inst.d[j][i] and inst.d[i][i] == 0 for i in range(7) for j in range(7))


def test_best_route_value_by_hand(hand):
    """Route 6-2-3-5: Entfernungen 6 + 2 + 1 + 4 + 5, Dualpreise 7 + 12 + 12 + 9; Zeiten: Kunde 6 wartet bis 10, Kunde 2 um 14, Kunde 3 um 17, Kunde 5 um 23, Rückkehr 30."""
    inst, pi = hand
    assert A.route_value(inst, pi, (6, 2, 3, 5)) == (6 + 2 + 1 + 4 + 5) - (7 + 12 + 12 + 9) == -22
    assert A.route_value(inst, pi, (2, 3, 6, 5)) == (8 + 1 + 3 + 7 + 5) - (12 + 12 + 7 + 9) == -16   # eine der beiden Routen mit -16
    t = max(6, 10)                  # Kunde 6: Ankunft 6, Fenster ab 10, also warten
    t = max(t + 2 + 2, 8)           # Kunde 2: Bedienzeit 2, Entfernung 2
    t = max(t + 2 + 1, 9)           # Kunde 3
    t = max(t + 2 + 4, 16)          # Kunde 5
    assert t + 2 + 5 == 30          # Rückkehr zur Zeit 30 <= 36
    best = [r for r in A.enumerate_routes(inst, pi) if r[1] == (6, 2, 3, 5)][0]
    assert best[2] == 30


def test_route_checker_rejects_infeasible_routes(hand):
    inst, pi = hand
    assert A.route_value(inst, pi, (4, 4)) is None                  # Kunde doppelt
    assert A.route_value(inst, pi, (4, 1)) is None                  # Kunde 1 wird nach 17 + 2 + 5 = 24 erreicht, sein Fenster endet bei 16
    assert A.route_value(inst, pi, (1, 2, 3, 4, 5, 6)) is None      # Last 2 + 3 + 3 + 6 + 2 + 2 = 18 > 12
    assert A.route_value(inst, pi, (7,)) is None and A.route_value(inst, pi, (0,)) is None
    assert A.route_value(inst, pi, ()) == 0


def test_enumeration_finds_52_routes_and_the_ranking_of_the_best_five(hand):
    inst, pi = hand
    routes = A.enumerate_routes(inst, pi)
    assert len(routes) == 52
    assert [(rc, r) for rc, r, _ in routes[:2]] == [(-22, (6, 2, 3, 5)), (-18, (2, 6, 3, 5))]
    assert sorted(r for rc, r, _ in routes if rc == -16) == [(2, 3, 6, 5), (3, 2, 6, 5)]
    assert routes[4][:2] == (-15, (2, 3, 5))
    assert routes[1][0] > routes[0][0]          # der beste Weg ist eindeutig
    assert A.best_by_enumeration(inst, pi) == (-22, (6, 2, 3, 5))


def test_number_of_labels_without_dominance_is_one_plus_the_number_of_feasible_partial_routes(hand):
    """Ohne Dominanz entsteht jedes zulässige Teilstück genau einmal; Zählung unabhängig mit einer Rekursion über Teilstücke (ohne Rückkehr)."""
    inst, pi = hand

    def count(i, time, load, visited):
        total = 0
        for j in range(1, 7):
            if visited >> j & 1:
                continue
            arrival = time + (2 if i else 0) + inst.d[i][j]
            if load + inst.demand[j] > 12 or arrival > inst.due[j]:
                continue
            total += 1 + count(j, max(arrival, inst.ready[j]), load + inst.demand[j], visited | 1 << j)
        return total

    assert count(0, 0, 0, 0) + 1 == 53 == A.price(inst, pi, 6, None).generated


# Aus dem unabhängigen Skript der Planung (hand_02.py, run_hand_02.log): bester Wert, Route, erzeugte, gestrichene Labels je Regel
EXPECTED = {
    "keine": (-22, (6, 2, 3, 5), 53, 0),
    "kosten": (-16, (2, 3, 6, 5), 18, 11),
    "kosten_zeit": (-18, (2, 6, 3, 5), 35, 19),
    "kosten_last": (-22, (6, 2, 3, 5), 41, 20),
    "kosten_gedaechtnis": (-22, (6, 2, 3, 5), 45, 15),
    "kosten_zeit_last": (-22, (6, 2, 3, 5), 42, 20),
    "kosten_zeit_gedaechtnis": (-22, (6, 2, 3, 5), 45, 15),
    "kosten_last_gedaechtnis": (-22, (6, 2, 3, 5), 45, 15),
    "voll": (-22, (6, 2, 3, 5), 45, 15),
}


@pytest.mark.parametrize("rule", list(EXPECTED))
def test_each_rule_on_the_hand_example_matches_the_independent_log(hand, rule):
    inst, pi = hand
    res = A.price(inst, pi, 6, A.RULES[rule])
    value, route, generated, dominated = EXPECTED[rule]
    assert (res.value, res.route, res.generated, res.dominated) == (value, route, generated, dominated)
    assert res.alive == generated - dominated == sum(1 for dead in res.dead if not dead)
    assert not res.aborted


def test_loss_pairs_of_the_two_wrong_rules(hand):
    """L6 gegen L13 („nur Kosten“) und L18 gegen L14 („Kosten + Zeit“) mit den Zahlen aus dem Log; Gleichstand L28 gegen L22 bei voller Regel."""
    inst, pi = hand
    r = A.price(inst, pi, 6, A.RULES["kosten"], trace=True)
    assert A.Event("verdraengt", 6, 13) in r.events
    assert r.labels[6][:5] == (10, -1, 2, 1 << 6, 6) and A.route_of(r.labels, 6) == (6,)
    assert r.labels[13][:5] == (12, -9, 5, 1 << 2 | 1 << 6, 6) and A.route_of(r.labels, 13) == (2, 6)
    r = A.price(inst, pi, 6, A.RULES["kosten_zeit"], trace=True)
    assert A.Event("verworfen", 18, 14) in r.events       # das neue Label L18 wird vom älteren L14 verworfen
    assert r.labels[18][:5] == (14, -11, 5, 1 << 2 | 1 << 6, 2) and A.route_of(r.labels, 18) == (6, 2)
    assert r.labels[14][:5] == (12, -14, 6, 1 << 2 | 1 << 3, 2) and A.route_of(r.labels, 14) == (3, 2)
    full = A.price(inst, pi, 6, A.RULES["voll"], trace=True)
    assert A.Event("verworfen", 28, 22) in full.events       # gleiche Labels: das ältere bleibt
    assert A.route_of(full.labels, 28) == (3, 2, 4) and A.route_of(full.labels, 22) == (2, 3, 4)
    assert A.Event("verdraengt", 25, 33) in full.events      # 2-6-3 (Kosten -18) wird vom späteren 6-2-3 (Kosten -22) verdrängt
    assert A.Event("verworfen", 11, 4) in full.events        # 2-4 wird von 4 dominiert, weil {4} in {2,4} liegt


def test_events_add_up_to_the_counts(hand):
    inst, pi = hand
    for name, rule in A.RULES.items():
        r = A.price(inst, pi, 6, rule, trace=True)
        kinds = [e.kind for e in r.events]
        assert kinds.count("bleibt") + kinds.count("verworfen") == r.generated - 1       # jedes erzeugte Label hat genau ein Ereignis (außer dem Start)
        assert kinds.count("verworfen") + kinds.count("verdraengt") == r.dominated


def test_trace_does_not_change_the_result(hand):
    inst, pi = hand
    a, b = A.price(inst, pi, 6, A.RULES["voll"]), A.price(inst, pi, 6, A.RULES["voll"], trace=True)
    assert a[:7] == b[:7] and a.events == () and len(b.events) > 0


# --- Einheiten --------------------------------------------------------------------------------------------------------------------------------

def _label(time=10, cost=-5, load=4, mem=0b110, node=2):
    return Label(time, cost, load, mem, node, -1)


def test_dominates_each_condition_separately():
    base = _label()
    full = A.RULES["voll"]
    assert A.dominates(base, base, full)                                           # Gleichstand: dominiert
    assert not A.dominates(_label(cost=-4), base, full)                           # teurer
    assert not A.dominates(_label(time=11), base, full)                           # später
    assert not A.dominates(_label(load=5), base, full)                            # mehr Last
    assert not A.dominates(_label(mem=0b1010), base, full)                        # besucht {1,3}, nicht Teilmenge von {1,2}
    assert A.dominates(_label(mem=0b010), base, full)                              # {1} ist Teilmenge von {1,2}
    # jede Regel ohne die Bedingung lässt den Verstoß durch
    assert A.dominates(_label(time=11), base, A.RULES["kosten_last_gedaechtnis"])
    assert A.dominates(_label(load=5), base, A.RULES["kosten_zeit_gedaechtnis"])
    assert A.dominates(_label(mem=0b1010), base, A.RULES["kosten_zeit_last"])
    assert A.dominates(_label(time=11, load=5, mem=0b1010), base, A.RULES["kosten"])
    assert not A.dominates(_label(cost=-4, time=1, load=0, mem=0), base, A.RULES["kosten"])


def test_dominates_is_a_partial_order_on_hand_labels():
    """Reflexiv, antisymmetrisch bis auf Gleichheit, transitiv (volle Regel) an einer Kette von Hand."""
    a, b, c = _label(time=8, cost=-9, load=2, mem=0b010), _label(time=9, cost=-7, load=3, mem=0b110), _label(time=10, cost=-5, load=4, mem=0b110)
    full = A.RULES["voll"]
    assert A.dominates(a, b, full) and A.dominates(b, c, full) and A.dominates(a, c, full)
    assert not A.dominates(b, a, full) and not A.dominates(c, b, full)


def test_conditions_agree_with_dominates():
    base = _label()
    for other in (base, _label(cost=-4), _label(time=11), _label(load=5), _label(mem=0b1010), _label(mem=0b010)):
        cond = A.conditions(other, base)
        assert list(cond) == list(A.CONDITION_NAMES)
        assert all(cond.values()) == A.dominates(other, base, A.RULES["voll"])


def test_extend_reasons_for_rejection(hand):
    inst, pi = hand
    ng = A.ng_masks(inst, 6)
    start = Label(0, 0, 0, 0, 0, -1)
    one = A.extend(inst, pi, ng, start, 0, 1)
    assert one == Label(6, 4 - 8, 2, 1 << 1, 1, 0)          # Entfernung 4, Dualpreis 8, Ankunft 4 vor Fensterbeginn 6: Warten bis 6
    assert A.extend(inst, pi, ng, one, 1, 1) is None        # derselbe Kunde
    assert A.extend(inst, pi, ng, Label(0, 0, 11, 0, 0, -1), 0, 1) is None   # Last 11 + 2 > 12
    assert A.extend(inst, pi, ng, Label(0, 0, 10, 0, 0, -1), 0, 1) is not None   # Last genau 12 ist erlaubt
    late = Label(20, 0, 0, 0, 6, -1)
    assert A.extend(inst, pi, ng, late, 0, 2) is None       # 20 + 2 + 2 = 24 > 16


def test_ng_masks_hand_values(hand):
    inst, _ = hand
    assert A.ng_masks(inst, 6) == [0] + [sum(1 << i for i in range(1, 7))] * 6          # k = n: jeder Kunde im Gedächtnis
    m1 = A.ng_masks(inst, 1)
    assert m1 == [0] + [1 << j for j in range(1, 7)]                                       # k = 1: nur der Kunde selbst
    m2 = A.ng_masks(inst, 2)
    assert m2[2] == 1 << 2 | 1 << 3 and m2[3] == 1 << 3 | 1 << 2                          # Kunde 2 und 3 liegen am nächsten beieinander (Abstand 1)


def test_price_is_deterministic_and_pure(hand):
    inst, pi = hand
    assert A.price(inst, pi, 6, A.RULES["voll"], trace=True) == A.price(inst, pi, 6, A.RULES["voll"], trace=True)


def test_routes_of_lists_improving_routes_only(hand):
    inst, pi = hand
    res = A.price(inst, pi, 6, A.RULES["keine"])
    routes = A.routes_of(res, 5)
    assert routes[0] == (-22, (6, 2, 3, 5)) and len(routes) == 5
    assert all(rc < 0 for rc, _ in routes) and [rc for rc, _ in routes] == sorted(rc for rc, _ in routes)


def test_every_rule_changes_the_result_on_at_least_one_instance():
    """Zweig-Test (DEMO-PLAYBOOK §0, §1b): jede Bedingung ändert auf mindestens einer Instanz die Label-Zahl oder das Ergebnis gegenüber der Regel ohne sie.
    Elementar (k = n) ist die Last-Bedingung redundant, wenn das Gedächtnis geprüft wird; sie wirkt erst bei k = 3."""
    changed = {"Zeit": False, "Last_elementar": False, "Last_k3": False, "Gedaechtnis": False}
    for seed in range(60):
        for width in (30, 80, 200):
            inst = S.make_instance(7, seed, width)
            pi = S.random_duals(7, seed)
            full = A.price(inst, pi, 7, A.RULES["voll"]).generated
            if A.price(inst, pi, 7, A.RULES["kosten_last_gedaechtnis"]).generated != full:
                changed["Zeit"] = True
            if A.price(inst, pi, 7, A.RULES["kosten_zeit_gedaechtnis"]).generated != full:
                changed["Last_elementar"] = True
            if A.price(inst, pi, 7, A.RULES["kosten_zeit_last"]).generated != full:
                changed["Gedaechtnis"] = True
            if A.price(inst, pi, 3, A.RULES["kosten_zeit_gedaechtnis"]).generated != A.price(inst, pi, 3, A.RULES["voll"]).generated:
                changed["Last_k3"] = True
    assert changed == {"Zeit": True, "Last_elementar": False, "Last_k3": True, "Gedaechtnis": True}
