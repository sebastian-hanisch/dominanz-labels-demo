"""Dominanz: wann darf ein Label gehen? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Label-Verfahren für den Weg mit den kleinsten reduzierten Kosten (Preisproblem der Spaltenerzeugung): Wann darf ein Teilweg (Label) gestrichen werden,
ohne den besten Weg zu verlieren? Handbeispiel Schritt für Schritt, Regel-Tabelle aus 180 Fällen, Größenversuch live, Folge für die Spaltenerzeugung.

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import dml_algorithm as A
import dml_constants as C
import dml_evaluation as ev
from dml_layout import dunkles_design, kopf_css
from dml_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from dml_scenario import HAND_DUALS
from dml_visualization import build_colgen_chart, build_factor_chart, build_hand_map, build_rule_chart, build_size_chart

st.set_page_config(page_title="Dominanz – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _hand(rule):
    return ev.analyse_hand(rule)


@st.cache_data(show_spinner=False)
def _hand_rules():
    return ev.compare_rules()


@st.cache_data(show_spinner=False)
def _hand_rules_all():
    return ev.compare_rules(C.TABLE_RULES)


@st.cache_data(show_spinner=False)
def _size(n, width, seed):
    return ev.size_experiment(n, width, seed)


@st.cache_data(show_spinner=False)
def _counter():
    return ev.counter_sweep()


@st.cache_data(show_spinner=False)
def _tables():
    return ev.load_rule_table(), ev.load_growth(), ev.load_colgen()


def _rule_label(rule):
    return C.RULE_LABELS[rule]


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in dml_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧭 Dominanz: wann darf ein Label gehen?")
st.markdown(
    """
Beim Suchen des **besten Weges mit mehreren Grenzen** (Zeitfenster, Last, jeder Kunde höchstens einmal) hält das **Label-Verfahren** jeden Teilweg als **Label** fest:
Kosten, verbrauchte Zeit, verbrauchte Last und besuchte Kunden. Damit es nicht alle Teilwege verfolgen muss, **streicht** es ein Label, das ein anderes Label
am selben Kunden **dominiert**. Diese Demo fragt: **Wie großzügig darf man streichen?** Wer nie streicht, erzeugt viele Labels; wer zu großzügig streicht,
verliert den besten Weg. Beides wird gezählt: am Handbeispiel Schritt für Schritt, an 180 Fällen, an einem Größenversuch und an der ganzen Spaltenerzeugung.

Weiter unten: die Expander **💬 In einfachen Worten** und **So funktioniert die Dominanz** (beide zuerst), fünf Experimente (**🔬**), **🚧 Wo die Annahmen enden**, **📐 Mathematische Formulierung** und
**⚠️ Annahmen, Grenzen und bekannte Probleme**. Die Anwendung dieses Verfahrens in einem Fall (Besatzungsplanung im Zugverkehr) zeigt
[crew-pairing-demo](https://github.com/sebastian-hanisch/crew-pairing-demo). Nicht zu verwechseln mit [hub-labeling-demo](https://github.com/sebastian-hanisch/hub-labeling-demo): Dort sind Labels vorberechnete
Listen für schnelle Abfragen kürzester Wege, hier sind es Teilwege im Preisproblem der Spaltenerzeugung.
"""
)

# erklaerseite:einfach:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/dominanz-teilwege-erklaert.json, nicht von Hand ändern)
with st.expander("💬 In einfachen Worten"):
    st.markdown(
        """
Beim Suchen des besten Weges mit Zeitfenstern, Ladegrenze und höchstens einem Besuch je Kunde hält das Label-Verfahren jeden Teilweg als **Label** fest: Kosten, Zeit, verbrauchte Last und besuchte Kunden. Ein Label darf gestrichen werden, wenn ein anderes Label am selben Kunden in allen vier Angaben mindestens so gut ist (**Dominanz**). Dann kann jede Fortsetzung des gestrichenen Labels auch vom anderen gefahren werden und wird nicht teurer. Wer nur die Kosten vergleicht, streicht zu großzügig und verliert in manchen Fällen den besten Weg. Die Demo zeigt das am Handbeispiel Schritt für Schritt, an vielen Zufallsfällen, an einem Größenversuch und an der ganzen Spaltenerzeugung. Gezählt werden erzeugte Labels, keine Sekunden.

[Ausführlich und verständlich erklärt, mit Fachteil](https://sebastianhanisch.net/dominanz-teilwege-erklaert.html)
        """
    )
# erklaerseite:einfach:end

with st.expander("So funktioniert die Dominanz", expanded=True):
    st.markdown(
        """
1. **Ein Label ist ein Teilweg in vier Zahlen:** die **reduzierten Kosten** bisher (Weglänge minus die **Dualpreise** der besuchten Kunden; der Dualpreis ist der Betrag, den die
   übergeordnete Planung einem Kunden zurechnet), die **Zeit** (Beginn der Bedienung; wer zu früh kommt, wartet kostenlos), die verbrauchte **Last** und die **besuchten Kunden**
   (das „Gedächtnis“: ein Kunde darf nicht noch einmal besucht werden).
2. **Das Verfahren verlängert Labels in Zeitreihenfolge** um je einen Kunden. Am selben Kunden können sehr viele Labels enden (verschiedene Wege dorthin).
3. **Ein Label O dominiert ein Label N am selben Kunden,** wenn O in allem mindestens so gut ist, was die Zukunft des Weges beeinflusst: Kosten **nicht höher**, Zeit **nicht später**,
   Last **nicht größer**, und die besuchten Kunden von O sind eine **Teilmenge** der von N. Dann kann jede Fortsetzung von N auch von O gefahren werden, und sie wird nicht teurer, sofern Warten erlaubt und kostenlos ist (wer früher ankommt, wartet einfach) und keine weiteren Grenzen gelten. N darf gehen.
   Sind beide in allem gleich, bleibt das ältere.
4. **Streicht man mit weniger Bedingungen, wird die Regel großzügiger und kann falsch werden:** Das Handbeispiel zeigt, welches Label dabei verloren geht, und die Messreihen zählen, wie oft das passiert. Eine Ausnahme: Wird das Gedächtnis geprüft und besucht jeder Kunde höchstens einmal, folgt die Last schon aus dem Gedächtnis, und ihr Fehlen ändert nichts (Experiment 3).

Merksatz: **Kosten allein entscheiden nicht.** Ein billigeres Label, das später ankommt, mehr Last hat oder schon einen Kunden verbraucht hat, den der beste Weg noch braucht, ist kein Ersatz.
"""
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Szenario ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Handbeispiel** (Ergebnis und Experimente 1 und 2)")
    rule = st.selectbox("Dominanzregel", C.LIVE_RULES, key="rule_select", format_func=_rule_label,
                        help="Welche Bedingungen das Label-Verfahren prüft, bevor es ein Label streicht. Kosten werden immer verglichen.")
    st.markdown("**Größenversuch** (Experiment 4)")
    n = st.slider("Kunden n", *bounds("n_slider"), key="n_slider", help="Zahl der Kunden der Zufallsinstanz (7 bis 20).")
    width = st.radio("Fensterbreite", C.WIDTH_OPTIONS, key="width_radio", horizontal=True,
                     help="Höchstbreite der Zeitfenster der Kunden in Zeiteinheiten (Horizont 300; auf die erreichbare Zeitspanne beschnitten). Breite Fenster lassen mehr Wege zu.")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    run = st.radio("Regel des Laufs", C.RUN_RULES, key="run_radio", horizontal=True, format_func=lambda r: "keine" if r == "keine" else "volle",
                   help="Welcher der beiden Läufe in Diagramm und Kennzahlen gezeigt wird; gerechnet werden immer beide, für den Faktor.")
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

sync_query_params({"rule_select": rule, "n_slider": int(n), "width_radio": int(width), "seed_input": int(seed), "run_radio": run})

rule_label = _rule_label(rule)
hand = _hand(rule)
hand_none = _hand("keine")
inst = hand.inst
res = hand.result
tables_rule, tables_growth, tables_colgen = _tables()

# --- Ergebnis: das Handbeispiel ------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Das Handbeispiel: sechs Kunden, eine Regel")
st.markdown(
    "Ein Fahrzeug startet im Depot (Gitterpunkt (5, 5)) und besucht Kunden, jeden höchstens einmal. **Entfernung = Fahrzeit = Manhattan-Abstand** (Zeilen plus Spalten auf dem Gitter, "
    f"so bleiben alle Zahlen ganz). Bedienzeit {inst.service}, Rückkehr spätestens zur Zeit {inst.horizon}, Last höchstens {inst.capacity}. Wer vor Beginn seines Fensters ankommt, wartet "
    "kostenlos. **Reduzierte Kosten einer Route** = Summe der Entfernungen minus Summe der Dualpreise der besuchten Kunden; gesucht ist die kleinste (negativste)."
)
table = pd.DataFrame(
    {
        "Kunde": list(range(1, inst.n + 1)),
        "Punkt": [f"({inst.points[i][0]}, {inst.points[i][1]})" for i in range(1, inst.n + 1)],
        "Entfernung zum Depot": [inst.d[0][i] for i in range(1, inst.n + 1)],
        "Last": [inst.demand[i] for i in range(1, inst.n + 1)],
        "Zeitfenster [früh, spät]": [f"[{inst.ready[i]}, {inst.due[i]}]" for i in range(1, inst.n + 1)],
        "Dualpreis": [HAND_DUALS[i] for i in range(1, inst.n + 1)],
    }
)
st.dataframe(table, hide_index=True, width="stretch")

m1, m2, m3, m4 = st.columns(4)
delta_value = res.value - hand.best_value   # mein Wert minus Referenz (Aufzählung); größer ist schlechter
m1.metric(f"Bester Wert der Regel „{rule_label}“", ev.fmt_num(res.value),
          delta=f"{delta_value:+g} gegen die Aufzählung".replace("-", "−") if delta_value else "wie die Aufzählung",
          delta_color="inverse" if delta_value else "off")
m2.metric("Aufzählung aller Routen", ev.fmt_num(hand.best_value), help=f"Bester Wert über alle {len(hand.routes)} zulässigen Routen (Aufzählung ohne Labels).")
delta_labels = res.generated - hand_none.result.generated
m3.metric("Erzeugte Labels", res.generated,
          delta=f"{delta_labels:+d} gegen ohne Dominanz".replace("-", "−") if delta_labels else "wie ohne Dominanz", delta_color="inverse" if delta_labels else "off")
m4.metric("Davon gestrichen", res.dominated, help="Labels, die durch Dominanz entfallen (neue, die gar nicht erst bleiben, und ältere, die verdrängt werden).")
st.caption(f"Die Aufzählung findet {len(hand.routes)} zulässige Routen. Von den {res.generated} erzeugten Labels bleiben {res.alive} am Ende.")
st.plotly_chart(build_hand_map(inst, hand.best_route, res.route, rule_label), width="stretch", key="hand_map")
st.caption("Hell grün: der beste Weg laut Aufzählung aller zulässigen Routen. Rot gestrichelt: der Weg, den die gewählte Regel findet, falls er abweicht. "
           "Die Linien folgen dem Gitter (erst waagerecht, dann senkrecht).")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Findet die gewählte Regel den besten Weg?")
kind, text = ev.verdict_hand(rule_label, res.value, res.route, hand.best_value, hand.best_route, len(hand.routes), res.generated, res.dominated,
                              ev.equal_value_routes(hand))
getattr(st, kind)(text)
if not hand.unique:
    st.warning("Der beste Weg ist in diesem Beispiel nicht eindeutig; der Vergleich bezieht sich auf die erste Route der Sortierung.")
rules_table = pd.DataFrame(
    [
        {"Regel": _rule_label(r["rule"]), "Bester Wert": r["value"], "Route": ev.fmt_route(r["route"]), "Erzeugte Labels": r["generated"],
         "Gestrichen": r["dominated"], "Am Ende lebend": r["alive"], "Gegen die Aufzählung": "richtig" if r["correct"] else "falsch"}
        for r in _hand_rules_all()
    ]
)
st.dataframe(rules_table, hide_index=True, width="stretch")
st.caption("Alle neun Regeln der Regel-Tabelle am Handbeispiel (elementar, ohne Zufall); in der Seitenleiste wählbar sind sechs davon. „Kosten + Last + Gedächtnis“ gleicht „Kosten + Gedächtnis“ und „Kosten + Zeit + Gedächtnis“ der vollen Regel, weil elementar die Last aus dem Gedächtnis folgt (Experiment 3). „Erzeugte Labels“ zählt jedes erzeugte Label, auch ein sofort gestrichenes, und das Start-Label im Depot.")

st.markdown("---")

# --- Experiment 1 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Dominanz Schritt für Schritt")
checked = ev.checked_conditions(rule)
st.caption(
    f"Handbeispiel mit der Regel „{rule_label}“ (Seitenleiste). Jede Zeile ist eine Entscheidung: ein neues Label wird verworfen, oder ein älteres entfällt. Die vier Spalten vergleichen "
    "das **dominierende** Label mit dem gestrichenen (links der Wert des dominierenden, rechts der des gestrichenen Labels): ✓ erfüllt (grün), ✗ verletzt (rot). Rot in einer Spalte, die die Regel **nicht prüft**, heißt: Die Regel hat hier großzügiger gestrichen, "
    "als die volle Regel erlaubt."
)
show_all = st.checkbox("Auch die Labels zeigen, die bleiben", key="show_all")
rows = ev.event_rows(hand, show_all=show_all)
if rows:
    df = pd.DataFrame(rows).drop(columns=["ok"])
    df = df.rename(columns={name: f"{name} ({'geprüft' if name in checked else 'nicht geprüft'})" for name in A.CONDITION_NAMES})
    cond_cols = [f"{name} ({'geprüft' if name in checked else 'nicht geprüft'})" for name in A.CONDITION_NAMES]
    styled = df.style.map(lambda v: C.CELL_OK if str(v).endswith("✓") else (C.CELL_BAD if str(v).endswith("✗") else ""), subset=cond_cols)
    widths = {"Ereignis": 115, "Gestrichenes Label": 125, "Dominierendes Label": 135, "Zu großzügig": 80, **{c: 125 for c in cond_cols}}
    st.dataframe(styled, hide_index=True, width="stretch", height=min(38 * (len(df) + 1) + 3, 420),
                 column_config={name: st.column_config.TextColumn(name, width=w) for name, w in widths.items()})
else:
    st.info("Mit dieser Regel wird nichts gestrichen, es gibt keine Entscheidung zu zeigen. Mit „Auch die Labels zeigen, die bleiben“ erscheinen alle erzeugten Labels.")
decisions = res.dominated
too_generous = sum(1 for r in ev.event_rows(hand) if r["ok"] is False)
kind, text = ev.verdict_decisions(rule_label, decisions, too_generous)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 2 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 2: Wo geht der beste Weg verloren?")
st.caption("Für jede der wählbaren Regeln, die den besten Weg des Handbeispiels verfehlt: die erste Vorstufe des besten Weges, die sie streicht, und warum das falsch ist.")
wrong = [r for r in _hand_rules() if not r["correct"]]
for r in wrong:
    a = _hand(r["rule"])
    loss = ev.first_loss(a)
    if loss is None:
        continue
    kind, text = ev.verdict_loss(_rule_label(r["rule"]), a.best_route, loss)
    getattr(st, kind)(text)
    dom_label, lost_label = a.result.labels[loss.dominator], a.result.labels[loss.lost]
    nxt = a.best_route[len(loss.prefix)] if len(loss.prefix) < len(a.best_route) else None
    lines = [f"- **Gestrichen:** {ev.label_text(a.inst, a.result, loss.lost)}.",
             f"- **Von wem:** {ev.label_text(a.inst, a.result, loss.dominator)}, nach der Regel „{_rule_label(r['rule'])}“ besser oder gleich.",
             f"- **Was die volle Regel dazu sagt:** {'; '.join(loss.violated)}."]
    if nxt is not None and (dom_label.mem >> nxt) & 1:
        lines.append(f"- **Folge:** Der nächste Halt des besten Weges ist Kunde {nxt}. Beim dominierenden Label steht er schon im Gedächtnis ({ev.fmt_set(dom_label.mem, a.inst.n)}), "
                     "es kann ihn nicht mehr anfahren. Der beste Weg ist ab hier nicht mehr zu finden.")
    st.markdown("\n".join(lines))
kind, text = ev.verdict_losses(len(wrong), len(C.LIVE_RULES))
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 3 --------------------------------------------------------------------------------------------------------------------------

cases = tables_rule["faelle"]
st.subheader(f"🔬 Experiment 3: Welche Bedingung ist nötig? Regel-Tabelle aus {cases} Fällen")
st.caption(
    f"Feste Messreihe: {tables_rule['instanzen']} Zufallsinstanzen mit {tables_rule['kunden']} Kunden, je mit den Fensterbreiten {', '.join(str(b) for b in tables_rule['breiten'])} "
    f"({cases} Fälle), zufällige Dualpreise. Bezug: „elementar“ gegen die Aufzählung aller Routen; „Gedächtnis k = 3“ (ein Label merkt sich besuchte Kunden nur, solange sie zu den 3 nächsten Kunden jedes weiteren Halts gehören, den Kunden selbst eingerechnet; bei gleicher Entfernung zählt der Kunde mit der kleineren Nummer zuerst (in diesen Fällen gibt es an der Grenze keinen Gleichstand); "
    "sonst darf der Kunde wiederkehren, also nicht elementar) gegen das Ergebnis ohne Dominanz bei k = 3. Die Mediane sind auf ganze Zahlen gerundet (bei zwei mittleren Werten weicht die Zahl um 0,5 ab)."
)
rows_el, rows_ng = ev.rule_rows(tables_rule, "elementar"), ev.rule_rows(tables_rule, "ng3")
df3 = pd.DataFrame(
    {
        "Regel": [_rule_label(r["regel"]) for r in rows_el],
        "elementar: Fälle verfehlt": [r["verfehlt"] for r in rows_el],
        "Anteil (%)": [100 * r["verfehlt"] / cases for r in rows_el],
        "Labels Median": [r["labels_median"] for r in rows_el],
        "Labels Mittel": [r["labels_mittel"] for r in rows_el],
        "Labels Maximum": [r["labels_max"] for r in rows_el],
        "k = 3: Fälle abweichend": [r["weicht_ab"] for r in rows_ng],
        "k = 3: Anteil (%)": [100 * r["weicht_ab"] / cases for r in rows_ng],
        "k = 3: Labels Median": [r["labels_median"] for r in rows_ng],
        "k = 3: Labels Mittel": [r["labels_mittel"] for r in rows_ng],
    }
)
st.dataframe(df3, hide_index=True, width="stretch",
             column_config={"Anteil (%)": st.column_config.NumberColumn(format="%.1f %%"), "k = 3: Anteil (%)": st.column_config.NumberColumn(format="%.1f %%"),
                            "Labels Mittel": st.column_config.NumberColumn(format="%.1f"), "k = 3: Labels Mittel": st.column_config.NumberColumn(format="%.1f")})
st.plotly_chart(build_rule_chart(rows_el, rows_ng, cases), width="stretch", key="rule_chart")
kind, text = ev.verdict_rule_table(rows_el, rows_ng, cases)
getattr(st, kind)(text)
st.caption(C.LAST_FROM_MEMORY_TEXT)
miss = tables_rule["verfehlung_nur_kosten"]
st.caption(
    f"Wo „nur Kosten“ den besten Weg verfehlt ({miss['faelle']} Fälle), findet sie im Median {ev.fmt_pct(100 * miss['wert_median'])} des besten reduzierten Kostenwertes "
    f"(Minimum {ev.fmt_pct(100 * miss['wert_min'])}) und in {'allen' if miss['ohne_verbessernde_route'] == 0 else miss['faelle'] - miss['ohne_verbessernde_route']} dieser Fälle noch eine verbessernde Route. "
    f"Ohne Dominanz sind es im Median das {ev.fmt_num(tables_rule['verhaeltnis_keine_zu_voll']['median'])}-Fache der Labels der vollen Regel (je Fall zwischen "
    f"{ev.fmt_dec(tables_rule['verhaeltnis_keine_zu_voll']['min'])} und {ev.fmt_dec(tables_rule['verhaeltnis_keine_zu_voll']['max'])})."
)

st.markdown("**Gegenprobe:** Verfehlt „Kosten + Gedächtnis“ den besten Weg auch dann nie, wenn die Fahrzeit nicht der Entfernung entspricht?")
if st.button(f"Gegenprobe rechnen ({ev.fmt_int(ev.COUNTER_INSTANCES)} Instanzen, einige Sekunden)", key="counter_button"):
    st.session_state["counter_done"] = True
if st.session_state.get("counter_done"):
    with st.spinner("Rechnet die Gegenprobe …"):
        missed = _counter()
    st.dataframe(pd.DataFrame([{"Regel": _rule_label(r), "Instanzen mit verfehltem Weg": len(missed[r]), "Zufalls-Seeds (die ersten drei)": ", ".join(str(s) for s in missed[r][:3])}
                               for r in ev.COUNTER_RULES]), hide_index=True, width="stretch")
    kind, text = ev.verdict_counter(missed, ev.COUNTER_INSTANCES)
    getattr(st, kind)(text)
    st.caption(f"Instanzen: 6 Kunden, Fahrzeiten zufällig zwischen 5 und 60, nicht symmetrisch (Dreiecksungleichung nicht erzwungen; sie ist in allen {ev.fmt_int(ev.COUNTER_INSTANCES)} Instanzen bei mindestens einem Knotentripel verletzt), "
               "Fenster der Breite 30 (jedes Fenster genau 30 breit), zufällige Dualpreise; Zufalls-Seeds 0 bis 2999; Bezug: Aufzählung aller Routen. "
               "Gegenüber der Regel-Tabelle ändert die Gegenprobe zugleich den Instanztyp (zufällige statt euklidischer Fahrzeiten, andere Lage der Fenster), die Kundenzahl (6 statt 7) "
               "und die Fensterbreite (immer genau 30 statt höchstens 30, 80 oder 200); welche Änderung den einen Fall erklärt, ist nicht untersucht.")

st.markdown("---")

# --- Experiment 4 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 4: Wie viele Labels spart die Dominanz?")
st.caption(
    f"Live: eine Zufallsinstanz mit n Kunden, Fensterbreite und Zufalls-Seed aus der Seitenleiste, zufällige Dualpreise (20 bis 70), elementar. Gerechnet wird ohne und mit voller Dominanz; "
    f"bei {ev.fmt_int(C.MAX_LABELS)} erzeugten Labels bricht ein Lauf ab. Gezählt werden Labels, **nicht Sekunden**."
)
with st.spinner("Rechnet beide Läufe (bei 20 Kunden und Breite 200 dauert das einige Sekunden) …"):
    size = _size(int(n), int(width), int(seed))
stats = size.runs[run]
none_run, full_run = size.runs["keine"], size.runs["voll"]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Erzeugte Labels", ev.fmt_int(stats.generated), help=f"Lauf mit {'keiner' if run == 'keine' else 'voller'} Dominanz (Seitenleiste); jedes erzeugte Label, auch ein sofort gestrichenes, plus das Start-Label.")
c2.metric("Gestrichen", ev.fmt_int(stats.dominated), help="Labels, die durch Dominanz entfallen.")
c3.metric("Faktor ohne / mit", "–" if size.factor is None else ev.fmt_num(size.factor), help="Labels ohne Dominanz geteilt durch Labels mit voller Dominanz (beide Läufe).")
c4.metric("Bester Wert", ev.fmt_num(stats.value), help="Kleinste reduzierte Kosten, die der Lauf findet.")
st.caption(f"Gezeigt: der Lauf {'ohne' if run == 'keine' else 'mit voller'} Dominanz. Gestrichen: {ev.fmt_pct(100 * stats.dominated / stats.generated)} der erzeugten Labels. "
           + ("Beide Läufe finden denselben besten Wert." if size.same_value else ("Ein Lauf ist abgebrochen." if size.aborted else "Die beiden Läufe finden verschiedene beste Werte.")))
st.plotly_chart(build_size_chart(stats, int(n)), width="stretch", key="size_chart")
kind, text = ev.verdict_size(int(n), int(width), none_run.generated, full_run.generated, full_run.dominated, size.aborted)
getattr(st, kind)(text)

growth_rows = tables_growth["teil_b"]
st.markdown(f"**Feste Messreihe: Faktor über die Kundenzahl, Fensterbreite {int(width)}** (10 Instanzen je Punkt, Zufalls-Seeds 0 bis 9, elementar)")
live_factor = None if size.factor is None else size.factor
st.plotly_chart(build_factor_chart(growth_rows, int(width), int(n), live_factor), width="stretch", key="factor_chart")
band = [r for r in growth_rows if r["breite"] == int(width)]
st.dataframe(
    pd.DataFrame(
        {
            "Kunden n": [r["n"] for r in band],
            "Labels ohne Dominanz (Median)": [r["labels_ohne_median"] for r in band],
            "Labels mit voller Dominanz (Median)": [r["labels_voll_median"] for r in band],
            "Faktor Median": [r["faktor_median"] for r in band],
            "Faktor Mittel": [r["faktor_mittel"] for r in band],
            "Faktor Maximum": [r["faktor_max"] for r in band],
        }
    ),
    hide_index=True, width="stretch",
    column_config={"Faktor Median": st.column_config.NumberColumn(format="%.2f"), "Faktor Mittel": st.column_config.NumberColumn(format="%.2f"),
                   "Faktor Maximum": st.column_config.NumberColumn(format="%.2f")},
)
st.markdown("**Größere Instanzen (30 Kunden), ganze Spaltenerzeugung (Dualpreise aus der Spaltenerzeugung, nicht zufällig), nicht elementar:** Anteil der erzeugten Labels, die mit voller Dominanz gestrichen werden (je Zeile das Mittel der Anteile je Lauf, gemittelt über die Läufe ohne Abbruch; je 6 Instanzen)")
st.dataframe(
    pd.DataFrame(
        {
            "Fensterbreite": [r["breite"] for r in tables_growth["v1"]],
            "Gedächtnis k": [r["k"] for r in tables_growth["v1"]],
            "Läufe": [r["laeufe"] for r in tables_growth["v1"]],
            "Anteil gestrichen (%)": [r["anteil_verworfen_prozent"] for r in tables_growth["v1"]],
        }
    ),
    hide_index=True, width="stretch", column_config={"Anteil gestrichen (%)": st.column_config.NumberColumn(format="%.1f %%")},
)
edge = {(r["breite"], r["n"]): r for r in growth_rows}
st.caption(f"Hinweise: Bei {C.N_MIN} Kunden ist der Faktor im Median {ev.fmt_num(edge[(80, C.N_MIN)]['faktor_median'])} (Breite 80) bzw. {ev.fmt_num(edge[(200, C.N_MIN)]['faktor_median'])} "
           f"(Breite 200), bei {C.N_MAX} Kunden {ev.fmt_num(edge[(80, C.N_MAX)]['faktor_median'])} bzw. {ev.fmt_num(edge[(200, C.N_MAX)]['faktor_median'])}: In beiden Reihen "
           "wird der Faktor im Median mit der Kundenzahl größer oder bleibt gleich, und bei Breite 200 liegt er bei jeder Kundenzahl höher als bei Breite 80 (Messreihe mit 10 Instanzen je Punkt, beide Breiten in der Tabelle der README). Die Sekunden dieser Python-Fassung sind kein Thema dieser Demo: Die Dominanzprüfung kostet je Label Zeit, und eine Zeitersparnis wird nicht behauptet. Die Mediane der Labels sind auf ganze Zahlen gerundet, die Faktoren werden je Instanz gerechnet.")

st.markdown("---")

# --- Experiment 5 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 5: Was passiert in der Spaltenerzeugung?")
cg = tables_colgen
st.caption(
    f"Feste Messreihe: {cg['instanzen']} Instanzen mit {cg['kunden']} Kunden, Fensterbreite {cg['breite']}, elementar. Die Spaltenerzeugung ruft das Label-Verfahren in jeder Runde mit neuen Dualpreisen auf "
    "und endet, wenn es keinen Weg mit negativen reduzierten Kosten mehr findet. Ihre Schlusszahl (die **Schranke**) ist nur dann eine gültige Untergrenze für die Gesamtplanung, "
    "wenn das Label-Verfahren jedes Mal den besten Weg fand. Verglichen: volle Dominanz gegen „nur Kosten“."
)
df5 = pd.DataFrame(
    {
        "Instanz (Zufalls-Seed)": [r["seed"] for r in cg["zeilen"]],
        "Schranke, volle Regel": [r["schranke_voll"] for r in cg["zeilen"]],
        "Schranke, nur Kosten": [r["schranke_kosten"] for r in cg["zeilen"]],
        "Unterschied (%)": [r["unterschied_prozent"] for r in cg["zeilen"]],
        "Labels, volle Regel": [r["labels_voll"] for r in cg["zeilen"]],
        "Labels, nur Kosten": [r["labels_kosten"] for r in cg["zeilen"]],
        "Runden, volle Regel": [r["iterationen_voll"] for r in cg["zeilen"]],
        "Runden, nur Kosten": [r["iterationen_kosten"] for r in cg["zeilen"]],
    }
)
st.dataframe(df5, hide_index=True, width="stretch",
             column_config={"Schranke, volle Regel": st.column_config.NumberColumn(format="%.4f"), "Schranke, nur Kosten": st.column_config.NumberColumn(format="%.4f"),
                            "Unterschied (%)": st.column_config.NumberColumn(format="%.3f")})
st.plotly_chart(build_colgen_chart(cg["zeilen"]), width="stretch", key="colgen_chart")
summary = ev.colgen_summary(cg["zeilen"])
kind, text = ev.verdict_colgen(summary)
getattr(st, kind)(text)
st.caption("Die Dualpreise kommen hier aus der Spaltenerzeugung selbst, nicht aus der Zufallsziehung der anderen Experimente. Eine Schranke, die bei „nur Kosten“ gleich bleibt (Unterschied 0), "
           "zeigt nur, dass die fehlenden Wege in dieser Instanz nicht nötig waren.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
ng_rows = {r["regel"]: r for r in tables_rule["ng3"]}
st.markdown(
    f"""
| Annahme | Was passiert, wenn sie nicht gilt | Belegt durch |
|---|---|---|
| **Fahrzeit gleich Entfernung** (Dreiecksungleichung gilt) | „Kosten + Gedächtnis“ kann den besten Weg verfehlen: In der Gegenprobe von Experiment 3 geschieht das bei 1 von {ev.fmt_int(ev.COUNTER_INSTANCES)} Instanzen (6 Kunden, Fenster der Breite 30, zufällige nicht symmetrische Fahrzeiten, Dreiecksungleichung nicht erzwungen); die Gegenprobe ändert zugleich Instanztyp, Kundenzahl und Fensterbreite, und ob die Dreiecksungleichung die Ursache ist, ist nicht untersucht. | Gegenprobe (`tests/test_claims.py`) |
| **Jeder Kunde höchstens einmal** (elementar) | Mit lockererem Gedächtnis (k = 3) weicht „Kosten + Gedächtnis“ in {ng_rows['kosten_gedaechtnis']['weicht_ab']} von {cases} Fällen ab, die volle Regel in keinem. | Experiment 3 |
| **Warten ist erlaubt und kostenlos** | Ohne Warten gilt „früher ankommen ist nie schlechter“ nicht; die Zeitbedingung wäre anders zu fassen. | nicht gemessen |
| **Nur Zeit und Last als Grenzen** | Jede weitere Grenze (zum Beispiel Fahrerzeit) braucht eine eigene Bedingung in der Dominanz. | nicht gemessen |
| **Zufällige Dualpreise** (Experimente 3 und 4, außer der 30-Kunden-Reihe) | In einer echten Spaltenerzeugung ändern sich die Dualpreise in jeder Runde; Experiment 5 rechnet das für {cg['instanzen']} Instanzen, die 30-Kunden-Reihe in Experiment 4 für je 6 Instanzen. | Experiment 5, Experiment 4 (30 Kunden) |
| **Bis 20 Kunden** | Bei 30 Kunden ist nur der Anteil gestrichener Labels gemessen, nicht der Faktor. | Experiment 4 |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    # erklaerseite:lesehilfe:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/dominanz-teilwege-erklaert.json, nicht von Hand ändern)
    st.markdown(
        r"""
**Lesehilfe.** Gegeben sind ein Depot und Kunden mit Entfernungen, Lasten, Zeitfenstern und Dualpreisen. Gesucht ist die Route ab und bis zum Depot mit den kleinsten reduzierten Kosten, jeder Kunde höchstens einmal. Das Label-Verfahren verlängert Teilwege Kunde für Kunde und streicht dominierte Labels.

| Symbol | Bedeutung |
|---|---|
| $i, j$ | Knoten; $0$ ist das Depot, $1,\dots,n$ sind Kunden |
| $d_{ij}$ | Entfernung von $i$ nach $j$; gleich der Fahrzeit |
| $\pi_j$ | Dualpreis des Kunden $j$ ($\pi_0 = 0$) |
| $q_j$, $Q$ | Last des Kunden $j$; Kapazität des Fahrzeugs |
| $e_j$, $l_j$ | frühester und spätester Beginn der Bedienung bei $j$ |
| $s$, $H$ | Bedienzeit je Kunde; Horizont (späteste Rückkehr ins Depot) |
| $\bar c(r)$ | reduzierte Kosten der Route $r$ |
| $(T, C, R, V)$ | Label: Zeit, reduzierte Kosten, verbrauchte Last, besuchte Kunden (Gedächtnis) |
| $L_1 \preceq L_2$ | Label $L_1$ dominiert Label $L_2$ (am selben Kunden) |

[Schritt für Schritt erklärt, mit Herleitung und Literatur](https://sebastianhanisch.net/dominanz-teilwege-erklaert.html#fachleute)
        """
    )
    # erklaerseite:lesehilfe:end
    st.markdown(
        r"""
**Reduzierte Kosten** einer Route $r = (j_0 = 0, j_1, \dots, j_m, j_{m+1} = 0)$:

$$\bar c(r) = \sum_{t=0}^{m} d_{j_t j_{t+1}} - \sum_{t=1}^{m} \pi_{j_t}$$

**Fortsetzung** eines Labels $(T, C, R, V)$ am Knoten $i$ zum Kunden $j \notin V$ (mit $s\,[i \ne 0]$: im Depot entfällt die Bedienzeit):

$$T' = \max\bigl(e_j,\; T + s\,[i \ne 0] + d_{ij}\bigr), \quad C' = C + d_{ij} - \pi_j, \quad R' = R + q_j, \quad V' = V \cup \{j\}$$

Zulässig ist sie, wenn $T + s\,[i \ne 0] + d_{ij} \le l_j$ und $R' \le Q$ gelten. Zurück ins Depot geht es, wenn

$$T + s + d_{i0} \le H$$

Die Formel für $V'$ gilt elementar ($k = n$). Mit Gedächtnis $k < n$ gilt $V' = (V \cap N_k(j)) \cup \{j\}$; dabei sind $N_k(j)$ die $k$ nächsten Kunden von $j$ einschließlich $j$, und ein Label vergisst Kunden außerhalb davon.

**Dominanz** (volle Regel):

$$L_1 \preceq L_2 \iff C_1 \le C_2, \quad T_1 \le T_2, \quad R_1 \le R_2, \quad V_1 \subseteq V_2$$

**Warum die volle Regel nichts verliert** (sofern Warten erlaubt und kostenlos ist und keine weiteren Grenzen als Zeit und Last gelten): Jede zulässige Fortsetzung von $L_2$ ist auch für $L_1$ zulässig (früher oder gleich spät ankommen hält Fenster und Horizont ein, weil Warten erlaubt ist;
weniger oder gleich viel Last; weniger besuchte Kunden heißt mehr freie Kunden) und kostet, weil die Kosten Summen sind, am Ende nicht mehr. Bei Gleichstand in allen vier Größen bleibt das ältere Label.
**Wo eine Bedingung fehlt,** gilt dieses Argument nicht, mit einer Ausnahme: Elementar folgt die Last aus dem Gedächtnis ($R = \sum_{j \in V} q_j$ mit $q_j \ge 0$, also $V_1 \subseteq V_2 \Rightarrow R_1 \le R_2$); die Regeln mit Gedächtnis brauchen die Last-Bedingung dann nicht, bei Gedächtnis $k = 3$ schon (Experiment 3). Ohne Gedächtnis bricht je ein Schritt des Arguments, wenn eine Bedingung fehlt; Experiment 2 zeigt am Handbeispiel für die Regeln, die dort den besten Weg verlieren, welche Fortsetzung fehlt (dass das Argument bricht, heißt nicht, dass jede Instanz verliert). Dass „Kosten + Gedächtnis“ in der Regel-Tabelle keinen Fall verfehlt, ist eine
Beobachtung an den gemessenen Instanzen (Gegenprobe in Experiment 3), kein Satz.

**Literatur** (Prüfstand: Autoren, Titel, Zeitschrift und Jahr per Suchtreffer geprüft; die Volltexte sind nicht gelesen, die Demo übernimmt keine Zahl daraus):
- Desrochers, Soumis (1988): A generalized permanent labelling algorithm for the shortest path problem with time windows, INFOR 26 (Labels beim Weg mit Zeitfenstern).
- Feillet, Dejax, Gendreau, Gueguen (2004): An exact algorithm for the elementary shortest path problem with resource constraints, Networks 44 (Elementarität als Ressource, Dominanz mit Besuchsmengen).
- Irnich, Desaulniers (2005): Shortest path problems with resource constraints, Kapitel 2 in *Column Generation*, Springer (Dominanz mit Erweiterungsfunktionen).
        """
    )

st.markdown("---")

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(C.ASSUMPTIONS_MARKDOWN)

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Ressourcenwege: von der Grenze zur Verfahrenswahl](https://sebastianhanisch.net/konzepte-ressourcenwege.html)."
)
