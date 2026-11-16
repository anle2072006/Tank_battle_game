"""PyGame GUI for Task 1 (N-Queens).

Run:  python gui.py
Shows the board, animates Min-Conflicts step by step (moved column is ringed in
yellow, attacked queens in red) and solves with the SAT/Glucose3 encoding on demand.
"""
import time
import pygame

from nqueens import SATQueensSolver, MinConflictsSolver
from nqueens.min_conflicts import VAR_HEURISTICS, INIT_MODES

W, H = 1060, 720
BOARD_PX, MARGIN = 680, 20
PANEL_X = BOARD_PX + 2 * MARGIN
PANEL_W = W - PANEL_X - MARGIN
N_MIN, N_MAX = 4, 64
SPEEDS = [2, 5, 10, 30, 60, 200, 1000]          # Min-Conflicts steps per second

BG = (24, 26, 33)
LIGHT, DARK = (238, 238, 210), (118, 150, 86)
QUEEN_OK, QUEEN_BAD, RING = (35, 80, 170), (205, 45, 45), (255, 210, 0)
BTN, BTN_HOVER, BTN_ON, TEXT = (58, 63, 80), (78, 85, 108), (60, 130, 90), (230, 232, 240)


class Button:
    def __init__(self, rect, label, action):
        self.rect, self.label, self.action = pygame.Rect(rect), label, action

    def draw(self, surf, font, mouse, active=False):
        color = BTN_ON if active else (BTN_HOVER if self.rect.collidepoint(mouse) else BTN)
        pygame.draw.rect(surf, color, self.rect, border_radius=6)
        txt = font.render(self.label() if callable(self.label) else self.label, True, TEXT)
        surf.blit(txt, txt.get_rect(center=self.rect.center))


class QueensApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("N-Queens - SAT & Min-Conflicts")
        self.font = pygame.font.Font(None, 26)
        self.big = pygame.font.Font(None, 38)
        self.small = pygame.font.Font(None, 22)
        self.n, self.speed_i = 8, 2
        self.var_i, self.init_i = 0, 1
        self.running = False
        self._reset_state()
        self._make_buttons()

    # ---------- state ----------
    def _reset_state(self):
        self.queens = [None] * self.n          # queens[col] = row
        self.mc, self.it = None, None
        self.moved = None
        self.running = False
        self.info = ["Choose a method:", "Run Min-Conflicts or Solve with SAT."]
        self.bad_cols, self.bad_pairs = set(), []
        self.acc = 0.0

    def _set_queens(self, q):
        self.queens = list(q)
        self.bad_cols, self.bad_pairs = set(), []
        if None in self.queens:
            return
        n = len(q)
        for i in range(n):
            for j in range(i + 1, n):
                if q[i] == q[j] or abs(q[i] - q[j]) == j - i:
                    self.bad_cols.update((i, j))
                    self.bad_pairs.append((i, j))

    # ---------- actions ----------
    def change_n(self, d):
        self.n = max(N_MIN, min(N_MAX, self.n + d))
        self._reset_state()

    def cycle_var(self):
        self.var_i = (self.var_i + 1) % len(VAR_HEURISTICS)
        self._reset_state()

    def cycle_init(self):
        self.init_i = (self.init_i + 1) % len(INIT_MODES)
        self._reset_state()

    def change_speed(self, d):
        self.speed_i = max(0, min(len(SPEEDS) - 1, self.speed_i + d))

    def reset(self):
        self._reset_state()

    def _start_mc(self):
        self.mc = MinConflictsSolver(self.n, VAR_HEURISTICS[self.var_i], INIT_MODES[self.init_i])
        self.it = self.mc.iter_steps()
        self.t0 = time.perf_counter()
        self.last = None

    def _advance(self):
        """One Min-Conflicts step. Returns False when finished."""
        if self.it is None:
            self._start_mc()
        try:
            step, restart, col, nconf = next(self.it)
        except StopIteration:
            self.running = False
            self.it = None
            return False
        self.last = (step, restart, nconf)
        self.moved = col
        self._set_queens(self.mc.q)
        solved = nconf == 0
        elapsed = time.perf_counter() - self.t0
        self.info = [f"Min-Conflicts ({VAR_HEURISTICS[self.var_i]}, init {INIT_MODES[self.init_i]})",
                     f"step: {step}   restarts: {restart}",
                     f"conflicted queens: {nconf}",
                     "SOLVED" if solved else "searching...",
                     f"elapsed: {elapsed:.2f}s"]
        if solved:
            self.running, self.it, self.moved = False, None, None
        return not solved

    def toggle_run(self):
        self.running = not self.running

    def step_once(self):
        self.running = False
        self._advance()

    def solve_sat(self):
        self.running, self.it, self.moved = False, None, None
        res = SATQueensSolver(self.n, timeout=20).solve()
        if res.satisfiable:
            self._set_queens(res.board.queens)
            self.info = ["SAT / Glucose3",
                         f"variables: {res.num_vars}",
                         f"clauses: {res.num_clauses}",
                         f"encode: {res.encode_time:.4f}s",
                         f"solve: {res.solve_time:.4f}s",
                         f"valid: {res.board.is_valid()}"]
        else:
            self.info = ["SAT / Glucose3",
                         "UNSAT" if res.satisfiable is False else "timeout",
                         f"clauses: {res.num_clauses}"]

    # ---------- UI ----------
    def _make_buttons(self):
        x, w = PANEL_X, PANEL_W
        half = (w - 10) // 2
        self.buttons = [
            Button((x, 70, half, 38), "N  -", lambda: self.change_n(-1)),
            Button((x + half + 10, 70, half, 38), "N  +", lambda: self.change_n(1)),
            Button((x, 120, w, 38), lambda: f"Variable: {VAR_HEURISTICS[self.var_i]}", self.cycle_var),
            Button((x, 168, w, 38), lambda: f"Init: {INIT_MODES[self.init_i]}", self.cycle_init),
            Button((x, 216, half, 38), "Slower", lambda: self.change_speed(-1)),
            Button((x + half + 10, 216, half, 38), "Faster", lambda: self.change_speed(1)),
            Button((x, 290, w, 42), lambda: "Pause" if self.running else "Run Min-Conflicts", self.toggle_run),
            Button((x, 340, w, 42), "Step", self.step_once),
            Button((x, 390, w, 42), "Solve with SAT", self.solve_sat),
            Button((x, 440, w, 42), "Reset", self.reset),
        ]

    def click(self, pos):
        for b in self.buttons:
            if b.rect.collidepoint(pos):
                b.action()
                return

    def update(self, dt):
        if not self.running:
            return
        self.acc += dt * SPEEDS[self.speed_i]
        guard = 0
        while self.acc >= 1 and self.running and guard < 2000:
            self.acc -= 1
            guard += 1
            self._advance()

    def draw(self):
        s, n = self.screen, self.n
        s.fill(BG)
        cell = BOARD_PX // n
        ox = oy = MARGIN
        for r in range(n):
            for c in range(n):
                pygame.draw.rect(s, LIGHT if (r + c) % 2 == 0 else DARK,
                                 (ox + c * cell, oy + r * cell, cell, cell))
        center = lambda c, r: (ox + c * cell + cell // 2, oy + r * cell + cell // 2)
        if n <= 30:
            for i, j in self.bad_pairs:
                pygame.draw.line(s, (220, 60, 60), center(i, self.queens[i]),
                                 center(j, self.queens[j]), 2)
        rad = max(3, int(cell * 0.38))
        for c, r in enumerate(self.queens):
            if r is None:
                continue
            pos = center(c, r)
            if c == self.moved:
                pygame.draw.circle(s, RING, pos, rad + max(2, cell // 12))
            pygame.draw.circle(s, QUEEN_BAD if c in self.bad_cols else QUEEN_OK, pos, rad)
            if cell >= 22:
                t = pygame.font.Font(None, int(cell * 0.7)).render("Q", True, (255, 255, 255))
                s.blit(t, t.get_rect(center=pos))

        mouse = pygame.mouse.get_pos()
        s.blit(self.big.render("N-Queens", True, TEXT), (PANEL_X, 20))
        s.blit(self.font.render(f"N = {n}", True, TEXT), (PANEL_X + PANEL_W - 80, 28))
        for b in self.buttons:
            b.draw(s, self.font, mouse, active=(self.running and "Pause" in str(b.label() if callable(b.label) else b.label)))
        s.blit(self.small.render(f"Speed: {SPEEDS[self.speed_i]} steps/s", True, TEXT), (PANEL_X, 262))
        y = 505
        for line in self.info:
            col = (120, 230, 140) if line == "SOLVED" else TEXT
            s.blit(self.small.render(line, True, col), (PANEL_X, y))
            y += 24
        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()
        while True:
            dt = clock.tick(60) / 1000
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    return
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    self.click(e.pos)
                if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                    self.toggle_run()
            self.update(dt)
            self.draw()


if __name__ == "__main__":
    QueensApp().run()
