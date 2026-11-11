"""Konstanten: Regler-Grenzen, feste Annahmen, Farben, Schnellstart-Szenarien und Texte, die App und README gemeinsam haben."""

# --- Regler ---------------------------------------------------------------------------------------------------------------------------------
# Komplexität am Regler-Maximum (n = 20, Breite 200): Ohne Dominanz liegt die Zahl der Labels im Median bei 51 322, mit voller Dominanz bei 14 690
# (README, Wachstumstabelle, Zufalls-Seeds 0 bis 9, `tests/test_claims.py::test_growth_cell`). MAX_LABELS fängt Ausreißer ab.
N_MIN, N_MAX, DEFAULT_N = 7, 20, 10
WIDTH_OPTIONS, DEFAULT_WIDTH = (80, 200), 80
SEED_MAX, DEFAULT_SEED = 999999, 1
MAX_LABELS = 300_000                     # Abbruch eines Live-Laufs bei so vielen erzeugten Labels
EQUAL_FACTOR = 1.2                       # Faktor (Labels ohne / mit Dominanz) unter diesem Wert gilt als „gleichauf“

LIVE_RULES = ("keine", "kosten", "kosten_zeit", "kosten_last", "kosten_gedaechtnis", "voll")   # im Handbeispiel wählbar
RUN_RULES = ("keine", "voll")                                                                   # im Größenversuch wählbar
TABLE_RULES = ("keine", "kosten", "kosten_zeit", "kosten_last", "kosten_gedaechtnis", "kosten_zeit_last", "kosten_zeit_gedaechtnis",
               "kosten_last_gedaechtnis", "voll")                                               # Reihenfolge der Regel-Tabelle
RULE_LABELS = {
    "keine": "keine Dominanz",
    "kosten": "nur Kosten",
    "kosten_zeit": "Kosten + Zeit",
    "kosten_last": "Kosten + Last",
    "kosten_gedaechtnis": "Kosten + Gedächtnis",
    "kosten_zeit_last": "Kosten + Zeit + Last",
    "kosten_zeit_gedaechtnis": "Kosten + Zeit + Gedächtnis",
    "kosten_last_gedaechtnis": "Kosten + Last + Gedächtnis",
    "voll": "volle Dominanz (Kosten, Zeit, Last, Gedächtnis)",
}

# --- Farben ---------------------------------------------------------------------------------------------------------------------------------
COLOR_OK = "#2F6B65"
COLOR_BAD = "#C0392B"
COLOR_OTHER = "rgba(150,150,150,0.55)"
COLOR_LINE = "#4c78a8"
COLOR_LINE2 = "#e08a2c"
CELL_OK = "background-color: rgba(46, 160, 67, 0.28)"
CELL_BAD = "background-color: rgba(218, 54, 51, 0.30)"

# --- Schnellstart-Szenarien -----------------------------------------------------------------------------------------------------------------
# Jedes Szenario setzt alle fünf Regler: Regel im Handbeispiel, Kundenzahl, Fensterbreite und Zufalls-Seed des Größenversuchs, Regel des Größenversuchs.
PRESETS = {
    "Volle Dominanz (Voreinstellung)": {"rule": "voll", "n": DEFAULT_N, "width": DEFAULT_WIDTH, "seed": DEFAULT_SEED, "run": "voll"},
    "Nur nach Kosten streichen": {"rule": "kosten", "n": DEFAULT_N, "width": DEFAULT_WIDTH, "seed": DEFAULT_SEED, "run": "voll"},
    "Kosten und Zeit": {"rule": "kosten_zeit", "n": DEFAULT_N, "width": DEFAULT_WIDTH, "seed": DEFAULT_SEED, "run": "voll"},
    "Kosten und Gedächtnis": {"rule": "kosten_gedaechtnis", "n": DEFAULT_N, "width": DEFAULT_WIDTH, "seed": DEFAULT_SEED, "run": "voll"},
    "20 Kunden, breite Fenster, nichts streichen": {"rule": "keine", "n": 20, "width": 200, "seed": 1, "run": "keine"},
    "7 Kunden, wenig Ersparnis": {"rule": "voll", "n": 7, "width": 80, "seed": 4, "run": "voll"},
}
PRESET_HELP = {
    "Volle Dominanz (Voreinstellung)": "Handbeispiel mit der vollen Regel (Kosten, Zeit, Last, besuchte Kunden); Größenversuch mit 10 Kunden, Fensterbreite 80, Zufalls-Seed 1.",
    "Nur nach Kosten streichen": "Handbeispiel mit der zu großzügigen Regel „nur Kosten“: Sie findet den besten Weg nicht.",
    "Kosten und Zeit": "Handbeispiel mit „Kosten + Zeit“: Der beste Weg geht eine Stufe später verloren.",
    "Kosten und Gedächtnis": "Handbeispiel mit „Kosten + Gedächtnis“: findet hier den besten Weg; in der Regel-Tabelle (Experiment 3) verfehlt diese Regel ihn bei 7 Kunden in keinem Fall.",
    "20 Kunden, breite Fenster, nichts streichen": "Größenversuch mit 20 Kunden, Fensterbreite 200 und Zufalls-Seed 1, ohne jede Dominanz; Handbeispiel ebenfalls ohne Dominanz.",
    "7 Kunden, wenig Ersparnis": "Größenversuch mit 7 Kunden, Fensterbreite 80 und Zufalls-Seed 4: ein Beispiel, in dem die Dominanz wenig spart (gleichauf: Faktor unter 1,2).",
}

# --- Text, den App und README gleich führen -------------------------------------------------------------------------------------------------
# Erklärung zur Regel-Tabelle (Experiment 3): warum die Last-Bedingung elementar neben dem Gedächtnis überflüssig ist (`tests/test_claims.py` prüft sie und den Wortlaut in der README).
LAST_FROM_MEMORY_TEXT = (
    "**Last und Gedächtnis.** Elementar (jeder Kunde höchstens einmal) ist die verbrauchte Last die Summe der Lasten der besuchten Kunden, und Lasten sind nicht negativ: "
    "Ist die Menge V₁ in V₂ enthalten, gilt automatisch R₁ ≤ R₂. Darum ändert die Last-Bedingung nichts, wenn das Gedächtnis geprüft wird: „Kosten + Gedächtnis“ und "
    "„Kosten + Last + Gedächtnis“ haben dieselben Label-Zahlen, „Kosten + Zeit + Gedächtnis“ dieselben wie die volle Regel. Beim Gedächtnis k = 3 vergisst ein Label Kunden; "
    "seine Last ist dann nicht mehr durch die gemerkten Kunden bestimmt, und die Last bleibt eine eigene Bedingung (dort unterscheiden sich „Kosten + Gedächtnis“ und "
    "„Kosten + Last + Gedächtnis“). Das folgt aus der Definition der Last und ist keine Messung; die 180 Fälle bestätigen es."
)

ASSUMPTIONS_MARKDOWN = """\
**Annahmen**
- Eigene Instanzen im Stil der Solomon-Instanzen (Quadrat 100 × 100, Fahrzeit gleich Entfernung, Bedienzeit 10, Kapazität 70, Horizont 300), **nicht die Originalinstanzen**; das Handbeispiel rechnet mit dem Manhattan-Abstand auf einem Gitter.
- Warten vor einem Zeitfenster ist erlaubt und kostenlos; nur deshalb gilt „früher ankommen ist nie schlechter“ als Dominanzbedingung für die Zeit.
- Die Dualpreise der Größenversuche, der Wachstumsreihen bis 20 Kunden und der Regel-Tabelle sind zufällig gezogen (gleichverteilt zwischen 20 und 70), nicht die einer echten Spaltenerzeugung; die ganze Spaltenerzeugung rechnen nur die 30-Kunden-Reihe (Experiment 4) und Teil C der Messreihen (Experiment 5).
- Gezählt werden erzeugte Labels, nicht Sekunden.

**Grenzen**
- Die Regel-Tabelle (180 Fälle) hat nur 7 Kunden; die Messreihen zum Wachstum haben je 10 Instanzen je Zelle; die Spaltenerzeugung ist an 10 Instanzen mit 10 Kunden gemessen.
- Gemessen sind genau die Regeln dieser Demo, nicht andere Dominanzregeln aus der Literatur (etwa mit Erweiterungsfunktionen oder bei mehr als zwei Grenzen).
- Die Demo macht **keine allgemeine Aussage über Rechenzeit**: In reinem Python kostet die Dominanzprüfung je Label Zeit; in einer einzelnen Messung der README (20 Kunden, Fensterbreite 200, auf einem ausgelasteten Rechner, nicht im Test, vom Rechner abhängig) war die Rechnung mit Dominanz langsamer als ohne, obwohl sie weniger Labels erzeugt; für andere Größen, auch für 30 Kunden, gibt es keine Zeitmessung.

**Bekannte Probleme und Unsicherheiten**
- Ursachen („weil …“) sind Deutungen, wo es dasteht; gemessen sind die Zählungen.
- Die Zahlen der Spaltenerzeugung (Experiment 5) hängen vom Weg ab, den der Löser des Master-Problems nimmt, und können mit einer anderen Version der Bibliothek leicht abweichen.
- Die Darstellung der Tabellen und Diagramme ist im Browser am Computer und in einem 375 Pixel breiten Fenster durchgesehen, nicht auf anderen Geräten oder in anderen Browsern. Die Diagramme haben keine Auswahl per Mausklick.
"""
