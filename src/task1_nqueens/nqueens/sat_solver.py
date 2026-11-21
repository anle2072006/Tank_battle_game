"""Solve N-Queens with the Glucose3 SAT solver (PySAT)."""
import time
import threading
from dataclasses import dataclass
from typing import Optional

from pysat.solvers import Glucose3

from .board import QueensBoard
from .cnf_encoder import CNFEncoder


@dataclass
class SATResult:
    n: int
    satisfiable: Optional[bool]      # None = timeout
    num_vars: int
    num_clauses: int
    encode_time: float
    solve_time: float
    board: Optional[QueensBoard]

    @property
    def total_time(self) -> float:
        return self.encode_time + self.solve_time


class SATQueensSolver:
    def __init__(self, n: int, timeout: Optional[float] = None):
        self.n = n
        self.timeout = timeout
        self.encoder = CNFEncoder(n)

    def solve(self) -> SATResult:
        t0 = time.perf_counter()
        clauses = self.encoder.encode()
        t1 = time.perf_counter()

        with Glucose3(bootstrap_with=clauses) as solver:
            timer = None
            if self.timeout:
                timer = threading.Timer(self.timeout, lambda: solver.interrupt())
                timer.start()
            sat = solver.solve_limited(expect_interrupt=bool(self.timeout))
            if timer:
                timer.cancel()
            model = solver.get_model() if sat else None
        t2 = time.perf_counter()

        board = None
        if sat:
            board = QueensBoard(self.n)
            for lit in model:
                if lit > 0 and lit <= self.encoder.num_vars:
                    r, c = self.encoder.decode(lit)
                    board.queens[c] = r
        return SATResult(self.n, sat, self.encoder.num_vars, len(clauses),
                         t1 - t0, t2 - t1, board)
