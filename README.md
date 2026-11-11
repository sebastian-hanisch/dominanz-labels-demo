# Dominanz: wann darf ein Label gehen? – Streamlit-Demo

Demo zum Thema Ressourcenwege und Spaltenerzeugung auf der Website „Sebastian Hanisch – Operations Research und Machine Learning“. Das **Label-Verfahren** sucht
den Weg mit den kleinsten **reduzierten Kosten** (Weglänge minus die Dualpreise der besuchten Kunden), mit Zeitfenstern, Last und höchstens einem Besuch je Kunde; es ist das Preisproblem der
Spaltenerzeugung. Jeder Teilweg ist ein **Label** (Kosten, Zeit, Last, besuchte Kunden). Diese Demo fragt nur eines: **Welches Label darf gestrichen werden, ohne den besten Weg zu verlieren?**
Gezählt werden erzeugte Labels, keine Sekunden.

Die Anwendung in einem Fall zeigt [crew-pairing-demo](https://github.com/sebastian-hanisch/crew-pairing-demo) (Besatzungsplanung im Zugverkehr: Dominanz als Werkzeug des Preisproblems, nicht gemessen).
Dominanz zwischen zwei Kosten (Pareto-Front) erklärt [multicriteria-demo](https://github.com/sebastian-hanisch/multicriteria-demo); hier kommen Verbrauch gegen eine Grenze und die besuchten Kunden dazu.
Die Spaltenerzeugung mit kürzestem Weg als Preisproblem zeigt [mcf-column-generation-demo](https://github.com/sebastian-hanisch/mcf-column-generation-demo).
**Abgrenzung:** [hub-labeling-demo](https://github.com/sebastian-hanisch/hub-labeling-demo) meint etwas anderes (vorberechnete Listen für schnelle Abfragen kürzester Wege); hier sind Labels Teilwege.

## Warum dieses Problem

Ohne Streichen wächst die Zahl der Labels mit der Zahl der Kunden und der Fensterbreite: im Median von 94 Labels (7 Kunden, Breite 80) auf 51 322 (20 Kunden, Breite 200; Wachstumstabelle unten, eigene Zufallsinstanzen, Python). Wer großzügig streicht, rechnet weniger, kann aber den besten Weg verlieren. Die Regel, nach der ein Label gehen
darf, ist deshalb keine Nebensache: Ein Label darf sicher gestrichen werden, wenn ein anderes Label am selben Kunden in allem mindestens so gut ist, was die Zukunft des Weges beeinflusst (Kosten, Zeit, Last und
besuchte Kunden), sofern Warten erlaubt und kostenlos ist und keine weiteren Grenzen als Zeit und Last gelten. Die Demo zeigt das an einem Handbeispiel mit sechs Kunden, zählt es an 180 Fällen aus und misst, was ein zu großzügiges Streichen in der Spaltenerzeugung anrichtet.

## Modell

Ein Depot und Kunden mit Last, Zeitfenster und Dualpreis; Entfernung = Fahrzeit; Warten vor einem Fenster ist kostenlos; Kapazität, Horizont (späteste Rückkehr) und Bedienzeit je Kunde. Ein Label am Kunden $i$ ist
$(T, C, R, V)$: Zeit, reduzierte Kosten, verbrauchte Last, besuchte Kunden (Gedächtnis). **Volle Dominanz:** $L_1$ dominiert $L_2$, wenn $C_1 \le C_2$, $T_1 \le T_2$, $R_1 \le R_2$ und $V_1 \subseteq V_2$;
bei Gleichstand bleibt das ältere Label. Die Formeln stehen im Expander **📐 Mathematische Formulierung** der App (`app.py`), mit Lesehilfe; der Expander **💬 In einfachen Worten** fasst das Verfahren ohne Formeln zusammen ([ausführlich erklärt](https://sebastianhanisch.net/dominanz-teilwege-erklaert.html)).

Zwei Arten von Instanzen: das **Handbeispiel** (6 Kunden, Manhattan-Abstand auf einem Gitter, alle Zahlen ganz, Bedienzeit 2, Horizont 36, Kapazität 12) und **Zufallsinstanzen im Stil der Solomon-Instanzen**
(Quadrat 100 × 100, Fahrzeit gleich Entfernung, Bedienzeit 10, Kapazität 70, Horizont 300, Fensterbreite höchstens 30, 80 oder 200, auf die erreichbare Zeitspanne beschnitten; **nicht die Originalinstanzen**) mit zufälligen Dualpreisen (gleichverteilt zwischen 20 und 70).

## Methodik

Das Label-Verfahren verlängert Labels in Zeitreihenfolge um je einen Kunden (`dml_algorithm.py`, `price`). Die **Dominanzregel** ist wählbar: keine, nur Kosten, Kosten + Zeit, Kosten + Last, Kosten + Gedächtnis
(besuchte Kunden als Teilmenge), Kosten + Zeit + Last und die volle Regel; in der Regel-Tabelle dazu zwei weitere Mischformen. Ein **Orakel** (Tiefensuche über alle Routen, ohne Labels) liefert den Bezug.
„Gedächtnis k = 3“ heißt: Ein Label merkt sich besuchte Kunden nur, solange sie zu den 3 nächsten Kunden (den Kunden selbst eingerechnet) jedes weiteren Halts gehören; sonst darf der Kunde wiederkehren
(nicht elementar, eine Wiederkehr schon nach einem Halt dazwischen ist möglich); k = Kundenzahl heißt jeder Kunde höchstens einmal (elementar).
Bei gleicher Entfernung zählt der Kunde mit der kleineren Nummer zuerst (stabile Sortierung), und der Halt selbst gehört immer dazu. In den 180 Fällen der Regel-Tabelle (euklidische Entfernungen) liegt an der Grenze
zwischen dem 3. und dem 4. nächsten Kunden nie ein Gleichstand (0 von 1 260 Fällen: 7 Halte mal 180 Fälle); das Gitter des Handbeispiels hat solche Gleichstände (bei k = 3 zum Beispiel am Kunden 4 die Kunden 1 und 6, beide Entfernung 5),
dort rechnet die Demo aber nur elementar, die Regel greift also nicht.
Die **Experimente** der App: (1) Handbeispiel Schritt für Schritt, jede Streichung mit den vier Vergleichen; (2) wo der beste Weg bei einer zu großzügigen Regel verloren geht; (3) Regel-Tabelle aus 180 Fällen und eine
Gegenprobe; (4) Größenversuch live (7 bis 20 Kunden) mit festen Messreihen; (5) Folge für die Spaltenerzeugung.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen sind Zählungen erzeugter Labels (jedes erzeugte Label, auch ein sofort gestrichenes, plus das Start-Label) oder Zählungen von Fällen an **festen Zufalls-Seeds**, Python, die genannten Instanzen und Dualpreise.
Sie sagen nichts über andere Dominanzregeln der Literatur aus. Die Spalte „Test“ nennt die Prüfung in `tests/test_claims.py` bzw. die genannte Testdatei (Zahl-zu-Test-Tabelle).

| Frage | Befund (Voraussetzung im Satz) | Test |
|---|---|---|
| Handbeispiel: beste Route? | 52 zulässige Routen (Aufzählung, 6 Kunden, elementar); beste 6-2-3-5 mit reduzierten Kosten −22, zweitbeste −18; der beste Weg ist eindeutig. | `test_algorithm.py::test_enumeration_finds_52_routes…` |
| Handbeispiel: Labels je Regel | Erzeugte / gestrichene Labels: keine 53 / 0; nur Kosten 18 / 11; Kosten + Zeit 35 / 19; Kosten + Last 41 / 20; Kosten + Gedächtnis 45 / 15; Kosten + Zeit + Last 42 / 20; Kosten + Zeit + Gedächtnis 45 / 15; Kosten + Last + Gedächtnis 45 / 15; volle Regel 45 / 15 (alle neun Regeln der Regel-Tabelle; „Kosten + Last + Gedächtnis“ gleicht „Kosten + Gedächtnis“ und „Kosten + Zeit + Gedächtnis“ der vollen Regel, weil elementar die Last aus dem Gedächtnis folgt, siehe „Last und Gedächtnis“ unter der Regel-Tabelle). | `test_algorithm.py::test_each_rule_on_the_hand_example…` |
| Handbeispiel: welche Regeln verfehlen den besten Weg? | „nur Kosten“ findet 2-3-6-5 mit −16 (die Aufzählung kennt zwei gleich gute Wege mit −16, 2-3-6-5 und 3-2-6-5; die Regel erzeugt 3-2-6-5 nicht, weil das Label des Teilwegs 3 vom Label des Teilwegs 2-3 verdrängt wird), „Kosten + Zeit“ findet 2-6-3-5 mit −18; alle anderen Regeln finden 6-2-3-5 mit −22. | `test_algorithm.py` (gleiche Tabelle) |
| 180 Fälle (60 Instanzen mit 7 Kunden × Fensterbreiten 30, 80, 200, elementar): weicht die volle Regel vom Orakel ab? | In 0 von 180 Fällen; „keine Dominanz“ ebenfalls in 0. | `test_oracle_dominanz_labels.py`, `test_claims.py` |
| 180 Fälle: verfehlt „nur Kosten“ den besten Weg? | In 67 von 180 Fällen (37,2 %); dort findet sie im Median 87,6 % des besten reduzierten Kostenwertes (Minimum 18,3 %) und in allen 67 noch eine verbessernde Route. | `test_claims.py` |
| 180 Fälle, Gedächtnis k = 3 (Bezug: Ergebnis ohne Dominanz bei k = 3) | Abweichungen: nur Kosten 72, Kosten + Zeit 35, Kosten + Last 22, Kosten + Gedächtnis 31, Kosten + Zeit + Last 14, Kosten + Zeit + Gedächtnis 10, Kosten + Last + Gedächtnis 2, volle Regel 0. | `test_claims.py` |
| 180 Fälle, elementar: wie oft verfehlt jede Regel mit Gedächtnis? | Kosten + Gedächtnis, Kosten + Zeit + Gedächtnis, Kosten + Last + Gedächtnis und die volle Regel je 0 von 180; die Last-Bedingung ändert bei Prüfung des Gedächtnisses die Label-Zahl in keinem der 180 Fälle (bei k = 3 in mindestens einem); der Grund steht unter der Regel-Tabelle (elementar folgt die Last aus dem Gedächtnis). | `test_claims.py`, `test_algorithm.py::test_every_rule_changes…` |
| Gegenprobe: 3 000 Zufallsinstanzen mit 6 Kunden, Fenster der Breite 30 (jedes Fenster genau 30 breit, alle 18 000 Fenster nachgerechnet), zufällige, nicht symmetrische Fahrzeiten zwischen 5 und 60 (Dreiecksungleichung nicht erzwungen; gemessen: in allen 3 000 Instanzen bei mindestens einem Knotentripel verletzt, im Zufalls-Seed 209 bei 31 von 210 Knotentripeln; Zufalls-Seeds 0 bis 2999, elementar) | Verfehlter Weg gegen die Aufzählung: nur Kosten 413, Kosten + Zeit 144, Kosten + Last 42, **Kosten + Gedächtnis 1** (Zufalls-Seed 209), Kosten + Zeit + Last 0, volle Regel 0. | `test_claims.py::test_counter_sample…`, `test_claims.py::test_counter_sample_violates_the_triangle_inequality…` |
| 180 Fälle: wie viel mehr Labels ohne Dominanz? | Je Fall im Median das 1,42-Fache der Labels der vollen Regel (Minimum 1,00, Maximum 4,86). | `test_claims.py` |
| Wachstum: Labels ohne gegen mit voller Dominanz (je Zelle 10 Instanzen, Zufalls-Seeds 0 bis 9, elementar) | Siehe Tabelle unten: bei 7 Kunden ist der Faktor im Median 1,35 (Breite 80) bzw. 2,08 (Breite 200), bei 20 Kunden 2,36 bzw. 3,49; größter Einzelfaktor 6,02 (Breite 200, 14 Kunden). | `test_claims.py::test_growth_cell` |
| 30 Kunden, ganze Spaltenerzeugung, nicht elementar (Gedächtnis k = 1, 3, 5), Fensterbreite 40, 100, 200, je 6 Instanzen | Anteil der erzeugten Labels, die gestrichen werden (volle Regel): 78,2 bis 91,4 % (je Zeile das Mittel der Anteile je Lauf, gemittelt über die Läufe ohne Abbruch; Quelle: `data/wachstum.json`). | `test_claims.py::test_growth_v1…` (Zeilen der Messreihe, ein Lauf neu gerechnet) |
| Spaltenerzeugung, 10 Instanzen mit 10 Kunden, Fensterbreite 80, elementar, Überdeckungs-Master | Mit „nur Kosten“ endet sie in 5 von 10 Instanzen bei einer höheren Zahl als mit der vollen Regel (Abstand zur Schranke der vollen Regel, bezogen auf diese: Mittel 1,216 %, Maximum 8,476 %; das Mittel läuft über alle 10 Instanzen, auch über die 5 ohne Unterschied); diese Zahl ist dann keine gültige Untergrenze mehr. | `test_claims.py::test_colgen_…` |

**Regel-Tabelle (Experiment 3), 180 Fälle.** Labels: Median / Mittel / Maximum über die 180 Fälle.

| Regel | elementar: Weg verfehlt | Labels Median / Mittel / Maximum | Gedächtnis k = 3: weicht ab | Labels Median / Mittel |
|---|---|---|---|---|
| keine Dominanz | 0 (0,0 %) | 85 / 188,1 / 1 404 | 0 (0,0 %) | 85 / 254,8 |
| nur Kosten | 67 (37,2 %) | 26 / 27,4 / 49 | 72 (40,0 %) | 26 / 28,2 |
| Kosten + Zeit | 37 (20,6 %) | 42 / 51,4 / 150 | 35 (19,4 %) | 42 / 55,4 |
| Kosten + Last | 20 (11,1 %) | 52 / 66,7 / 203 | 22 (12,2 %) | 52 / 72,6 |
| Kosten + Gedächtnis | 0 (0,0 %) | 58 / 91,8 / 378 | 31 (17,2 %) | 40 / 47,9 |
| Kosten + Zeit + Last | 12 (6,7 %) | 56 / 73,5 / 253 | 14 (7,8 %) | 56 / 81,5 |
| Kosten + Zeit + Gedächtnis | 0 (0,0 %) | 58 / 94,5 / 403 | 10 (5,6 %) | 51 / 83,7 |
| Kosten + Last + Gedächtnis | 0 (0,0 %) | 58 / 91,8 / 378 | 2 (1,1 %) | 56 / 89,8 |
| volle Dominanz (Kosten, Zeit, Last, Gedächtnis) | 0 (0,0 %) | 58 / 94,5 / 403 | 0 (0,0 %) | 57 / 102,0 |

Die Mediane stehen als ganze Zahlen; wo der Median das Mittel zweier Werte ist, ist er gerundet und weicht um 0,5 ab (z. B. 58 statt 58,5, 40 statt 39,5 und 56 statt 56,5).

**Last und Gedächtnis.** Elementar (jeder Kunde höchstens einmal) ist die verbrauchte Last die Summe der Lasten der besuchten Kunden, und Lasten sind nicht negativ: Ist die Menge V₁ in V₂ enthalten, gilt automatisch R₁ ≤ R₂. Darum ändert die Last-Bedingung nichts, wenn das Gedächtnis geprüft wird: „Kosten + Gedächtnis“ und „Kosten + Last + Gedächtnis“ haben dieselben Label-Zahlen, „Kosten + Zeit + Gedächtnis“ dieselben wie die volle Regel. Beim Gedächtnis k = 3 vergisst ein Label Kunden; seine Last ist dann nicht mehr durch die gemerkten Kunden bestimmt, und die Last bleibt eine eigene Bedingung (dort unterscheiden sich „Kosten + Gedächtnis“ und „Kosten + Last + Gedächtnis“). Das folgt aus der Definition der Last und ist keine Messung; die 180 Fälle bestätigen es.

**Wachstum der Labels (Experiment 4), je Zelle 10 Instanzen.** „Faktor“ ist je Instanz die Zahl der Labels ohne Dominanz geteilt durch die mit voller Dominanz; Median, Mittel (der Faktoren, nicht Verhältnis der Mittel) und Maximum über die 10 Instanzen.

| Breite | n | Labels ohne Dominanz (Median) | mit voller Dominanz (Median) | Faktor Median | Mittel | Maximum |
|---|---|---|---|---|---|---|
| 80 | 7 | 94 | 60 | 1,35 | 1,46 | 2,14 |
| 80 | 8 | 122 | 86 | 1,46 | 1,47 | 2,00 |
| 80 | 9 | 182 | 127 | 1,46 | 1,54 | 2,38 |
| 80 | 10 | 295 | 156 | 1,73 | 1,87 | 2,77 |
| 80 | 12 | 602 | 300 | 1,91 | 1,92 | 2,86 |
| 80 | 14 | 1 138 | 586 | 2,08 | 2,09 | 2,88 |
| 80 | 16 | 1 408 | 692 | 2,08 | 2,13 | 2,98 |
| 80 | 20 | 4 424 | 1 878 | 2,36 | 2,53 | 4,37 |
| 200 | 7 | 364 | 134 | 2,08 | 2,27 | 3,79 |
| 200 | 8 | 602 | 279 | 2,26 | 2,36 | 3,17 |
| 200 | 9 | 1 436 | 530 | 2,35 | 2,63 | 4,96 |
| 200 | 10 | 1 768 | 597 | 2,86 | 2,98 | 4,16 |
| 200 | 12 | 4 219 | 1 546 | 2,94 | 3,18 | 5,59 |
| 200 | 14 | 11 589 | 3 073 | 3,17 | 3,80 | 6,02 |
| 200 | 16 | 14 589 | 4 453 | 3,39 | 3,63 | 5,36 |
| 200 | 20 | 51 322 | 14 690 | 3,49 | 3,56 | 4,65 |

Auch hier sind die Medianspalten gerundet (z. B. 94 statt 93,5 und 60 statt 60,5 bei Breite 80 und 7 Kunden); die Faktoren werden je Instanz gerechnet und sind davon nicht betroffen. In beiden Breiten wird der Faktor im Median mit der Kundenzahl größer oder bleibt gleich (Breite 80: gleich bei 8 und 9 sowie bei 14 und 16 Kunden), und bei jeder Kundenzahl liegt er bei Breite 200 höher als bei Breite 80 (`test_claims.py::test_growth_median_factor_rises_with_n_and_width`).

**Spaltenerzeugung (Experiment 5).** Je Instanz (Zufalls-Seed 0 bis 9) die Schranke mit voller Dominanz gegen „nur Kosten“: gleich in den Instanzen 0, 3, 5, 8 und 9; höher mit „nur Kosten“ in 1 (1,161 %), 2 (0,755 %), 4 (0,077 %), 6 (1,691 %) und 7 (8,476 %). Die Prozentwerte sind der Abstand der Schranke von „nur Kosten“ zur Schranke der vollen Regel, bezogen auf die Schranke der vollen Regel; das Mittel von 1,216 % läuft über alle 10 Instanzen, auch über die 5 mit Unterschied 0 (Summe der Prozentwerte 12,16, geteilt durch 10).

**Messung dieser README, nicht im Test:** In dieser Python-Fassung war die Rechnung mit Dominanz bei 20 Kunden und Breite 200 langsamer als ohne (Summe über die 10 Instanzen: 26,4 s mit gegen 4,2 s ohne Dominanz, nicht je Instanz; auf einem durch
parallele Läufe ausgelasteten Rechner; eine einzelne Messung), obwohl die volle Dominanz dort weniger Labels erzeugt (Faktor 3,49 im Median, siehe Wachstumstabelle). Sekunden hängen vom Rechner ab und stehen in keinem Test; die Demo stellt keine allgemeine Aussage über Rechenzeit auf.

## Ehrliche Grenzen

- Eigene Instanzen im Stil der Solomon-Instanzen, **nicht die Originalinstanzen**; die Regel-Tabelle hat nur 7 Kunden, die Wachstumsreihen höchstens 20, die Spaltenerzeugung 10 Kunden. Bei 30 Kunden ist nur der Anteil gestrichener Labels gemessen.
- „Kosten + Gedächtnis“ verfehlt den besten Weg bei 7 Kunden in 0 von 180 Fällen; das ist eine Beobachtung an diesen Instanzen (Fahrzeit gleich Entfernung), kein Satz: In der Gegenprobe (3 000 Instanzen mit 6 Kunden und zufälligen, nicht symmetrischen Fahrzeiten, Dreiecksungleichung nicht erzwungen) gibt es 1 Fall. Die Gegenprobe ändert gegenüber der Regel-Tabelle zugleich den Instanztyp (zufällige statt euklidischer Fahrzeiten, andere Lage der Fenster), die Kundenzahl (6 statt 7) und die Fensterbreite (immer genau 30 statt höchstens 30, 80 oder 200); welche dieser Änderungen den Fall erklärt und ob die Dreiecksungleichung die Ursache ist, ist nicht untersucht.
- Warten ist erlaubt und kostenlos; ohne Warten gilt „früher ankommen ist nie schlechter“ nicht (nicht gemessen). Weitere Grenzen (Fahrerzeit und so weiter) brauchen weitere Bedingungen (nicht gemessen).
- Die Dualpreise der Experimente 3 und 4 sind zufällig gezogen, nicht die einer echten Spaltenerzeugung; Ausnahme ist die 30-Kunden-Reihe in Experiment 4 (je 6 Instanzen), die wie Experiment 5 die ganze Spaltenerzeugung rechnet. Deren Zahlen hängen vom Weg des Master-Problems ab und können mit einer anderen Version der Bibliothek leicht abweichen.
- Gemessen sind genau die Regeln dieser Demo, nicht andere Dominanzregeln aus der Literatur.
- Literatur (Prüfstand: Titel, Zeitschrift und Jahr per Suchtreffer geprüft, Volltexte nicht gelesen, keine Zahl daraus übernommen): Desrochers, Soumis (1988), INFOR; Feillet, Dejax, Gendreau, Gueguen (2004), Networks; Irnich, Desaulniers (2005), Kapitel 2 in *Column Generation*.

Annahmen, Grenzen und bekannte Probleme, wie sie auch in der App stehen (ein Test prüft, dass beide Fassungen gleich sind):

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

## Verifikation

- **Kern:** je Einheit gegen Handrechnung am Handbeispiel (`tests/conftest.py`, `tests/test_algorithm.py`): Dominanz je Bedingung, Fortsetzung, Gedächtnis, Zählungen und Ereignisse je Regel; unabhängiger Routenprüfer; Zweig-Test (jede Bedingung ändert auf mindestens einer Instanz das Ergebnis).
- **Orakel** (`tests/test_oracle_dominanz_labels.py`): Tiefensuche über alle Routen ohne Labels (selbst am Handbeispiel und an einer Permutationsaufzählung geprüft) gegen die volle Regel und „keine Dominanz“ in 180 Fällen; Trennschärfe: „nur Kosten“ weicht ab; Zahl der Labels ohne Dominanz gegen die Zahl der zulässigen Teilrouten; Invariante: lebende Labels am selben Kunden dominieren einander nicht.
- **Eigenschaften** (`tests/test_eigenschaften_dominanz_labels.py`): Umnummerieren der Kunden, Skalieren aller Längen und Zeiten, mit Dominanz nie mehr Labels, gleicher bester Wert mit und ohne Dominanz, zusätzliche Option verschlechtert nie.
- **Randfälle** (`tests/test_edge_cases.py`): ein und zwei Kunden, leere Route, Gleichstand (das ältere Label bleibt), Last und Horizont genau an der Grenze, Abbruch bei zu vielen Labels.
- **Zahlen der README** (`tests/test_claims.py`): Regel-Tabelle und Gegenprobe werden neu gerechnet; die Wachstumszellen ebenfalls; die Spaltenerzeugung wird für alle 10 Instanzen neu gerechnet (Bänder statt exakter Gleichheit für „nur Kosten“); die Messreihen unter `data/` stehen mit Quelle je Zeile.
- **Verdikte** (`tests/test_verdicts.py`) und **je Schnellstart-Szenario die erwartete Verdikt-Zeile** (`tests/test_presets.py`, `tests/test_app.py`).
- **Oberfläche:** AppTest-Rauchtest (jeder Knopf, jeder Regler am Minimum und Maximum, jede Option, Eckfälle, Permalink mit ungültigen Werten), Layout (fester Kopf, Schnellstart in der Seitenleiste, Hervorhebung), Footer, Laufzeit-Importe.
- **Testzahl:** 168 Tests (`pytest --collect-only -q tests`).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Kopf, Handbeispiel, fünf Experimente, Grenzen, Formeln, Fußzeile |
| `dml_algorithm.py` | Kern: Label-Verfahren mit wählbarer Dominanzregel, Dominanz und Einzelbedingungen, Fortsetzung, Gedächtnis, Aufzählung aller Routen, Routenprüfer |
| `dml_constants.py` | Regler-Grenzen, Regelnamen, Farben, Schnellstart-Szenarien, gemeinsamer Text der Annahmen |
| `dml_evaluation.py` | Handbeispiel-Auswertung, Ereignistabelle, Verlustpaare, Größenversuch, Gegenprobe, Laden der Messreihen, Verdikte (reine Funktionen) |
| `dml_layout.py` | Fester Kopf (Stylesheet) |
| `dml_presets.py` | Permalink (Begrenzen), Schnellstart in der Seitenleiste, aktives Szenario hervorgehoben, Zufalls-Seed-Knopf |
| `dml_scenario.py` | Handbeispiel, Zufallsinstanzen im Solomon-Stil, Dualpreise, Instanzen der Gegenprobe |
| `dml_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `data/regeltabelle.json`, `data/wachstum.json`, `data/spaltenerzeugung.json` | feste Messreihen, jede Zeile mit Quelle |
| `tools/bands_bauen.py` | erzeugt `data/*.json` aus den Rohausgaben der Messungen und rechnet Mittel und Minimum des Faktors mit dem Kern der Demo nach |
| `tools/colgen_ref.py` | Spaltenerzeugung (scipy, Überdeckungs-Master) für Tests und Werkzeuge, nicht für die App |
| `requirements-dev.txt` | Laufzeit plus pytest und scipy (nur für `tools/colgen_ref.py` in den Tests) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | siehe Verifikation |

## Bewusst nicht umgesetzt

- Keine Aussage über Rechenzeit und keine Zeitmessung in der App.
- Kein Zeitfenster-Ausbau (Fenster und Warten sind hier nur eine Zahl im Label), keine zweite Grenze neben Last, keine Elementaritäts-Verfahren im Detail (nur der Befund, dass die Last-Bedingung bei Prüfung des Gedächtnisses elementar überflüssig ist, weil die Last aus dem Gedächtnis folgt, und bei k = 3 nicht).
- Keine Eimer und keine gelernten Streichregeln; keine anderen Dominanzregeln aus der Literatur.
- Keine Live-Spaltenerzeugung in der App (Experiment 5 zeigt feste Messreihen, die Tests rechnen sie neu).
- Kein PDF-Export.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Python 3.12 oder neuer (die CI läuft mit 3.12). Die in der Streamlit Cloud eingestellte Python-Version ist beim ersten Deploy einzutragen. <!-- lint-ok: dezimalpunkt -->

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und pandas.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Ressourcenwege: von der Grenze zur Verfahrenswahl](https://sebastianhanisch.net/konzepte-ressourcenwege.html).
