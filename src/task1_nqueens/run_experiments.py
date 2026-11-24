"""Experiments for Task 1. Writes CSV files + plots into ./results.

  python run_experiments.py            # full run
  python run_experiments.py --quick    # small run
"""
import argparse
import csv
import os
import statistics as st

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from nqueens import SATQueensSolver, MinConflictsSolver, CNFEncoder

OUT = "results"


def exp_sat(ns, timeout):
    rows = []
    for n in ns:
        enc = CNFEncoder(n)
        r = SATQueensSolver(n, timeout).solve()
        assert r.num_clauses == enc.expected_clause_count()
        ok = r.board.is_valid() if r.board else None
        rows.append(dict(N=n, variables=r.num_vars, clauses=r.num_clauses,
                         encode_s=round(r.encode_time, 5), solve_s=round(r.solve_time, 5),
                         total_s=round(r.total_time, 5), satisfiable=r.satisfiable, valid=ok))
        print("SAT", rows[-1])
    return rows


def exp_mc(ns, configs, runs, seed0=0):
    rows = []
    for n in ns:
        for var_h, init in configs:
            steps, times, solved = [], [], 0
            for i in range(runs):
                r = MinConflictsSolver(n, var_h, init, seed=seed0 + i).solve()
                solved += r.solved and r.board.is_valid()
                steps.append(r.steps)
                times.append(r.time)
            rows.append(dict(N=n, var_heuristic=var_h, init=init, runs=runs,
                             success_rate=solved / runs,
                             mean_steps=round(st.mean(steps), 1),
                             median_steps=st.median(steps),
                             mean_time_s=round(st.mean(times), 5)))
            print("MC", rows[-1])
    return rows


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


def plot_sat(rows):
    ns = [r["N"] for r in rows]
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
    ax[0].plot(ns, [r["clauses"] for r in rows], "o-")
    ax[0].set(xlabel="N", ylabel="#CNF clauses", title="CNF size")
    ax[1].plot(ns, [r["encode_s"] for r in rows], "s-", label="encode")
    ax[1].plot(ns, [r["solve_s"] for r in rows], "o-", label="Glucose3 solve")
    ax[1].set(xlabel="N", ylabel="seconds", title="SAT running time")
    ax[1].legend()
    fig.tight_layout()
    fig.savefig(f"{OUT}/sat_scaling.png", dpi=150)


def plot_mc(rows):
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
    labels = sorted({(r["var_heuristic"], r["init"]) for r in rows})
    for lab in labels:
        pts = [r for r in rows if (r["var_heuristic"], r["init"]) == lab]
        ax[0].plot([p["N"] for p in pts], [p["mean_steps"] for p in pts], "o-", label=f"{lab[0]}+{lab[1]}")
        ax[1].plot([p["N"] for p in pts], [p["mean_time_s"] for p in pts], "o-", label=f"{lab[0]}+{lab[1]}")
    for a, y in zip(ax, ["mean #steps", "mean time (s)"]):
        a.set(xlabel="N", ylabel=y, xscale="log", yscale="log")
    ax[0].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(f"{OUT}/mc_heuristics.png", dpi=150)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    
    sat_ns = [4, 5, 6, 8, 10, 12, 16, 20] if a.quick else [4, 5, 6, 8, 10, 12, 16, 20, 24, 28, 32, 40, 50]
    mc_ns = [8, 16, 32, 64] if a.quick else [8, 16, 32, 64, 128, 256, 512, 1000]
    runs = 5 if a.quick else 20
    configs = [("random", "random"), ("max_conflict", "random"), ("oldest", "random"),
               ("random", "greedy"), ("max_conflict", "greedy"), ("oldest", "greedy")]

    sat_rows = exp_sat(sat_ns, timeout=120)
    write_csv(f"{OUT}/sat_results.csv", sat_rows)
    plot_sat(sat_rows)

    mc_rows = exp_mc(mc_ns, configs, runs)
    write_csv(f"{OUT}/mc_results.csv", mc_rows)
    plot_mc(mc_rows)


if __name__ == "__main__":
    main()
