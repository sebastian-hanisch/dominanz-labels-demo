"""Spaltenerzeugung (Überdeckungs-Master) für die Nachrechnung von Teil C: nur für Tests und Werkzeuge, nicht für die App (braucht scipy).

Master: Kosten der Routen minimieren, jeder Kunde mindestens einmal überdeckt (LP, HiGHS). Die Dualpreise des Masters gehen als Kundenpreise
in das Label-Verfahren der Demo (`dml_algorithm.price`); neue Routen mit negativen reduzierten Kosten werden als Spalten ergänzt, bis keine
neue mehr kommt. Das Ergebnis ist die Schranke des Masters; sie ist nur eine gültige Untergrenze, wenn das Preisproblem den besten Weg findet."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import dml_algorithm as A  # noqa: E402


def route_cost(inst, route) -> float:
    seq = (0,) + tuple(route) + (0,)
    return sum(inst.d[a][b] for a, b in zip(seq, seq[1:]))


def colgen(inst, k: int, rule, max_iter: int = 400) -> dict:
    """Schranke, Iterationen, Spalten, erzeugte und gestrichene Labels der Spaltenerzeugung mit der gegebenen Dominanzregel."""
    from scipy.optimize import linprog

    n = inst.n
    cols = [(i,) for i in range(1, n + 1)]
    costs = [route_cost(inst, r) for r in cols]
    generated = dominated = 0
    bound = None
    iterations = 0
    while iterations < max_iter:
        iterations += 1
        matrix = np.zeros((n, len(cols)))
        for c, route in enumerate(cols):
            for i in route:
                matrix[i - 1, c] += 1
        res = linprog(costs, A_ub=-matrix, b_ub=-np.ones(n), bounds=(0, None), method="highs")
        pi = (0.0,) + tuple(-res.ineqlin.marginals)
        bound = res.fun
        result = A.price(inst, pi, k, rule)
        generated += result.generated
        dominated += result.dominated
        known = set(cols)
        fresh = [route for _, route in A.routes_of(result, 15) if route not in known]
        if not fresh:
            break
        for route in fresh:
            cols.append(route)
            costs.append(route_cost(inst, route))
    return {"bound": bound, "iterations": iterations, "columns": len(cols), "generated": generated, "dominated": dominated}
