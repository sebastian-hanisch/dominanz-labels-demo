"""Jede Zahl der README und der App-Texte wird hier nachgerechnet (DEMO-PLAYBOOK §4, §11a). Zeiten stehen in keinem Test.

Die festen Messreihen (data/*.json) stammen aus den Rohausgaben der Messungen der Planung (Quelle je Zeile). Hier werden sie mit dem Kern dieser Demo **neu gerechnet**:
Regel-Tabelle (180 Fälle, elementar und Gedächtnis k = 3), jede Zelle des Wachstums (10 Instanzen), die Spaltenerzeugung für alle 10 Instanzen, ein Lauf der 30-Kunden-Reihe
und die Gegenprobe ohne Dreiecksungleichung. Plattformabhängig ist nur der Weg des LP-Lösers in der Spaltenerzeugung bei „nur Kosten“: dort stehen Bänder statt exakter Gleichheit."""

import json
import statistics
import sys
from pathlib import Path

import pytest

import dml_algorithm as A
import dml_constants as C
import dml_evaluation as ev
import dml_scenario as S

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def cases180():
    out = []
    for seed in range(60):
        for width in (30, 80, 200):
            inst, pi = S.make_instance(7, seed, width), S.random_duals(7, seed)
            out.append((inst, pi, A.best_by_enumeration(inst, pi)[0]))
    return out


@pytest.fixture(scope="module")
def table():
    return ev.load_rule_table()


# --- Regel-Tabelle ----------------------------------------------------------------------------------------------------------------------------

def test_rule_table_elementary_is_recomputed_exactly(cases180, table):
    assert len(cases180) == table["faelle"] == 180
    for row in table["elementar"]:
        miss, labels = 0, []
        for inst, pi, ref in cases180:
            res = A.price(inst, pi, inst.n, A.RULES[row["regel"]])
            labels.append(res.generated)
            miss += abs(res.value - ref) > 1e-6
        assert miss == row["verfehlt"], row["regel"]
        assert round(statistics.median(labels)) == row["labels_median"] and round(statistics.mean(labels), 1) == row["labels_mittel"] and max(labels) == row["labels_max"], row["regel"]


def test_rule_table_with_ng_memory_k3_is_recomputed_exactly(cases180, table):
    refs = [A.price(inst, pi, 3, None).value for inst, pi, _ in cases180]
    for row in table["ng3"]:
        miss, labels = 0, []
        for (inst, pi, _), ref in zip(cases180, refs):
            res = A.price(inst, pi, 3, A.RULES[row["regel"]])
            labels.append(res.generated)
            miss += abs(res.value - ref) > 1e-6
        assert miss == row["weicht_ab"] and round(statistics.median(labels)) == row["labels_median"] and round(statistics.mean(labels), 1) == row["labels_mittel"], row["regel"]


def test_the_counts_named_in_the_readme_and_the_app(table):
    el = {r["regel"]: r for r in table["elementar"]}
    ng = {r["regel"]: r for r in table["ng3"]}
    assert el["voll"]["verfehlt"] == 0 and el["keine"]["verfehlt"] == 0 and el["kosten"]["verfehlt"] == 67
    assert 100 * 67 / 180 == pytest.approx(37.2, abs=0.05) and "67 von 180 Fällen (37,2 %)" in README
    assert [el[r]["verfehlt"] for r in ("kosten_gedaechtnis", "kosten_zeit_gedaechtnis", "kosten_last_gedaechtnis", "voll")] == [0, 0, 0, 0]
    assert [ng[r]["weicht_ab"] for r in ("kosten", "kosten_zeit", "kosten_last", "kosten_gedaechtnis", "kosten_zeit_last", "kosten_zeit_gedaechtnis",
                                         "kosten_last_gedaechtnis", "voll")] == [72, 35, 22, 31, 14, 10, 2, 0]
    assert "Abweichungen: nur Kosten 72, Kosten + Zeit 35, Kosten + Last 22, Kosten + Gedächtnis 31, Kosten + Zeit + Last 14, Kosten + Zeit + Gedächtnis 10, Kosten + Last + Gedächtnis 2, volle Regel 0." in README


def test_the_readme_rule_table_rows_equal_the_data(table):
    for a, b in zip(ev.rule_rows(table, "elementar"), ev.rule_rows(table, "ng3")):
        row = (f"| {C.RULE_LABELS[a['regel']]} | {a['verfehlt']} ({ev.fmt_pct(100 * a['verfehlt'] / 180)}) | {ev.fmt_int(a['labels_median'])} / "
               f"{str(a['labels_mittel']).replace('.', ',')} / {ev.fmt_int(a['labels_max'])} | {b['weicht_ab']} ({ev.fmt_pct(100 * b['weicht_ab'] / 180)}) | "
               f"{b['labels_median']} / {str(b['labels_mittel']).replace('.', ',')} |").replace(" ", " ")
        assert row in README, row


def test_last_condition_is_redundant_when_the_memory_is_checked_but_not_at_k3(cases180):
    same = [A.price(i, p, 7, A.RULES["kosten_zeit_gedaechtnis"]).generated == A.price(i, p, 7, A.RULES["voll"]).generated for i, p, _ in cases180]
    assert all(same)
    differ3 = sum(A.price(i, p, 3, A.RULES["kosten_zeit_gedaechtnis"]).generated != A.price(i, p, 3, A.RULES["voll"]).generated for i, p, _ in cases180)
    assert differ3 > 0


def test_ratio_and_size_of_the_miss(cases180, table):
    ratios, found = [], []
    for inst, pi, ref in cases180:
        ratios.append(A.price(inst, pi, 7, None).generated / A.price(inst, pi, 7, A.RULES["voll"]).generated)
        res = A.price(inst, pi, 7, A.RULES["kosten"])
        if abs(res.value - ref) > 1e-6:
            found.append(res.value / ref)
    r = table["verhaeltnis_keine_zu_voll"]
    assert (round(statistics.median(ratios), 2), round(min(ratios), 2), round(max(ratios), 2)) == (r["median"], r["min"], r["max"]) == (1.42, 1.0, 4.86)
    m = table["verfehlung_nur_kosten"]
    assert len(found) == m["faelle"] == 67
    assert (round(statistics.median(found), 3), round(min(found), 3)) == (m["wert_median"], m["wert_min"]) == (0.876, 0.183)
    assert all(f > 0 for f in found) and m["ohne_verbessernde_route"] == 0
    for piece in ("im Median 87,6 % des besten reduzierten Kostenwertes (Minimum 18,3 %) und in allen 67 noch eine verbessernde Route", "im Median das 1,42-Fache", "(Minimum 1,00, Maximum 4,86)"):
        assert piece in README, piece


# --- Wachstum ---------------------------------------------------------------------------------------------------------------------------------

GROWTH = ev.load_growth()["teil_b"]


@pytest.mark.parametrize("cell", GROWTH, ids=[f"b{c['breite']}_n{c['n']}" for c in GROWTH])
def test_growth_cell(cell):
    n, width = cell["n"], cell["breite"]
    none, full, factors = [], [], []
    for seed in range(10):
        inst, pi = S.make_instance(n, seed, width), S.random_duals(n, seed)
        a, b = A.price(inst, pi, n, None).generated, A.price(inst, pi, n, A.RULES["voll"]).generated
        none.append(a)
        full.append(b)
        factors.append(a / b)
    assert cell["instanzen"] == 10 and cell["quelle"]
    assert (round(statistics.median(none)), round(statistics.median(full))) == (cell["labels_ohne_median"], cell["labels_voll_median"])
    assert (round(statistics.median(factors), 2), round(max(factors), 2), round(statistics.mean(factors), 2), round(min(factors), 2)) == (
        cell["faktor_median"], cell["faktor_max"], cell["faktor_mittel"], cell["faktor_min"])


def test_growth_rows_in_the_readme_and_headline_numbers():
    for r in GROWTH:
        f = lambda x: f"{x:.2f}".replace(".", ",")  # noqa: E731
        row = (f"| {r['breite']} | {r['n']} | {ev.fmt_int(r['labels_ohne_median'])} | {ev.fmt_int(r['labels_voll_median'])} | {f(r['faktor_median'])} | "
               f"{f(r['faktor_mittel'])} | {f(r['faktor_max'])} |").replace(" ", " ")
        assert row in README, row
    cell = {(r["breite"], r["n"]): r for r in GROWTH}
    assert (cell[(80, 7)]["faktor_median"], cell[(200, 7)]["faktor_median"], cell[(80, 20)]["faktor_median"], cell[(200, 20)]["faktor_median"]) == (1.35, 2.08, 2.36, 3.49)
    assert max(GROWTH, key=lambda r: r["faktor_max"])["faktor_max"] == 6.02 and cell[(200, 14)]["faktor_max"] == 6.02
    assert "bei 7 Kunden ist der Faktor im Median 1,35 (Breite 80) bzw. 2,08 (Breite 200), bei 20 Kunden 2,36 bzw. 3,49; größter Einzelfaktor 6,02 (Breite 200, 14 Kunden)" in README
    assert all(r["faktor_min"] <= r["faktor_median"] <= r["faktor_max"] and r["faktor_min"] <= r["faktor_mittel"] <= r["faktor_max"] for r in GROWTH)


def test_growth_v1_rows_and_one_recomputed_run():
    rows = ev.load_growth()["v1"]
    assert len(rows) == 9 and all(r["n"] == 30 and r["laeufe"] == 6 and r["quelle"] for r in rows)
    shares = [r["anteil_verworfen_prozent"] for r in rows]
    assert (min(shares), max(shares)) == (78.2, 91.4) and "78,2 bis 91,4 %" in README
    sys.path.insert(0, str(ROOT / "tools"))
    pytest.importorskip("scipy")
    from colgen_ref import colgen

    run = colgen(S.make_instance(30, 0, 40), 5, A.RULES["voll"])        # Zeile Breite 40, Seed 0, k = 5 der Messreihe: Anteil 0,767, Schranke 862,5837
    assert run["dominated"] / run["generated"] == pytest.approx(0.767, abs=0.03)
    assert run["bound"] == pytest.approx(862.5837, abs=1e-2)


# --- Spaltenerzeugung -------------------------------------------------------------------------------------------------------------------------

def test_colgen_all_ten_instances_recomputed_and_summary():
    pytest.importorskip("scipy")
    sys.path.insert(0, str(ROOT / "tools"))
    from colgen_ref import colgen

    data = ev.load_colgen()
    assert (data["kunden"], data["breite"], data["instanzen"]) == (10, 80, 10) and len(data["zeilen"]) == 10 and all(r["quelle"] for r in data["zeilen"])
    higher = 0
    for row in data["zeilen"]:
        inst = S.make_instance(10, row["seed"], 80)
        full, cost = colgen(inst, 10, A.RULES["voll"]), colgen(inst, 10, A.RULES["kosten"])
        assert full["bound"] == pytest.approx(row["schranke_voll"], abs=1e-3), row["seed"]          # unabhängig vom Weg des Löser: die Schranke der vollen Regel
        assert cost["bound"] >= full["bound"] - 1e-6, row["seed"]                                    # fehlende Spalten können die Schranke nur erhöhen
        higher += cost["bound"] > full["bound"] + 1e-6
    # Bänder statt exakter Gleichheit (Weg des Lösers ist plattformabhängig); die genaue Zählung steht in den Daten und unten
    assert 3 <= higher <= 7
    instance7 = S.make_instance(10, 7, 80)
    assert 100 * (colgen(instance7, 10, A.RULES["kosten"])["bound"] / colgen(instance7, 10, A.RULES["voll"])["bound"] - 1) > 5.0


def test_colgen_summary_numbers_in_data_and_texts():
    s = ev.colgen_summary(ev.load_colgen()["zeilen"])
    assert (s["instanzen"], s["hoeher"]) == (10, 5)
    assert round(s["mittel"], 3) == 1.216 and s["maximum"] == 8.476
    _, text = ev.verdict_colgen(s)
    assert "5 von 10 Instanzen" in text and "Mittel 1,216 %" in text and "Maximum 8,476 %" in text
    for piece in ("in 5 von 10 Instanzen bei einer höheren Zahl", "1,216 %", "8,476 %", "1 (1,161 %), 2 (0,755 %), 4 (0,077 %), 6 (1,691 %) und 7 (8,476 %)"):
        assert piece in README, piece
    rows = ev.load_colgen()["zeilen"]
    assert [r["seed"] for r in rows if r["unterschied_prozent"] > 1e-9] == [1, 2, 4, 6, 7]


# --- Gegenprobe ohne Dreiecksungleichung ------------------------------------------------------------------------------------------------------

def test_counter_sample_counts():
    missed = ev.counter_sweep()
    assert ev.COUNTER_INSTANCES == 3000
    assert {k: len(v) for k, v in missed.items()} == {"kosten": 413, "kosten_zeit": 144, "kosten_last": 42, "kosten_gedaechtnis": 1, "kosten_zeit_last": 0, "voll": 0}
    assert missed["kosten_gedaechtnis"] == [209]
    assert "nur Kosten 413, Kosten + Zeit 144, Kosten + Last 42, **Kosten + Gedächtnis 1** (Zufalls-Seed 209), Kosten + Zeit + Last 0, volle Regel 0." in README


def test_counter_instance_209_by_hand():
    """Das Gegenbeispiel: „Kosten + Gedächtnis“ verfehlt den besten Weg, die volle Regel findet ihn (gegen die Aufzählung)."""
    inst, pi = S.make_general_instance(209)
    best = A.best_by_enumeration(inst, pi)
    assert A.price(inst, pi, inst.n, A.RULES["voll"]).value == pytest.approx(best[0], abs=1e-6)
    assert A.price(inst, pi, inst.n, A.RULES["kosten_gedaechtnis"]).value > best[0] + 1.0


# --- Größenversuch und Presets ----------------------------------------------------------------------------------------------------------------

def test_size_experiment_numbers_of_the_presets_and_the_default():
    r = ev.size_experiment(20, 200, 1)
    assert (r.runs["keine"].generated, r.runs["voll"].generated) == (42863, 12361) and round(r.factor, 2) == 3.47 and r.same_value
    r = ev.size_experiment(10, 80, 1)
    assert (r.runs["keine"].generated, r.runs["voll"].generated, round(r.factor, 2)) == (151, 102, 1.48)
    r = ev.size_experiment(7, 80, 4)
    assert (r.runs["keine"].generated, r.runs["voll"].generated, round(r.factor, 2)) == (108, 102, 1.06)


def test_size_run_counts_add_up():
    r = ev.size_experiment(9, 80, 3)
    for run in r.runs.values():
        assert 1 + sum(run.alive_per_customer) + sum(run.dominated_per_customer) == run.generated
        assert sum(run.dominated_per_customer) == run.dominated
    assert r.runs["keine"].dominated == 0


# --- Handbeispiel in der README ---------------------------------------------------------------------------------------------------------------

def test_hand_example_numbers_in_the_readme(hand):
    inst, pi = hand
    routes = A.enumerate_routes(inst, pi)
    assert len(routes) == 52 and routes[0][:2] == (-22, (6, 2, 3, 5)) and routes[1][0] == -18
    for piece in ("52 zulässige Routen (Aufzählung, 6 Kunden, elementar); beste 6-2-3-5 mit reduzierten Kosten −22, zweitbeste −18",
                  "keine 53 / 0; nur Kosten 18 / 11; Kosten + Zeit 35 / 19; Kosten + Last 41 / 20; Kosten + Gedächtnis 45 / 15; Kosten + Zeit + Last 42 / 20; "
                  "Kosten + Zeit + Gedächtnis 45 / 15; Kosten + Last + Gedächtnis 45 / 15; volle Regel 45 / 15",
                  "„nur Kosten“ findet 2-3-6-5 mit −16 (die Aufzählung kennt zwei gleich gute Wege mit −16, 2-3-6-5 und 3-2-6-5; die Regel erzeugt 3-2-6-5 nicht, "
                  "weil das Label des Teilwegs 3 vom Label des Teilwegs 2-3 verdrängt wird), „Kosten + Zeit“ findet 2-6-3-5 mit −18"):
        assert piece in README, piece


def test_app_texts_without_a_measurement_in_the_tests_are_absent():
    """Die Zeitangabe steht nur als „Messung dieser README, nicht im Test“ in der README und in keinem App-Text."""
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "26,4" not in app and "4,2 s" not in app
    assert json.loads((ROOT / "data" / "wachstum.json").read_text(encoding="utf-8"))["teil_b"]


# --- Instanzen: die Konstanten, die README und App nennen --------------------------------------------------------------------------------------

def test_instance_constants_named_in_the_texts():
    """Quadrat 100 x 100, Depot in der Mitte, Fahrzeit gleich Entfernung, Bedienzeit 10, Kapazität 70, Horizont 300, Fensterbreite höchstens die gewählte; Dualpreise zwischen 20 und 70."""
    for width in (30, 80, 200):
        inst = S.make_instance(12, 5, width)
        assert (inst.service, inst.capacity, inst.horizon, inst.points[0]) == (10.0, 70, 300.0, (50.0, 50.0))
        assert all(0 <= x <= 100 and 0 <= y <= 100 for x, y in inst.points)
        assert all(inst.d[i][j] == pytest.approx(((inst.points[i][0] - inst.points[j][0]) ** 2 + (inst.points[i][1] - inst.points[j][1]) ** 2) ** 0.5) for i in range(13) for j in range(13))
        assert all(inst.due[i] - inst.ready[i] <= width + 1e-9 for i in range(1, 13)) and all(5 <= inst.demand[i] <= 25 for i in range(1, 13))
    duals = [x for seed in range(20) for x in S.random_duals(10, seed)[1:]]
    assert 20 <= min(duals) and max(duals) <= 70 and S.random_duals(4, 1)[0] == 0.0


def test_counter_instance_constants_named_in_the_texts():
    """Gegenprobe: 6 Kunden, Fahrzeiten zufällig zwischen 5 und 60 (nicht symmetrisch, Dreiecksungleichung verletzt), Fenster der Breite genau 30 (nicht beschnitten)."""
    asymmetric = violates = 0
    for seed in range(200):
        inst, pi = S.make_general_instance(seed)
        assert inst.n == 6 and all(5 <= inst.d[i][j] < 60 for i in range(7) for j in range(7) if i != j) and all(inst.d[i][i] == 0 for i in range(7))
        assert all(abs(inst.due[i] - inst.ready[i] - 30) < 1e-9 for i in range(1, 7)) and all(20 <= pi[i] <= 70 for i in range(1, 7))
        asymmetric += inst.d[1][2] != inst.d[2][1]
        violates += any(inst.d[a][c] > inst.d[a][b] + inst.d[b][c] for a in range(7) for b in range(7) for c in range(7) if len({a, b, c}) == 3)
    assert asymmetric > 150 and violates > 100


def test_the_seed_of_the_counter_sample_named_in_the_texts_exists():
    assert "Zufalls-Seeds 0 bis 2999" in README and ev.COUNTER_INSTANCES == 3000


# --- Aussagen nach unabhängiger Prüfung: Gedächtnis, Mediane, beschnittene Fenster -----------------------------------------------------------------

def test_memory_k3_forgets_a_customer_that_is_not_among_the_nearest_of_the_next_stop():
    """README und App: „Gedächtnis k = 3“ heißt nicht „erst nach drei weiteren Halten“. Instanz n = 7, Breite 200, Zufalls-Seed 3: Kunde 3 gehört nicht zu den
    3 nächsten Kunden von 5 (einschließlich 5), also ist er nach der Route 3-5 vergessen und die Route 3-5-3 entsteht schon nach einem Halt dazwischen; elementar nicht."""
    inst, pi = S.make_instance(7, 3, 200), S.random_duals(7, 3)
    ng3, ng7 = A.ng_masks(inst, 3), A.ng_masks(inst, 7)
    assert not (ng3[5] >> 3) & 1 and (ng3[5] >> 5) & 1
    start = A.Label(0, 0, 0, 0, 0, -1)
    chain = []
    for ng in (ng3, ng7):
        l1 = A.extend(inst, pi, ng, start, 0, 3)
        l2 = A.extend(inst, pi, ng, l1, 1, 5)
        chain.append(A.extend(inst, pi, ng, l2, 2, 3))
    assert chain[0] is not None and chain[0].node == 3 and chain[1] is None


def test_medians_in_the_tables_are_rounded_halves(cases180):
    """Die Mediane der Tabellen stehen als ganze Zahlen; die README nennt 58 statt 58,5, 40 statt 39,5, 56 statt 56,5 (Regel-Tabelle) und 94 statt 93,5, 60 statt 60,5 (Wachstum)."""
    def median(k, rule):
        return statistics.median(A.price(inst, pi, k, A.RULES[rule]).generated for inst, pi, _ in cases180)
    assert median(7, "kosten_gedaechtnis") == 58.5 and median(3, "kosten_gedaechtnis") == 39.5 and median(3, "kosten_last_gedaechtnis") == 56.5
    none, full = [], []
    for seed in range(10):
        inst, pi = S.make_instance(7, seed, 80), S.random_duals(7, seed)
        none.append(A.price(inst, pi, 7, None).generated)
        full.append(A.price(inst, pi, 7, A.RULES["voll"]).generated)
    assert (statistics.median(none), statistics.median(full)) == (93.5, 60.5)
    for stueck in ("58 statt 58,5, 40 statt 39,5 und 56 statt 56,5", "94 statt 93,5 und 60 statt 60,5"):
        assert stueck in README, stueck


def test_windows_are_cut_to_the_reachable_span_so_that_the_width_is_only_an_upper_bound():
    inst = S.make_instance(12, 5, 200)
    widths = [inst.due[i] - inst.ready[i] for i in range(1, 13)]
    assert max(widths) <= 200 + 1e-9 and min(widths) < 200 - 1e-9
    assert "Fensterbreite höchstens 30, 80 oder 200, auf die erreichbare Zeitspanne beschnitten" in README


# --- Korrekturliste der Prüfer: Bezug der Prozentwerte, Dreiecksungleichung, Last und Gedächtnis, Steigerungswörter ----------------------------------

def test_colgen_percentages_are_the_gap_to_the_bound_of_the_full_rule_relative_to_it():
    """Unterschied (%) = (Schranke „nur Kosten“ − Schranke der vollen Regel) / Schranke der vollen Regel; das Mittel läuft über alle 10 Instanzen, auch über die 5 mit Unterschied 0."""
    rows = ev.load_colgen()["zeilen"]
    for r in rows:
        assert r["unterschied_prozent"] == pytest.approx(100 * (r["schranke_kosten"] / r["schranke_voll"] - 1), abs=0.0015), r["seed"]
    s = ev.colgen_summary(rows)
    assert sum(1 for r in rows if r["unterschied_prozent"] <= 1e-9) == 5 and round(sum(r["unterschied_prozent"] for r in rows), 2) == 12.16 and round(s["mittel"], 3) == 1.216
    for piece in ("Abstand zur Schranke der vollen Regel, bezogen auf diese: Mittel 1,216 %, Maximum 8,476 %; das Mittel läuft über alle 10 Instanzen, auch über die 5 ohne Unterschied",
                  "bezogen auf die Schranke der vollen Regel; das Mittel von 1,216 % läuft über alle 10 Instanzen, auch über die 5 mit Unterschied 0 (Summe der Prozentwerte 12,16, geteilt durch 10)"):
        assert piece in README, piece


def test_counter_sample_violates_the_triangle_inequality_in_every_instance():
    """Die Gegenprobe erzwingt die Dreiecksungleichung nicht; gemessen: in jeder der 3 000 Instanzen ist sie bei mindestens einem Knotentripel verletzt, im Zufalls-Seed 209 bei 31 von 210."""
    def violated(inst):
        nodes = range(inst.n + 1)
        return sum(1 for a in nodes for b in nodes for c in nodes if len({a, b, c}) == 3 and inst.d[a][c] > inst.d[a][b] + inst.d[b][c] + 1e-12)

    counts = [violated(S.make_general_instance(seed)[0]) for seed in range(ev.COUNTER_INSTANCES)]
    assert all(c > 0 for c in counts)
    assert counts[209] == 31 and 7 * 6 * 5 == 210
    for piece in ("zufällige, nicht symmetrische Fahrzeiten zwischen 5 und 60 (Dreiecksungleichung nicht erzwungen; gemessen: in allen 3 000 Instanzen bei mindestens einem Knotentripel verletzt, "
                  "im Zufalls-Seed 209 bei 31 von 210 Knotentripeln; Zufalls-Seeds 0 bis 2999, elementar)",
                  "(zufällige statt euklidischer Fahrzeiten, andere Lage der Fenster), die Kundenzahl (6 statt 7) und die Fensterbreite (immer genau 30 statt höchstens 30, 80 oder 200)",
                  "ob die Dreiecksungleichung die Ursache ist, ist nicht untersucht"):
        assert piece in README, piece
    assert "ohne Dreiecksungleichung" not in README


def test_growth_median_factor_rises_with_n_and_width():
    """Die Aussage „mit der Kundenzahl größer oder gleich, bei Breite 200 höher als bei 80“ (README, App) steht an den Zellen der Messreihe; Zahlen der Einleitung und des Kopfkommentars."""
    by = {(r["breite"], r["n"]): r["faktor_median"] for r in GROWTH}
    equal_steps = []
    for width in (80, 200):
        ns = sorted(n for w, n in by if w == width)
        assert all(by[(width, a)] <= by[(width, b)] for a, b in zip(ns, ns[1:])), width
        equal_steps += [(width, a, b) for a, b in zip(ns, ns[1:]) if by[(width, a)] == by[(width, b)]]
    assert equal_steps == [(80, 8, 9), (80, 14, 16)]
    assert all(by[(200, n)] > by[(80, n)] for n in {n for _, n in by})
    cell = {(r["breite"], r["n"]): r for r in GROWTH}
    assert (cell[(80, 7)]["labels_ohne_median"], cell[(200, 20)]["labels_ohne_median"], cell[(200, 20)]["labels_voll_median"]) == (94, 51322, 14690)
    for piece in ("im Median von 94 Labels (7 Kunden, Breite 80) auf 51 322 (20 Kunden, Breite 200; Wachstumstabelle unten",
                  "wird der Faktor im Median mit der Kundenzahl größer oder bleibt gleich (Breite 80: gleich bei 8 und 9 sowie bei 14 und 16 Kunden), und bei jeder Kundenzahl liegt er bei Breite 200 höher als bei Breite 80"):
        assert piece in README, piece
    constants = (ROOT / "dml_constants.py").read_text(encoding="utf-8")
    assert "245 096" not in constants and "46 956" not in constants and "im Median bei 51 322" in constants and "bei 14 690" in constants


def test_last_is_the_sum_over_the_remembered_customers_when_elementary_but_not_at_k3(cases180):
    """Elementar (k = n) ist die Last eines Labels die Summe der Lasten seiner besuchten Kunden; bei V1 ⊆ V2 gilt dann R1 ≤ R2, die Last-Bedingung neben dem Gedächtnis ändert nichts.
    Bei k = 3 vergisst das Gedächtnis Kunden: dort gibt es Labels, deren Last größer ist als die Summe der Lasten der gemerkten Kunden."""
    def remembered_load(inst, mem):
        return sum(inst.demand[i] for i in range(1, inst.n + 1) if (mem >> i) & 1)

    for inst, pi, _ in cases180:
        assert all(lab.load == remembered_load(inst, lab.mem) for lab in A.price(inst, pi, inst.n, None).labels[1:])
    forgetting = sum(any(lab.load > remembered_load(inst, lab.mem) for lab in A.price(inst, pi, 3, None).labels[1:]) for inst, pi, _ in cases180)
    assert forgetting > 0
    # gleiche Entscheidungen, also gleiche Ergebnisse: Kosten + Gedächtnis = Kosten + Last + Gedächtnis und Kosten + Zeit + Gedächtnis = volle Regel
    for inst, pi, _ in cases180:
        for a, b in (("kosten_gedaechtnis", "kosten_last_gedaechtnis"), ("kosten_zeit_gedaechtnis", "voll")):
            ra, rb = A.price(inst, pi, inst.n, A.RULES[a]), A.price(inst, pi, inst.n, A.RULES[b])
            assert (ra.generated, ra.dominated, ra.value, ra.route) == (rb.generated, rb.dominated, rb.value, rb.route)
    assert C.LAST_FROM_MEMORY_TEXT in README


def test_readme_wording_after_the_review():
    constants = (ROOT / "dml_constants.py").read_text(encoding="utf-8")
    assert "Konzepte" not in README and "Linie" not in README
    assert "wächst die Zahl der Labels mit der Zahl der Kunden und der Fensterbreite stark" not in README
    assert "bei den größten" not in README and "bei den größten" not in constants
    assert "bei 20 Kunden und Breite 200 langsamer als ohne (Summe über die 10 Instanzen: 26,4 s mit gegen 4,2 s ohne Dominanz, nicht je Instanz;" in README
    assert "obwohl die volle Dominanz dort weniger Labels erzeugt (Faktor 3,49 im Median, siehe Wachstumstabelle)" in README
    assert "war die Rechnung mit Dominanz langsamer als ohne, obwohl sie weniger Labels erzeugt" in constants and "weniger Labels erzeugt; für andere Größen" in README
    assert "(20 Kunden, Fensterbreite 200, auf einem ausgelasteten Rechner, nicht im Test, vom Rechner abhängig) war die Rechnung mit Dominanz langsamer als ohne" in README
    assert "Ausnahme ist die 30-Kunden-Reihe in Experiment 4 (je 6 Instanzen), die wie Experiment 5 die ganze Spaltenerzeugung rechnet" in README
    assert "nur Experiment 5 rechnet" not in README and "nur Teil C der Messreihen" not in README
    assert "sofern Warten erlaubt und kostenlos ist und keine weiteren Grenzen als Zeit und Last gelten" in README
    assert "früher ankommen ist immer besser" not in README


# --- Zusatzpunkte: Zeitmessung, Handbeispiel-Tabelle, zwei gleich gute Wege, Gleichstände im Gedächtnis ---------------------------------------------

def test_the_measured_seconds_come_from_the_log_as_sums_over_ten_instances():
    """Die README nennt 26,4 s und 4,2 s als Summe über die 10 Instanzen; der Faktor im Median steht in der Wachstumszelle (20 Kunden, Breite 200)."""
    cell = {(r["breite"], r["n"]): r for r in GROWTH}[(200, 20)]
    assert cell["instanzen"] == 10 and cell["faktor_median"] == 3.49
    log = ROOT.parent / "label-setting-planung" / "vormessung" / "run_p02.log"
    if log.exists():
        text = log.read_text(encoding="utf-8", errors="replace")
        assert "Sekunden (Summe über die 10 Instanzen)" in text and "4.22   26.37" in text


def test_the_hand_table_names_all_nine_rules_of_the_rule_table():
    """Alle neun Regeln am Handbeispiel (README und App), nachgerechnet mit dem Kern; die zwei Regeln mit Gedächtnis und Zeit bzw. Last: je 45 erzeugt, 15 gestrichen, Wert −22."""
    rows = {r["rule"]: r for r in ev.compare_rules(C.TABLE_RULES)}
    assert [(rows[k]["generated"], rows[k]["dominated"]) for k in C.TABLE_RULES] == [(53, 0), (18, 11), (35, 19), (41, 20), (45, 15), (42, 20), (45, 15), (45, 15), (45, 15)]
    for k in ("kosten_zeit_gedaechtnis", "kosten_last_gedaechtnis"):
        assert rows[k]["value"] == -22 and rows[k]["route"] == (6, 2, 3, 5) and rows[k]["correct"]
    assert (rows["kosten_last_gedaechtnis"]["generated"], rows["kosten_last_gedaechtnis"]["dominated"]) == (rows["kosten_gedaechtnis"]["generated"], rows["kosten_gedaechtnis"]["dominated"])
    assert (rows["kosten_zeit_gedaechtnis"]["generated"], rows["kosten_zeit_gedaechtnis"]["dominated"]) == (rows["voll"]["generated"], rows["voll"]["dominated"])


def test_nur_kosten_has_two_equally_good_routes_in_the_enumeration_and_only_one_is_generated(hand):
    inst, pi = hand
    routes = A.enumerate_routes(inst, pi)
    assert [r for v, r, _ in routes if v == -16] == [(2, 3, 6, 5), (3, 2, 6, 5)]
    a = ev.analyse_hand("kosten")
    assert (a.result.value, a.result.route) == (-16, (2, 3, 6, 5)) and ev.equal_value_routes(a) == ((3, 2, 6, 5),)
    generated = {A.route_of(a.result.labels, i) for i in range(len(a.result.labels))}
    assert (3, 2, 6, 5) not in generated and (3, 2) not in generated
    assert any(e.kind == "verdraengt" and A.route_of(a.result.labels, e.label) == (3,) and A.route_of(a.result.labels, e.partner) == (2, 3) for e in a.result.events)
    assert ev.equal_value_routes(ev.analyse_hand("kosten_zeit")) == () and ev.equal_value_routes(ev.analyse_hand("voll")) == ()


def test_ng_neighbours_break_ties_by_the_smaller_customer_number():
    """README und App: bei gleicher Entfernung zählt die kleinere Kundennummer zuerst, der Halt selbst gehört immer dazu; ng_masks gegen eine eigene Sortierung nach (Entfernung, Nummer)."""
    def expected(inst, j, k):
        order = sorted(range(1, inst.n + 1), key=lambda i: (inst.d[j][i], i))
        return set(order[:k]) | {j}

    def members(mask, n):
        return {i for i in range(1, n + 1) if (mask >> i) & 1}

    hand = S.hand_instance()
    for k in range(1, 7):
        masks = A.ng_masks(hand, k)
        assert all(members(masks[j], 6) == expected(hand, j, k) for j in range(1, 7)), k
    assert hand.d[4][1] == hand.d[4][6] == 5 and members(A.ng_masks(hand, 3)[4], 6) == {1, 4, 5}      # Gleichstand: Kunde 1 vor Kunde 6
    boundary_ties = total = 0
    for seed in range(60):
        for width in (30, 80, 200):
            inst = S.make_instance(7, seed, width)
            masks = A.ng_masks(inst, 3)
            for j in range(1, 8):
                order = sorted(range(1, 8), key=lambda i: (inst.d[j][i], i))
                total += 1
                boundary_ties += inst.d[j][order[2]] == inst.d[j][order[3]]
                assert members(masks[j], 7) == expected(inst, j, 3)
    assert (boundary_ties, total) == (0, 1260)
    for piece in ("Bei gleicher Entfernung zählt der Kunde mit der kleineren Nummer zuerst (stabile Sortierung), und der Halt selbst gehört immer dazu.",
                  "nie ein Gleichstand (0 von 1 260 Fällen: 7 Halte mal 180 Fälle)",
                  "(bei k = 3 zum Beispiel am Kunden 4 die Kunden 1 und 6, beide Entfernung 5)",
                  "dort rechnet die Demo aber nur elementar, die Regel greift also nicht"):
        assert piece in README, piece


def test_every_window_of_the_counter_sample_is_exactly_30_wide_and_the_30_customer_share_names_its_mean():
    """Alle 18 000 Fenster der Gegenprobe sind genau 30 breit (README: „Fenster der Breite 30“, nicht „höchstens“); die Zufallsinstanzen der Regel-Tabelle bleiben „höchstens“.
    Der Anteil bei 30 Kunden ist je Zeile das Mittel der Anteile je Lauf über die Läufe ohne Abbruch (Quelle in data/wachstum.json)."""
    widths = [inst.due[i] - inst.ready[i] for inst in (S.make_general_instance(seed)[0] for seed in range(ev.COUNTER_INSTANCES)) for i in range(1, 7)]
    assert len(widths) == 18000 and all(abs(w - 30) < 1e-9 for w in widths)
    for piece in ("6 Kunden, Fenster der Breite 30 (jedes Fenster genau 30 breit, alle 18 000 Fenster nachgerechnet), zufällige, nicht symmetrische",
                  "die Fensterbreite (immer genau 30 statt höchstens 30, 80 oder 200)",
                  "(je Zeile das Mittel der Anteile je Lauf, gemittelt über die Läufe ohne Abbruch; Quelle: `data/wachstum.json`)",
                  "Fensterbreite höchstens 30, 80 oder 200, auf die erreichbare Zeitspanne beschnitten"):
        assert piece in README, piece
    assert "Fenster der Breite höchstens 30" not in README
    assert all("Mittel der Anteile je Lauf über die Läufe ohne Abbruch" in r["quelle"] for r in ev.load_growth()["v1"])
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "Fenster der Breite 30 (jedes Fenster genau 30 breit)" in app and "höchstens 30" not in app.replace("immer genau 30 statt höchstens 30", "")
    assert "je Zeile das Mittel der Anteile je Lauf, gemittelt über die Läufe ohne Abbruch" in app
