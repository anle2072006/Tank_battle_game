"""Board representation and solution checking for the N-Queens problem."""
from typing import List, Optional


class QueensBoard:
    """N x N board. A solution is stored as `queens[col] = row` (one queen per column)."""

    def __init__(self, n: int, queens: Optional[List[int]] = None):
        if n < 1:
            raise ValueError("N must be >= 1")
        self.n = n
        self.queens = queens if queens is not None else [-1] * n

    # ---------- checking ----------
    def count_conflicting_pairs(self) -> int:
        """Number of pairs of queens attacking each other (0 means solved)."""
        q, bad = self.queens, 0
        for i in range(self.n):
            for j in range(i + 1, self.n):
                if q[i] == q[j] or abs(q[i] - q[j]) == j - i:
                    bad += 1
        return bad

    def is_valid(self) -> bool:
        return (len(self.queens) == self.n
                and all(0 <= r < self.n for r in self.queens)
                and self.count_conflicting_pairs() == 0)

    # ---------- display ----------
    def __str__(self) -> str:
        rows = []
        for r in range(self.n):
            rows.append(" ".join("Q" if self.queens[c] == r else "." for c in range(self.n)))
        return "\n".join(rows)
