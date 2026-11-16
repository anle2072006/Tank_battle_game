"""CLI demo for Task 1 (N-Queens).

Examples:
  python main.py --n 8 --method sat
  python main.py --n 8 --method mc --var-heuristic max_conflict --init greedy
  python main.py --n 100 --method mc --var-heuristic oldest --init greedy --no-print
"""
import argparse

from nqueens import SATQueensSolver, MinConflictsSolver
from nqueens.min_conflicts import VAR_HEURISTICS, INIT_MODES


def main():
    ap = argparse.ArgumentParser(description="N-Queens: SAT (Glucose3) and Min-Conflicts")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--method", choices=["sat", "mc"], default="sat")
    ap.add_argument("--var-heuristic", choices=VAR_HEURISTICS, default="random")
    ap.add_argument("--init", choices=INIT_MODES, default="random")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--timeout", type=float, default=None, help="SAT timeout (s)")
    ap.add_argument("--no-print", action="store_true", help="do not print the board")
    a = ap.parse_args()

    if a.method == "sat":
        res = SATQueensSolver(a.n, a.timeout).solve()
        print(f"[SAT/Glucose3] N={a.n} vars={res.num_vars} clauses={res.num_clauses} "
              f"encode={res.encode_time:.4f}s solve={res.solve_time:.4f}s sat={res.satisfiable}")
        board = res.board
    else:
        res = MinConflictsSolver(a.n, a.var_heuristic, a.init, seed=a.seed).solve()
        print(f"[Min-Conflicts/{a.var_heuristic}/{a.init}] N={a.n} solved={res.solved} "
              f"steps={res.steps} restarts={res.restarts} time={res.time:.4f}s")
        board = res.board

    if board is not None:
        print("valid:", board.is_valid())
        if not a.no_print and a.n <= 40:
            print(board)


if __name__ == "__main__":
    main()
