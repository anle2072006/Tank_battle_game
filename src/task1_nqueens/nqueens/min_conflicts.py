"""Min-Conflicts local search for N-Queens, with pluggable heuristics.

State : queens[col] = row  (one queen per column, so column conflicts never occur).
Counters row_cnt / d1_cnt / d2_cnt give the number of queens on each row and
diagonal, so the conflicts of any square are computed in O(1).

Variable-selection heuristics (which conflicted column to repair):
  "random"        classic Min-Conflicts: random conflicted column.
  "max_conflict"  column with the most conflicts (ties broken randomly).
  "oldest"        proposed: among conflicted columns, the one that has gone the
                  longest without being moved, biased by its conflict count
                  (score = conflicts * (1 + age/N)). Spreads repairs and avoids
                  repeatedly shuffling the same few queens (plateau cycling).
Initialisation:
  "random"  random row for each column.
  "greedy"  place columns one by one on the row with the fewest conflicts so far.
Value selection (all heuristics): row with minimum conflicts, ties random.
"""
import random
import time
from dataclasses import dataclass
from typing import List, Optional

from .board import QueensBoard

VAR_HEURISTICS = ("random", "max_conflict", "oldest")
INIT_MODES = ("random", "greedy")


@dataclass
class MCResult:
    n: int
    solved: bool
    steps: int
    restarts: int
    time: float
    board: QueensBoard


class MinConflictsSolver:
    def __init__(self, n: int, var_heuristic: str = "random", init: str = "random",
                 max_steps: Optional[int] = None, max_restarts: int = 20,
                 seed: Optional[int] = None):
        if var_heuristic not in VAR_HEURISTICS or init not in INIT_MODES:
            raise ValueError("unknown heuristic / init mode")
        self.n = n
        self.var_heuristic = var_heuristic
        self.init = init
        self.max_steps = max_steps if max_steps is not None else max(1000, 20 * n)
        self.max_restarts = max_restarts
        self.rng = random.Random(seed)

    # ---------- state ----------
    def _init_state(self):
        n, rng = self.n, self.rng
        self.q: List[int] = [0] * n
        self.row_cnt = [0] * n
        self.d1 = [0] * (2 * n - 1)   # index r - c + n - 1
        self.d2 = [0] * (2 * n - 1)   # index r + c
        self.last_moved = [0] * n
        if self.init == "random":
            for c in range(n):
                self._place(c, rng.randrange(n))
        else:
            cols = list(range(n))
            rng.shuffle(cols)
            for c in cols:
                self._place(c, self._best_row(c, placed=False))

    def _place(self, c: int, r: int):
        self.q[c] = r
        self.row_cnt[r] += 1
        self.d1[r - c + self.n - 1] += 1
        self.d2[r + c] += 1

    def _remove(self, c: int):
        r = self.q[c]
        self.row_cnt[r] -= 1
        self.d1[r - c + self.n - 1] -= 1
        self.d2[r + c] -= 1

    def _conflicts(self, c: int, r: int, placed: bool = True) -> int:
        """Queens attacking square (r, c), not counting the queen of column c itself."""
        k = self.row_cnt[r] + self.d1[r - c + self.n - 1] + self.d2[r + c]
        if placed and self.q[c] == r:
            k -= 3
        return k

    def _best_row(self, c: int, placed: bool = True) -> int:
        best, rows = None, []
        for r in range(self.n):
            k = self._conflicts(c, r, placed)
            if best is None or k < best:
                best, rows = k, [r]
            elif k == best:
                rows.append(r)
        return self.rng.choice(rows)

    # ---------- variable selection ----------
    def _conflicted(self):
        return [(c, k) for c in range(self.n)
                if (k := self._conflicts(c, self.q[c])) > 0]

    def _pick_column(self, conflicted, step: int) -> int:
        h, rng = self.var_heuristic, self.rng
        if h == "random":
            return rng.choice(conflicted)[0]
        if h == "max_conflict":
            m = max(k for _, k in conflicted)
            return rng.choice([c for c, k in conflicted if k == m])
        # "oldest"
        scores = [(k * (1 + (step - self.last_moved[c]) / self.n), c) for c, k in conflicted]
        m = max(s for s, _ in scores)
        return rng.choice([c for s, c in scores if s == m])

    # ---------- main loop ----------
    def solve(self) -> MCResult:
        t0 = time.perf_counter()
        total_steps = 0
        for restart in range(self.max_restarts + 1):
            self._init_state()
            for step in range(1, self.max_steps + 1):
                conflicted = self._conflicted()
                if not conflicted:
                    return self._result(True, total_steps, restart, t0)
                c = self._pick_column(conflicted, step)
                r = self._best_row(c)
                self._remove(c)
                self._place(c, r)
                self.last_moved[c] = step
                total_steps += 1
            if not self._conflicted():
                return self._result(True, total_steps, restart, t0)
        return self._result(False, total_steps, self.max_restarts, t0)

    def iter_steps(self):
        """Step-by-step version of solve() for visualisation.

        Yields (total_steps, restart, moved_col, num_conflicted_columns) after the
        initialisation (moved_col=None) and after every move. The current state is
        in self.q. The generator stops when solved (num_conflicted == 0) or when
        all restarts are used up.
        """
        total = 0
        for restart in range(self.max_restarts + 1):
            self._init_state()
            conflicted = self._conflicted()
            yield total, restart, None, len(conflicted)
            for step in range(1, self.max_steps + 1):
                if not conflicted:
                    return
                c = self._pick_column(conflicted, step)
                r = self._best_row(c)
                self._remove(c)
                self._place(c, r)
                self.last_moved[c] = step
                total += 1
                conflicted = self._conflicted()
                yield total, restart, c, len(conflicted)
            if not conflicted:
                return

    def _result(self, solved, steps, restarts, t0) -> MCResult:
        return MCResult(self.n, solved, steps, restarts,
                        time.perf_counter() - t0, QueensBoard(self.n, list(self.q)))
