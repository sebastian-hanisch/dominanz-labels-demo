"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import dml_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360, legend_below=True):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=-0.25) if legend_below else {})
    return lock_axes(fig)


def _manhattan_path(points, route):
    """Linienzug einer Route auf dem Gitter: erst waagerecht, dann senkrecht (der Abstand der Demo ist der Manhattan-Abstand)."""
    seq = (0,) + tuple(route) + (0,)
    xs, ys = [], []
    for a, b in zip(seq, seq[1:]):
        (x1, y1), (x2, y2) = points[a], points[b]
        xs += [x1, x2, x2]
        ys += [y1, y1, y2]
    return xs, ys


def build_hand_map(inst, best_route, found_route, found_label):
    """Die Kunden des Handbeispiels auf dem Gitter; der beste Weg (Aufzählung) und der Weg der gewählten Regel."""
    fig = go.Figure()
    if best_route:
        xs, ys = _manhattan_path(inst.points, best_route)
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_OK, width=7), opacity=0.45, name="bester Weg (Aufzählung)", hoverinfo="skip"))
    if found_route and tuple(found_route) != tuple(best_route):
        xs, ys = _manhattan_path(inst.points, found_route)
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_BAD, width=3, dash="dash"), name=f"Weg der Regel „{found_label}“", hoverinfo="skip"))
    elif found_route:
        xs, ys = _manhattan_path(inst.points, found_route)
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_LINE, width=2, dash="dot"), name=f"Weg der Regel „{found_label}“ (derselbe)", hoverinfo="skip"))
    cust = list(range(1, inst.n + 1))
    hover = [f"Kunde {i}: Last {inst.demand[i]}, Fenster [{inst.ready[i]}, {inst.due[i]}]" for i in cust]
    fig.add_trace(go.Scatter(x=[inst.points[i][0] for i in cust], y=[inst.points[i][1] for i in cust], mode="markers+text", text=[str(i) for i in cust],
                             textposition="top center", marker=dict(size=16, color=C.COLOR_LINE), textfont=dict(size=13), name="Kunden", hovertext=hover,
                             hovertemplate="%{hovertext}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[inst.points[0][0]], y=[inst.points[0][1]], mode="markers+text", text=["Depot"], textposition="bottom center",
                             marker=dict(size=16, color="black", symbol="square"), name="Depot", hovertemplate="Depot<extra></extra>"))
    fig.update_xaxes(range=[-0.5, 9.5], title_text="Gitter, waagerecht", dtick=1)
    fig.update_yaxes(range=[1.5, 11.5], title_text="Gitter, senkrecht", dtick=1)
    return _base(fig, height=380)


def build_rule_chart(rows_el, rows_ng, cases):
    """Fälle, in denen die Regel den besten Weg verfehlt (elementar) bzw. vom Ergebnis ohne Dominanz abweicht (Gedächtnis k = 3), je Regel."""
    names = [C.RULE_LABELS[r["regel"]].replace(" (Kosten, Zeit, Last, Gedächtnis)", "") for r in rows_el]
    fig = go.Figure()
    fig.add_trace(go.Bar(y=names, x=[r["verfehlt"] for r in rows_el], orientation="h", name="elementar (jeder Kunde höchstens einmal)", marker_color=C.COLOR_OK,
                         hovertemplate="%{y}: %{x} von " + str(cases) + "<extra></extra>"))
    fig.add_trace(go.Bar(y=names, x=[r["weicht_ab"] for r in rows_ng], orientation="h", name="Gedächtnis k = 3 (nicht elementar)", marker_color=C.COLOR_LINE2,
                         hovertemplate="%{y}: %{x} von " + str(cases) + "<extra></extra>"))
    fig.update_xaxes(title_text=f"Fälle mit verfehltem Weg (von {cases})", range=[0, 80])
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(barmode="group")
    return _base(fig, height=470)


def build_size_chart(stats, n):
    """Erzeugte Labels je Kunde: am Ende lebend und gestrichen (gestapelt)."""
    labels = [f"K{i}" for i in range(1, n + 1)]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=list(stats.alive_per_customer), name="lebt am Ende", marker_color=C.COLOR_OK,
                         hovertemplate="%{x}: %{y} lebende Labels<extra></extra>"))
    fig.add_trace(go.Bar(x=labels, y=list(stats.dominated_per_customer), name="gestrichen", marker_color=C.COLOR_OTHER,
                         hovertemplate="%{x}: %{y} gestrichene Labels<extra></extra>"))
    fig.update_layout(barmode="stack")
    fig.update_xaxes(title_text="Kunde, bei dem das Label endet")
    fig.update_yaxes(title_text="erzeugte Labels")
    return _base(fig)


def build_factor_chart(rows, width, live_n=None, live_factor=None):
    """Faktor (Labels ohne / mit voller Dominanz) über die Kundenzahl für eine Fensterbreite: Minimum bis Maximum, Median, Mittel (10 Instanzen je Punkt);
    optional der Wert der Live-Rechnung."""
    rows = [r for r in rows if r["breite"] == width]
    xs = [r["n"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs + xs[::-1], y=[r["faktor_max"] for r in rows] + [r["faktor_min"] for r in rows][::-1], fill="toself",
                             fillcolor="rgba(76,120,168,0.18)", line=dict(width=0), hoverinfo="skip", name="Minimum bis Maximum"))
    fig.add_trace(go.Scatter(x=xs, y=[r["faktor_median"] for r in rows], mode="lines+markers", line=dict(color=C.COLOR_LINE, width=3), name="Median",
                             hovertemplate="n = %{x}: Median %{y:.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[r["faktor_mittel"] for r in rows], mode="lines", line=dict(color=C.COLOR_LINE2, width=2, dash="dash"), name="Mittel",
                             hovertemplate="n = %{x}: Mittel %{y:.2f}<extra></extra>"))
    top = max(9.0, max(r["faktor_max"] for r in rows) + 0.5)
    if live_factor is not None:
        top = max(top, live_factor + 0.5)
        fig.add_trace(go.Scatter(x=[live_n], y=[live_factor], mode="markers", marker=dict(size=14, color=C.COLOR_BAD, symbol="star"), name="Ihre Instanz",
                                 hovertemplate="n = %{x}: Faktor %{y:.2f}<extra></extra>"))
    fig.update_xaxes(title_text="Kunden n", range=[6.5, 20.5], dtick=1)
    fig.update_yaxes(title_text="Labels ohne Dominanz / mit voller Dominanz", range=[0, top])
    return _base(fig)


def build_colgen_chart(rows):
    """Unterschied der Schranke (nur Kosten gegen volle Regel) je Instanz in Prozent."""
    fig = go.Figure(go.Bar(x=[f"Instanz {r['seed']}" for r in rows], y=[max(r["unterschied_prozent"], 0.0) for r in rows], marker_color=C.COLOR_BAD,
                           hovertemplate="%{x}: %{y:.3f} %<extra></extra>"))
    fig.update_xaxes(title_text="Instanz (Zufalls-Seed)")
    fig.update_yaxes(title_text="Schranke „nur Kosten“ höher als volle Regel (%)", range=[0, 10])
    return _base(fig)
