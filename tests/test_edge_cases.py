"""Randfälle des Label-Verfahrens (DEMO-PLAYBOOK §12): n = 1, n = 2, Gleichstand, inklusive Grenzen, leere Route, Abbruch."""

import pytest

import dml_algorithm as A
import dml_evaluation as ev
import dml_scenario as S
from dml_scenario import Instance


def _line_instance(n, dist=5.0, due=100.0, demand=5, capacity=70, horizon=300.0, ready=0.0):
    """Kunden auf einer Linie im Abstand `dist`; Fenster [ready, due]."""
    pts = [(float(i) * dist, 0.0) for i in range(n + 1)]
    d = tuple(tuple(abs(a[0] - b[0]) for b in pts) for a in pts)
    return Instance(n, tuple(pts), d, (0,) + (demand,) * n, (0.0,) + (ready,) * n, (horizon,) + (due,) * n, 10.0, horizon, capacity)


def test_one_customer():
    inst = _line_instance(1)
    pi = (0.0, 20.0)
    res = A.price(inst, pi, 1, A.RULES["voll"])
    assert res.route == (1,) and res.value == pytest.approx(5 + 5 - 20)
    assert res.generated == 2 and res.dominated == 0


def test_exactly_two_customers_and_dominance_between_them():
    inst = _line_instance(2)
    pi = (0.0, 20.0, 20.0)
    for rule in ("keine", "kosten", "voll"):
        res = A.price(inst, pi, 2, A.RULES[rule])
        assert res.route == (1, 2) and res.value == pytest.approx(5 + 5 + 10 - 40)    # Weg 0-1-2-0: 5 + 5 + 10, Dualpreise 20 + 20


def test_empty_route_when_no_route_has_negative_reduced_cost():
    inst = _line_instance(3)
    res = A.price(inst, (0.0, 0.0, 0.0, 0.0), 3, A.RULES["voll"])
    assert res.route == () and res.value == 0
    assert A.best_by_enumeration(inst, (0.0,) * 4) == (0, ())
    assert A.routes_of(res) == []


def test_ties_the_older_label_stays():
    """Zwei gleiche Labels am Kunden 3 (Wege 1-3 und 2-3 mit gleicher Zeit, Kosten, Last): Bei „nur Kosten“ bleibt das ältere, das jüngere wird verworfen."""
    d = ((0.0, 5.0, 5.0, 10.0), (5.0, 0.0, 100.0, 5.0), (5.0, 100.0, 0.0, 5.0), (10.0, 5.0, 5.0, 0.0))
    inst = Instance(3, ((0.0, 0.0),) * 4, d, (0, 5, 5, 5), (0.0,) * 4, (300.0,) * 4, 10.0, 300.0, 70)
    pi = (0.0, 20.0, 20.0, 20.0)
    res = A.price(inst, pi, 3, A.RULES["kosten"], trace=True)
    at3 = [i for i, lab in enumerate(res.labels) if lab.node == 3 and not res.dead[i]]
    assert len(at3) == 1 and A.route_of(res.labels, at3[0]) == (1, 3)          # das ältere (über Kunde 1) bleibt
    lost = [A.route_of(res.labels, e.label) for e in res.events if e.kind == "verworfen" and res.labels[e.label].node == 3]
    assert (2, 3) in lost
    # bei der vollen Regel bleiben beide: das Gedächtnis ({1,3} gegen {2,3}) trennt sie
    full = A.price(inst, pi, 3, A.RULES["voll"])
    assert sorted(A.route_of(full.labels, i) for i, lab in enumerate(full.labels) if lab.node == 3 and not full.dead[i] and len(A.route_of(full.labels, i)) == 2) == [(1, 3), (2, 3)]


def test_same_time_but_higher_cost_does_not_dominate():
    a = A.Label(10, -5, 4, 0b10, 1, -1)
    b = A.Label(10, -6, 4, 0b10, 1, -1)
    assert not A.dominates(a, b, A.RULES["voll"]) and A.dominates(b, a, A.RULES["voll"])


def test_load_exactly_equal_to_capacity_is_allowed_one_more_is_not():
    inst = _line_instance(2, demand=35, capacity=70)
    assert A.price(inst, (0.0, 50.0, 50.0), 2, A.RULES["voll"]).route == (1, 2)        # 35 + 35 = 70 = Kapazität
    over = _line_instance(2, demand=35, capacity=69)
    assert len(A.price(over, (0.0, 50.0, 50.0), 2, A.RULES["voll"]).route) == 1


def test_return_exactly_at_the_horizon_is_allowed():
    inst = _line_instance(1, dist=10.0, horizon=40.0, due=30.0)   # hin 10, bedienen 10, zurück 10: Rückkehr zur Zeit 30; Horizont 30 reicht gerade
    tight = Instance(inst.n, inst.points, inst.d, inst.demand, inst.ready, inst.due, inst.service, 30.0, inst.capacity)
    assert A.price(tight, (0.0, 100.0), 1, A.RULES["voll"]).route == (1,)
    too_tight = Instance(inst.n, inst.points, inst.d, inst.demand, inst.ready, inst.due, inst.service, 29.9, inst.capacity)
    assert A.price(too_tight, (0.0, 100.0), 1, A.RULES["voll"]).route == ()


def test_all_windows_open_no_waiting():
    inst = S.make_instance(7, 3, 10_000)       # Fenster so breit, dass sie auf [Hinfahrt, H - Bedienzeit - Rückfahrt] begrenzt sind
    pi = S.random_duals(7, 3)
    ref, _ = A.best_by_enumeration(inst, pi)
    assert A.price(inst, pi, 7, A.RULES["voll"]).value == pytest.approx(ref, abs=1e-6)


def test_abort_at_max_labels_is_reported():
    inst, pi = S.make_instance(12, 2, 200), S.random_duals(12, 2)
    res = A.price(inst, pi, 12, None, max_labels=100)
    assert res.aborted and 100 <= res.generated < 100 + inst.n
    assert not A.price(inst, pi, 12, A.RULES["voll"]).aborted


def test_size_experiment_with_abort_has_no_factor():
    r = ev.size_experiment(12, 200, 2, max_labels=50)
    assert r.aborted and r.factor is None and r.same_value is None


def test_ng_masks_clip_k_into_the_valid_range():
    inst = S.make_instance(4, 0, 80)
    assert A.ng_masks(inst, 99) == A.ng_masks(inst, 4)
    assert A.ng_masks(inst, 0) == A.ng_masks(inst, 1)


def test_label_text_and_numbers_formatting():
    assert ev.fmt_num(-22) == "−22" and ev.fmt_num(3.0) == "3" and ev.fmt_num(1.4824) == "1,48" and ev.fmt_num(-0.5, 1) == "−0,5"
    assert ev.fmt_int(51322) == "51 322" and ev.fmt_pct(37.2222) == "37,2 %" and ev.fmt_pct(1.216, 3) == "1,216 %"
    assert ev.fmt_dec(1.0) == "1,00" and ev.fmt_dec(4.857) == "4,86" and ev.fmt_dec(0.5, 1) == "0,5"
    assert ev.fmt_set(0b1100, 6) == "{2,3}" and ev.fmt_set(0, 6) == "{}" and ev.fmt_route(()) == "keine" and ev.fmt_route((6, 2)) == "6-2"
