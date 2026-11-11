"""Schnellstart-Szenarien: Vollständigkeit, gültige Werte, Standard-Szenario = Standardeinstellungen, und die erwartete Verdikt-Zeile je Szenario (DEMO-PLAYBOOK §11a Punkt 7)."""

import pytest

import dml_constants as C
import dml_evaluation as ev
import dml_presets as P

DEFAULT = "Volle Dominanz (Voreinstellung)"
# Erwartung je Szenario: Art des Verdikts im Handbeispiel (success: Regel findet den besten Weg, error: verfehlt ihn), Art und Textstück des Verdikts im Größenversuch
EXPECTED = {
    "Volle Dominanz (Voreinstellung)": ("success", "info", "das 1,48-Fache"),
    "Nur nach Kosten streichen": ("error", "info", "das 1,48-Fache"),
    "Kosten und Zeit": ("error", "info", "das 1,48-Fache"),
    "Kosten und Gedächtnis": ("success", "info", "das 1,48-Fache"),
    "20 Kunden, breite Fenster, nichts streichen": ("success", "info", "das 3,47-Fache"),
    "7 Kunden, wenig Ersparnis": ("success", "info", "kaum etwas"),
}


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP) == set(EXPECTED)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_widget_bounds():
    for name, preset in C.PRESETS.items():
        assert preset["rule"] in C.LIVE_RULES and preset["run"] in C.RUN_RULES and preset["width"] in C.WIDTH_OPTIONS, name
        assert C.N_MIN <= preset["n"] <= C.N_MAX and 0 <= preset["seed"] <= C.SEED_MAX, name


def test_default_preset_equals_the_default_settings():
    preset = C.PRESETS[DEFAULT]
    assert next(iter(C.PRESETS)) == DEFAULT
    for state_key, spec in P.SETTING_SPECS.items():
        key = next(k for k, v in P.PRESET_KEYS.items() if v == state_key)
        assert preset[key] == spec.default, state_key


def test_setting_specs_cover_every_preset_key_and_choices_are_the_constants():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    assert P.SETTING_SPECS["rule_select"].choices == C.LIVE_RULES and P.SETTING_SPECS["run_radio"].choices == C.RUN_RULES
    assert P.SETTING_SPECS["width_radio"].choices == C.WIDTH_OPTIONS


def test_every_rule_label_exists_for_every_rule():
    import dml_algorithm as A
    assert set(C.RULE_LABELS) == set(A.RULES) and set(C.TABLE_RULES) == set(A.RULES) and len(C.TABLE_RULES) == 9


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_expected_verdict_lines_of_every_preset(name):
    hand_kind, size_kind, size_piece = EXPECTED[name]
    p = C.PRESETS[name]
    a = ev.analyse_hand(p["rule"])
    kind, _ = ev.verdict_hand(C.RULE_LABELS[p["rule"]], a.result.value, a.result.route, a.best_value, a.best_route, len(a.routes), a.result.generated, a.result.dominated)
    assert kind == hand_kind
    size = ev.size_experiment(p["n"], p["width"], p["seed"])
    kind, text = ev.verdict_size(size.n, size.width, size.runs["keine"].generated, size.runs["voll"].generated, size.runs["voll"].dominated, size.aborted)
    assert kind == size_kind and size_piece in text, text
    assert size.same_value is True


def test_the_help_text_of_the_small_preset_claims_a_factor_below_the_threshold():
    size = ev.size_experiment(7, 80, 4)
    assert size.factor < C.EQUAL_FACTOR and "gleichauf" in C.PRESET_HELP["7 Kunden, wenig Ersparnis"]
