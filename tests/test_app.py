"""End-to-end-Tests über Streamlits AppTest: lädt app.py mit den Standardeinstellungen, klickt jeden Knopf, fährt jeden Regler an seine Grenzen, wählt jede Option,
prüft den Permalink und je Schnellstart-Szenario die erwartete Verdikt-Zeile. Expander werden nie per Index angesprochen (DEMO-PLAYBOOK §2 Punkt 7)."""

import os
import re

import pytest
from streamlit.testing.v1 import AppTest

import dml_constants as C
import dml_evaluation as ev
import dml_presets as P

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
AUTOPLAY_MARKER = "▶"  # Auto-Play-Buttons (Animation mit sleep) im Smoke-Test auslassen


def _fresh_app(query=None) -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    if query:
        at.query_params.update(query)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at, kind):
    return [e.value for e in getattr(at, kind)]


def test_app_loads_without_exception():
    at = _fresh_app()
    assert at.title[0].value.endswith("Dominanz: wann darf ein Label gehen?")


def test_every_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        if AUTOPLAY_MARKER in label:
            continue
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_every_slider_at_its_min_and_max_does_not_raise():
    labels = [s.label for s in _fresh_app().slider]
    assert labels, "keine Slider gefunden"
    for index, label in enumerate(labels):
        for edge in ("min", "max"):
            at = _fresh_app()
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            if isinstance(slider.value, int):
                value = int(value)
            slider.set_value(value).run(timeout=TIMEOUT)
            assert not at.exception, (label, edge, [str(e) for e in at.exception])


@pytest.mark.parametrize("key,options", [("rule_select", C.LIVE_RULES), ("run_radio", C.RUN_RULES), ("width_radio", C.WIDTH_OPTIONS)])
def test_every_option_of_every_choice_widget_does_not_raise(key, options):
    for option in options:
        at = _fresh_app()
        for art in ("selectbox", "radio"):
            try:
                getattr(at.sidebar, art)(key=key).set_value(option).run(timeout=TIMEOUT)
                break
            except KeyError:
                continue
        assert not at.exception, (key, option, [str(e) for e in at.exception])


def test_seed_input_at_min_and_max_and_all_minima_and_all_maxima_together():
    """Eckfall-Matrix (DEMO-PLAYBOOK §1d) und Worst-Case am Regler-Maximum (§1c): Kundenzahl und Fensterbreite am Maximum, Zufalls-Seed am Minimum und am Maximum, alle Läufe fertig."""
    lows = {"n_slider": C.N_MIN, "width_radio": C.WIDTH_OPTIONS[0], "seed_input": 0}
    highs = {"n_slider": C.N_MAX, "width_radio": C.WIDTH_OPTIONS[-1], "seed_input": C.SEED_MAX}
    for combo in (lows, highs, {**highs, "seed_input": 0}, {**lows, "seed_input": C.SEED_MAX}):
        at = _fresh_app()
        at.sidebar.slider(key="n_slider").set_value(combo["n_slider"])
        at.sidebar.radio(key="width_radio").set_value(combo["width_radio"])
        at.sidebar.number_input(key="seed_input").set_value(combo["seed_input"])
        at.run(timeout=TIMEOUT)
        assert not at.exception, (combo, [str(e) for e in at.exception])
        assert at.sidebar.slider(key="n_slider").value == combo["n_slider"]


def test_permalink_sets_the_widgets_and_clamps_invalid_values():
    at = _fresh_app({"regel": "kosten_zeit", "n": "14", "breite": "200", "seed": "7", "lauf": "keine"})
    assert at.sidebar.selectbox(key="rule_select").value == "kosten_zeit"
    assert at.sidebar.slider(key="n_slider").value == 14 and at.sidebar.radio(key="width_radio").value == 200
    assert at.sidebar.number_input(key="seed_input").value == 7 and at.sidebar.radio(key="run_radio").value == "keine"
    bad = _fresh_app({"regel": "unsinn", "n": "999", "breite": "123", "seed": "-5", "lauf": "x"})
    assert bad.sidebar.selectbox(key="rule_select").value == "voll" and bad.sidebar.slider(key="n_slider").value == C.N_MAX
    assert bad.sidebar.radio(key="width_radio").value == C.DEFAULT_WIDTH and bad.sidebar.number_input(key="seed_input").value == 0
    assert bad.sidebar.radio(key="run_radio").value == "voll"
    garbage = _fresh_app({"n": "abc", "seed": "1.5"})
    assert garbage.sidebar.slider(key="n_slider").value == C.DEFAULT_N and garbage.sidebar.number_input(key="seed_input").value == C.DEFAULT_SEED


def test_query_params_follow_the_settings():
    at = _fresh_app()
    at.sidebar.selectbox(key="rule_select").set_value("kosten").run(timeout=TIMEOUT)
    assert at.query_params["regel"] == ["kosten"] or at.query_params["regel"] == "kosten"


def test_sections_are_present_by_title_not_by_index():
    at = _fresh_app()
    expanders = {e.label: e for e in at.expander}
    assert "So funktioniert die Dominanz" in expanders and expanders["So funktioniert die Dominanz"].proto.expanded
    assert "💬 In einfachen Worten" in expanders
    assert "📐 Mathematische Formulierung" in expanders and "⚠️ Annahmen, Grenzen und bekannte Probleme" in expanders
    subheaders = [s.value for s in at.subheader]
    for number in range(1, 6):
        assert any(s.startswith(f"🔬 Experiment {number}:") for s in subheaders), number
    assert any(s.startswith("🚧 Wo die Annahmen enden") for s in subheaders)
    math_blocks = expanders["📐 Mathematische Formulierung"].markdown
    assert math_blocks[0].value.startswith("**Lesehilfe.**") and "| Symbol | Bedeutung |" in math_blocks[0].value
    assert sum("**Lesehilfe.**" in b.value for b in math_blocks) == 1
    math = "\n".join(b.value for b in math_blocks)
    assert "Prüfstand" in math and "Volltexte sind nicht gelesen" in math


def test_assumptions_expander_text_equals_the_constant_and_the_readme():
    at = _fresh_app()
    box = next(e for e in at.expander if e.label == "⚠️ Annahmen, Grenzen und bekannte Probleme")
    assert box.markdown[0].value.strip() == C.ASSUMPTIONS_MARKDOWN.strip()
    readme = open(os.path.join(os.path.dirname(APP_PATH), "README.md"), encoding="utf-8").read()
    assert C.ASSUMPTIONS_MARKDOWN.strip() in readme


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_shows_its_expected_verdict_lines(name):
    at = _fresh_app()
    at.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    rule = C.PRESETS[name]["rule"]
    hand_ok = rule in ("keine", "voll", "kosten_gedaechtnis", "kosten_last")
    label = C.RULE_LABELS[rule]
    successes, errors = _texts(at, "success"), _texts(at, "error")
    if hand_ok:
        assert any(t.startswith(f"Die Regel „{label}“ findet den besten Weg 6-2-3-5") for t in successes), name
        assert not any("verfehlt den besten Weg" in t for t in errors)
    else:
        assert any(t.startswith(f"Die Regel „{label}“ verfehlt den besten Weg") for t in errors), name
        assert any("geht der beste Weg 6-2-3-5" in t for t in errors)
    info = " ".join(_texts(at, "info"))
    assert (f"n = {C.PRESETS[name]['n']} Kunden und Fensterbreite {C.PRESETS[name]['width']}") in info


def test_checkbox_shows_the_labels_that_stay():
    at = _fresh_app()
    assert not any("Ereignis" in d.value.columns for d in at.dataframe if hasattr(d.value, "columns") and "bleibt" in set(d.value.get("Ereignis", [])))
    at.checkbox(key="show_all").set_value(True).run(timeout=TIMEOUT)
    assert not at.exception
    frames = [d.value for d in at.dataframe if hasattr(d.value, "columns") and "Ereignis" in d.value.columns]
    assert frames and "bleibt" in set(frames[0]["Ereignis"]) and "neues Label verworfen" in set(frames[0]["Ereignis"]) and "älteres entfällt" in set(frames[0]["Ereignis"])


def test_no_dominance_rule_shows_the_hint_instead_of_an_empty_table():
    at = _fresh_app({"regel": "keine"})
    assert any("Mit dieser Regel wird nichts gestrichen" in t for t in _texts(at, "info"))


def test_counter_button_runs_the_counter_sample():
    at = _fresh_app()
    button = next(b for b in at.button if b.key == "counter_button")
    button.click().run(timeout=TIMEOUT)
    assert not at.exception
    assert any("Zufalls-Seed 209" in t and "Dreiecksungleichung nicht erzwungen" in t and "ohne Dreiecksungleichung" not in t for t in _texts(at, "warning"))
    captions = _texts(at, "caption")
    assert any(f"nicht symmetrisch (Dreiecksungleichung nicht erzwungen; sie ist in allen {ev.fmt_int(3000)} Instanzen bei mindestens einem Knotentripel verletzt)" in t
               and "zugleich den Instanztyp" in t and "die Kundenzahl (6 statt 7)" in t and "die Fensterbreite" in t for t in captions)


def test_hand_table_has_nine_rules_and_the_verdict_names_both_routes_with_minus_16():
    at = _fresh_app({"regel": "kosten"})
    frames = [d.value for d in at.dataframe if hasattr(d.value, "columns") and "Gegen die Aufzählung" in d.value.columns]
    assert len(frames) == 1 and list(frames[0]["Regel"]) == [C.RULE_LABELS[r] for r in C.TABLE_RULES]
    row = frames[0].set_index("Regel").loc[C.RULE_LABELS["kosten_last_gedaechtnis"]]
    assert (row["Erzeugte Labels"], row["Gestrichen"], row["Gegen die Aufzählung"]) == (45, 15, "richtig")
    assert any("Alle neun Regeln der Regel-Tabelle" in t and "weil elementar die Last aus dem Gedächtnis folgt" in t for t in _texts(at, "caption"))
    assert any("Mit demselben Wert −16 kennt die Aufzählung auch die Route 3-2-6-5; die Regel gibt 2-3-6-5 aus." in t for t in _texts(at, "error"))
    assert any("bei gleicher Entfernung zählt der Kunde mit der kleineren Nummer zuerst" in t for t in _texts(at, "caption"))


def test_texts_with_their_conditions_and_without_unmeasured_comparatives():
    """Korrekturliste der Prüfer: Voraussetzungen im Expander und in der Mathematik, Last-aus-Gedächtnis-Erklärung, Bezug der Prozentwerte, kein Steigerungswort ohne Maßstab."""
    at = _fresh_app()
    expanders = {e.label: e for e in at.expander}
    how = expanders["So funktioniert die Dominanz"].markdown[0].value
    assert "und sie wird nicht teurer, sofern Warten erlaubt und kostenlos ist" in how and "keine weiteren Grenzen gelten" in how
    math = "\n".join(b.value for b in expanders["📐 Mathematische Formulierung"].markdown)
    assert "sofern Warten erlaubt und kostenlos ist und keine weiteren Grenzen als Zeit und Last gelten" in math
    assert "Elementar folgt die Last aus dem Gedächtnis" in math and "V_1 \\subseteq V_2 \\Rightarrow R_1 \\le R_2" in math and "Ohne Gedächtnis bricht je ein Schritt" in math
    assert "V' = (V \\cap N_k(j)) \\cup \\{j\\}" in math
    captions = _texts(at, "caption")
    assert C.LAST_FROM_MEMORY_TEXT in captions
    growth = next(t for t in captions if t.startswith("Hinweise: Bei 7 Kunden"))
    assert "deutlich mehr" not in growth and "wird der Faktor im Median mit der Kundenzahl größer oder bleibt gleich" in growth
    assert any("Dualpreise aus der Spaltenerzeugung, nicht zufällig" in m.value for m in at.markdown)
    warnings = _texts(at, "warning")
    assert any("Abstand zur Schranke der vollen Regel, bezogen auf diese: Mittel 1,216 %, Maximum 8,476 %" in t and "auch über die 5 ohne Unterschied" in t for t in warnings)
    ends = next(m.value for m in at.markdown if "| Annahme |" in m.value)
    assert "außer der 30-Kunden-Reihe" in ends and "ändert zugleich Instanztyp, Kundenzahl und Fensterbreite" in ends


def test_settings_in_the_url_match_the_setting_specs():
    assert {spec.url_param for spec in P.SETTING_SPECS.values()} == {"regel", "n", "breite", "seed", "lauf"}
    assert re.fullmatch(r"[a-z]+", "".join(spec.url_param for spec in P.SETTING_SPECS.values()))
