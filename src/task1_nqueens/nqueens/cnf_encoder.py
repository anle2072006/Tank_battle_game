"""Propositional-logic (CNF) encoding of N-Queens.

Variable x(r, c) is True  <=>  there is a queen on square (row r, column c).
DIMACS variable id: r * N + c + 1   (ids start at 1).

Constraints (all converted to CNF):
  1. Each row has at least one queen:        (x(r,0) v x(r,1) v ... v x(r,N-1))
  2. Each column has at least one queen:     (x(0,c) v ... v x(N-1,c))
  3. At most one queen per row/column/diagonal (pairwise):
         for every two distinct squares a, b on the same line:  (~a v ~b)
     This is the CNF form of  a -> ~b  (i.e. ~(a ^ b)).
Together: exactly N queens, no two attack each other.
"""
from itertools import combinations
from typing import List

Clause = List[int]


class CNFEncoder:
    def __init__(self, n: int):
        self.n = n

    def var(self, r: int, c: int) -> int:
        return r * self.n + c + 1

    def decode(self, row_col_of_var: int):
        v = row_col_of_var - 1
        return divmod(v, self.n)  # (row, col)

    @property
    def num_vars(self) -> int:
        return self.n * self.n

    # ---------- line generators ----------
    def _rows(self):
        return [[self.var(r, c) for c in range(self.n)] for r in range(self.n)]

    def _cols(self):
        return [[self.var(r, c) for r in range(self.n)] for c in range(self.n)]

    def _diagonals(self):
        n, lines = self.n, []
        for d in range(-(n - 1), n):                       # r - c = d
            lines.append([self.var(r, r - d) for r in range(n) if 0 <= r - d < n])
        for s in range(0, 2 * n - 1):                      # r + c = s
            lines.append([self.var(r, s - r) for r in range(n) if 0 <= s - r < n])
        return lines

    # ---------- clause generation ----------
    def at_least_one_clauses(self) -> List[Clause]:
        return [list(line) for line in self._rows() + self._cols()]

    def at_most_one_clauses(self) -> List[Clause]:
        clauses = []
        for line in self._rows() + self._cols() + self._diagonals():
            clauses.extend([-a, -b] for a, b in combinations(line, 2))
        return clauses

    def encode(self) -> List[Clause]:
        return self.at_least_one_clauses() + self.at_most_one_clauses()

    # ---------- closed-form clause count (for the report) ----------
    def expected_clause_count(self) -> int:
        n = self.n
        c2 = lambda k: k * (k - 1) // 2
        alo = 2 * n
        amo_rc = 2 * n * c2(n)
        amo_diag = 2 * (2 * sum(c2(k) for k in range(1, n)) + c2(n))
        return alo + amo_rc + amo_diag
