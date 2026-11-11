"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Schwelle der Art und jede Zahl im Text steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Zahlen, nicht Seeds."""

import dml_constants as C
import dml_evaluation as ev


def test_verdict_hand_success_and_error_name_their_numbers():
    kind, text = ev.verdict_hand("nur Kosten", -22, (6, 2, 3, 5), -22, (6, 2, 3, 5), 52, 45, 15)
    assert kind == "success"
    assert "„nur Kosten“ findet den besten Weg 6-2-3-5 mit reduzierten Kosten −22" in text and "aller 52 zulässigen Routen" in text and "45 Labels, 15 davon" in text
    kind, text = ev.verdict_hand("nur Kosten", -16, (2, 3, 6, 5), -22, (6, 2, 3, 5), 52, 18, 11)
    assert kind == "error" and "verfehlt den besten Weg" in text
    assert "findet 2-3-6-5 mit −16" in text and "findet 6-2-3-5 mit −22" in text and "erzeugt 18 Labels und streicht 11" in text


def test_verdict_hand_names_the_equally_good_routes_of_the_enumeration():
    kind, text = ev.verdict_hand("nur Kosten", -16, (2, 3, 6, 5), -22, (6, 2, 3, 5), 52, 18, 11, ((3, 2, 6, 5),))
    assert kind == "error" and "Mit demselben Wert −16 kennt die Aufzählung auch die Route 3-2-6-5; die Regel gibt 2-3-6-5 aus." in text
    _, two = ev.verdict_hand("x", -16, (2, 3, 6, 5), -22, (6, 2, 3, 5), 52, 18, 11, ((3, 2, 6, 5), (4, 2, 6, 5)))
    assert "auch die Routen 3-2-6-5 und 4-2-6-5" in two
    assert "Mit demselben Wert" not in ev.verdict_hand("nur Kosten", -16, (2, 3, 6, 5), -22, (6, 2, 3, 5), 52, 18, 11)[1]


def test_verdict_hand_right_value_but_wrong_route_is_an_error():
    assert ev.verdict_hand("x", -22, (2, 6, 3, 5), -22, (6, 2, 3, 5), 52, 5, 1)[0] == "error"


def test_verdict_decisions_three_branches():
    assert ev.verdict_decisions("keine Dominanz", 0, 0)[0] == "info"
    kind, text = ev.verdict_decisions("volle Dominanz", 15, 0)
    assert kind == "success" and "Alle 15 Streichungen" in text
    kind, text = ev.verdict_decisions("nur Kosten", 11, 7)
    assert kind == "warning" and "7 von 11 Streichungen" in text and "„nur Kosten“" in text


def test_verdict_loss_names_prefix_labels_and_number_of_violated_conditions():
    loss = ev.Loss((6,), 6, 13, ("Zeit: 12 > 10", "Last: 5 > 2", "Gedächtnis: {2,6} ⊄ {6}"))
    kind, text = ev.verdict_loss("nur Kosten", (6, 2, 3, 5), loss)
    assert kind == "error" and "6-2-3-5 schon an der Vorstufe 6 verloren" in text and "L6 wird von L13" in text and "3 der vier Bedingungen" in text
    kind, text = ev.verdict_loss("volle Dominanz", (6, 2, 3, 5), None)
    assert kind == "success" and "keine Vorstufe" in text


def test_verdict_losses_counts_rules():
    assert ev.verdict_losses(0, 6)[0] == "success"
    kind, text = ev.verdict_losses(2, 6)
    assert kind == "info" and "bei 2 der 6 wählbaren Regeln" in text and "in beiden Fällen erfüllt ein dominierendes Label nicht alle vier Bedingungen" in text


def test_verdict_losses_does_not_say_both_when_the_number_differs():
    """Der Satz über die verletzten Bedingungen hängt nicht an genau zwei verlorenen Regeln."""
    _, one = ev.verdict_losses(1, 6)
    _, three = ev.verdict_losses(3, 6)
    assert "bei 1 der 6" in one and "in diesem Fall" in one and "beiden" not in one
    assert "bei 3 der 6" in three and "in allen 3 Fällen" in three and "beiden" not in three


def test_verdict_rule_table_uses_the_counts_of_the_rows():
    def row(rule, miss, key="verfehlt"):
        return {"regel": rule, key: miss, "labels_median": 1, "labels_mittel": 1.0}

    rows_el = [row("kosten", 67), row("voll", 0), row("kosten_gedaechtnis", 0)]
    rows_ng = [row("kosten_gedaechtnis", 31, "weicht_ab"), row("voll", 0, "weicht_ab")]
    kind, text = ev.verdict_rule_table(rows_el, rows_ng, 180)
    assert kind == "info"
    assert "Bei 180 Fällen" in text and "in 67 Fällen (37,2 %)" in text and "die volle Regel in 0" in text
    assert "„Kosten + Gedächtnis“ ihn in 0 Fällen" in text and "k = 3 weicht diese Regel in 31 Fällen" in text and "(0 Fälle)" in text


def test_verdict_counter_both_branches():
    kind, text = ev.verdict_counter({"kosten_gedaechtnis": [], "voll": []}, 3000)
    assert kind == "info" and "3 000 Instanzen" in text and "nie" in text and "Dreiecksungleichung nicht erzwungen" in text and "ohne Dreiecksungleichung" not in text
    kind, text = ev.verdict_counter({"kosten_gedaechtnis": [209], "voll": []}, 3000)
    assert kind == "warning" and "in 1 Fall (Zufalls-Seed 209)" in text and "die volle Regel in 0" in text and "…" not in text
    assert "Dreiecksungleichung nicht erzwungen" in text and "ändert zugleich Fahrzeiten, Kundenzahl (6 statt 7) und Fensterbreite" in text and "ohne Dreiecksungleichung" not in text
    kind, text = ev.verdict_counter({"kosten_gedaechtnis": [1, 2, 3, 4], "voll": [5]}, 10)
    assert "in 4 Fällen (Zufalls-Seed 1, 2, 3, …" in text and "die volle Regel in 1" in text


def test_verdict_size_thresholds_and_numbers():
    kind, text = ev.verdict_size(7, 80, 108, 102, 40, False)               # Faktor 1,059: gleichauf
    assert kind == "info" and "kaum etwas" in text and "108 Labels ohne, 102 mit voller Dominanz (Faktor 1,06; unter 1,2 gilt hier als gleichauf)" in text
    kind, text = ev.verdict_size(7, 80, 120, 100, 40, False)               # genau 1,2: nicht mehr gleichauf (Schwelle ist exklusiv)
    assert "kaum etwas" not in text and "das 1,20-Fache" in text
    kind, text = ev.verdict_size(20, 200, 42863, 12361, 3000, False)
    assert "n = 20 Kunden und Fensterbreite 200" in text and "42 863 Labels, mit voller Dominanz 12 361: das 3,47-Fache" in text
    assert "24,3 % der erzeugten Labels" in text                            # 3000 / 12361
    kind, text = ev.verdict_size(20, 200, 300000, 10, 0, True)
    assert kind == "warning" and "300 000" in text and "Abbruch" in text


def test_equal_factor_threshold_is_the_documented_one():
    assert C.EQUAL_FACTOR == 1.2


def test_verdict_colgen_branches_and_summary():
    rows = [{"unterschied_prozent": 0.0}, {"unterschied_prozent": 1.0}, {"unterschied_prozent": 3.0}, {"unterschied_prozent": -0.0}]
    s = ev.colgen_summary(rows)
    assert s == {"instanzen": 4, "hoeher": 2, "mittel": 1.0, "maximum": 3.0}
    kind, text = ev.verdict_colgen(s)
    assert kind == "warning" and "in 2 von 4 Instanzen" in text and "Mittel 1,000 %" in text and "Maximum 3,000 %" in text and "keine gültige Untergrenze" in text
    assert "Abstand zur Schranke der vollen Regel, bezogen auf diese" in text and "das Mittel läuft über alle 4 Instanzen, auch über die 2 ohne Unterschied" in text
    kind, text = ev.verdict_colgen({"instanzen": 4, "hoeher": 0, "mittel": 0.0, "maximum": 0.0})
    assert kind == "success" and "In allen 4 Instanzen" in text
