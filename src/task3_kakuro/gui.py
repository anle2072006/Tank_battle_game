import tkinter as tk
from collections import Counter

from board import Board, WhiteCell, ClueCell
from solver import KakuroSolver, VAR_HEURISTICS, VAL_HEURISTICS
from events import EventEmitter
from puzzles import SAMPLE_5X5, SAMPLE_9X9


class KakuroGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Kakuro - CSP Visualizer")

        self.board = Board(SAMPLE_5X5)
        self.puzzle_var = tk.StringVar(value="5x5")
        self.var_heuristic = tk.StringVar(value="mrv_degree")
        self.val_heuristic = tk.StringVar(value="none")
        self.speed_var = tk.IntVar(value=10)

        self.events = []
        self.snapshots = []
        self.step_index = -1
        self.playback_values = {}
        self.playback_domains = {}
        self.playback_mode = False
        self.active_cell = None
        self.active_event = None
        self.playing = False
        self.after_id = None

        main_frame = tk.Frame(root, padx=14, pady=12)
        main_frame.pack(fill="both", expand=True)

        # Cot trai: bang Kakuro ve bang Canvas
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side="left", anchor="n", padx=(0, 16))

        tk.Label(
            left_frame, text="KAKURO CSP VISUALIZER",
            font=("Arial", 16, "bold")
        ).pack(pady=(0, 8))

        self.canvas = tk.Canvas(left_frame, bg="#1E293B", highlightthickness=1)
        self.canvas.pack()

        # Chu giai mau su kien
        legend_frame = tk.Frame(left_frame)
        legend_frame.pack(pady=(8, 0))
        for color, text in (
            ("#FEF08A", "Domain Update"),
            ("#BBF7D0", "Assign"),
            ("#FECACA", "Backtrack"),
        ):
            item = tk.Frame(legend_frame)
            item.pack(side="left", padx=6)
            tk.Label(item, bg=color, width=2, relief="solid", borderwidth=1).pack(side="left")
            tk.Label(item, text=f" {text}", font=("Arial", 9)).pack(side="left")

        # Cot phai: cau hinh, dieu khien va thong ke
        right_frame = tk.Frame(main_frame, width=280)
        right_frame.pack(side="left", fill="y", anchor="n")

        cfg_frame = tk.LabelFrame(right_frame, text="Configuration", padx=8, pady=6)
        cfg_frame.pack(fill="x", pady=(0, 8))

        row1 = tk.Frame(cfg_frame)
        row1.pack(fill="x", pady=2)
        tk.Label(row1, text="Puzzle size:", width=13, anchor="w").pack(side="left")
        tk.OptionMenu(
            row1, self.puzzle_var, "5x5", "9x9", command=self.change_puzzle
        ).pack(side="left", fill="x", expand=True)

        row2 = tk.Frame(cfg_frame)
        row2.pack(fill="x", pady=2)
        tk.Label(row2, text="Var heuristic:", width=13, anchor="w").pack(side="left")
        tk.OptionMenu(row2, self.var_heuristic, *VAR_HEURISTICS).pack(
            side="left", fill="x", expand=True
        )

        row3 = tk.Frame(cfg_frame)
        row3.pack(fill="x", pady=2)
        tk.Label(row3, text="Val heuristic:", width=13, anchor="w").pack(side="left")
        tk.OptionMenu(row3, self.val_heuristic, *VAL_HEURISTICS).pack(
            side="left", fill="x", expand=True
        )

        self.solve_button = tk.Button(
            right_frame, text="Solve", command=self.solve,
            font=("Arial", 11, "bold"), pady=4
        )
        self.solve_button.pack(fill="x", pady=(0, 8))

        ctrl_frame = tk.LabelFrame(right_frame, text="Playback", padx=8, pady=6)
        ctrl_frame.pack(fill="x", pady=(0, 8))

        btn_row = tk.Frame(ctrl_frame)
        btn_row.pack(fill="x", pady=(0, 6))
        tk.Button(btn_row, text="< Back", command=self.previous_step).pack(
            side="left", expand=True, fill="x", padx=2
        )
        self.play_button = tk.Button(btn_row, text="Play", command=self.toggle_play)
        self.play_button.pack(side="left", expand=True, fill="x", padx=2)
        tk.Button(btn_row, text="Next >", command=self.next_step).pack(
            side="left", expand=True, fill="x", padx=2
        )
        tk.Button(btn_row, text=">> Result", command=self.show_result).pack(
            side="left", expand=True, fill="x", padx=2
        )

        speed_row = tk.Frame(ctrl_frame)
        speed_row.pack(fill="x")
        tk.Label(speed_row, text="Speed (steps/s):").pack(side="left")
        tk.Scale(
            speed_row, from_=1, to=60, orient="horizontal",
            variable=self.speed_var, showvalue=True, length=140
        ).pack(side="right")

        self.step_label = tk.Label(
            ctrl_frame, text="Step 0/0", font=("Arial", 10, "bold")
        )
        self.step_label.pack(pady=(6, 0))

        detail_frame = tk.LabelFrame(right_frame, text="Step Detail", padx=8, pady=6)
        detail_frame.pack(fill="x", pady=(0, 8))
        self.event_detail = tk.Label(
            detail_frame, text="Press Solve to start",
            font=("Arial", 9), justify="left", anchor="nw",
            wraplength=250, height=5
        )
        self.event_detail.pack(fill="x")

        status_frame = tk.LabelFrame(right_frame, text="Statistics", padx=8, pady=6)
        status_frame.pack(fill="x")
        self.status = tk.Label(
            status_frame, text="Ready",
            font=("Arial", 10), justify="left", anchor="w"
        )
        self.status.pack(fill="x")

        self.draw_board()

    def _stop_autoplay(self):
        self.playing = False
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.play_button.config(text="Play")

    def change_puzzle(self, selection):
        self._stop_autoplay()
        puzzle = SAMPLE_5X5 if selection == "5x5" else SAMPLE_9X9
        self.board = Board(puzzle)
        self.events = []
        self.snapshots = []
        self.step_index = -1
        self.playback_mode = False
        self.playback_values = {}
        self.playback_domains = {}
        self.active_cell = None
        self.active_event = None

        self.step_label.config(text="Step 0/0")
        self.event_detail.config(text="Press Solve to start")
        self.status.config(text="Ready")
        self.draw_board()

    def draw_board(self):
        cell_size = 76 if self.board.rows <= 5 else 54
        w = self.board.cols * cell_size
        h = self.board.rows * cell_size
        self.canvas.config(width=w, height=h)
        self.canvas.delete("all")

        for r in range(self.board.rows):
            for c in range(self.board.cols):
                x0, y0 = c * cell_size, r * cell_size
                x1, y1 = x0 + cell_size, y0 + cell_size
                cell = self.board.grid[r][c]

                if isinstance(cell, ClueCell):
                    has_clue = cell.row_sum is not None or cell.col_sum is not None
                    bg = "#334155" if has_clue else "#1E293B"
                    self.canvas.create_rectangle(
                        x0, y0, x1, y1, fill=bg, outline="#0F172A", width=1
                    )
                    self.canvas.create_line(x0, y0, x1, y1, fill="#94A3B8", width=1)
                    clue_font = ("Arial", 10 if cell_size >= 70 else 9, "bold")
                    if cell.row_sum is not None:
                        self.canvas.create_text(
                            x0 + cell_size * 0.72, y0 + cell_size * 0.28,
                            text=str(cell.row_sum), fill="#FFFFFF", font=clue_font
                        )
                    if cell.col_sum is not None:
                        self.canvas.create_text(
                            x0 + cell_size * 0.28, y0 + cell_size * 0.72,
                            text=str(cell.col_sum), fill="#FFFFFF", font=clue_font
                        )
                elif isinstance(cell, WhiteCell):
                    pos = (r, c)
                    bg = "#FFFFFF"
                    if self.playback_mode and pos == self.active_cell:
                        if self.active_event == "ASSIGN":
                            bg = "#BBF7D0"
                        elif self.active_event == "DOMAIN_UPDATE":
                            bg = "#FEF08A"
                        elif self.active_event == "BACKTRACK":
                            bg = "#FECACA"

                    self.canvas.create_rectangle(
                        x0, y0, x1, y1, fill=bg, outline="#334155", width=1
                    )

                    if self.playback_mode:
                        value = self.playback_values.get(pos, 0)
                        domain = self.playback_domains.get(pos, set(range(1, 10)))
                    else:
                        value = cell.value
                        domain = set()

                    if value:
                        val_font = ("Arial", 18 if cell_size >= 70 else 15, "bold")
                        self.canvas.create_text(
                            (x0 + x1) / 2, (y0 + y1) / 2,
                            text=str(value), fill="#0F172A", font=val_font
                        )
                    elif self.playback_mode:
                        dom_font = ("Arial", 9 if cell_size >= 70 else 8)
                        sub = cell_size / 3.0
                        for d in sorted(domain):
                            dr, dc = divmod(d - 1, 3)
                            self.canvas.create_text(
                                x0 + (dc + 0.5) * sub,
                                y0 + (dr + 0.5) * sub,
                                text=str(d), fill="#64748B", font=dom_font
                            )

    def on_event(self, event_type, data):
        self.events.append((event_type, data.copy()))
        values = {
            (cell.row, cell.col): cell.value
            for cell in self.board.white_cells
        }
        domains = {
            (cell.row, cell.col): cell.domain.copy()
            for cell in self.board.white_cells
        }
        self.snapshots.append({
            "event": event_type,
            "data": data.copy(),
            "values": values,
            "domains": domains,
        })

    def solve(self):
        self._stop_autoplay()
        puzzle = SAMPLE_5X5 if self.puzzle_var.get() == "5x5" else SAMPLE_9X9

        self.board = Board(puzzle)
        self.events = []
        self.snapshots = []
        self.playback_mode = False
        self.active_cell = None
        self.active_event = None
        self.status.config(text="Solving...")
        self.root.update_idletasks()

        bus = EventEmitter()
        bus.subscribe(self.on_event)
        try:
            solver = KakuroSolver(
                self.board,
                var_heuristic=self.var_heuristic.get(),
                val_heuristic=self.val_heuristic.get(),
                event_bus=bus,
                max_assignments=10000,
            )
            success = solver.solve()
        finally:
            bus.unsubscribe(self.on_event)

        self.step_index = -1
        self.playback_mode = True
        self.playback_values = {(c.row, c.col): 0 for c in self.board.white_cells}
        self.playback_domains = {
            (c.row, c.col): set(range(1, 10)) for c in self.board.white_cells
        }

        self.step_label.config(text=f"Step 0/{len(self.snapshots)}")
        self.event_detail.config(text="Press Play or Next to replay solver events")
        self.draw_board()

        counts = Counter(event_type for event_type, _ in self.events)
        stats = solver.get_stats()
        if success:
            self.status.config(
                text=(
                    f"Solved! ({stats['execution_time']:.4f}s)\n"
                    f"Assignments: {stats['assignments']} | Backtracks: {stats['backtracks']}\n"
                    f"Domain updates: {stats['domain_updates']}"
                )
            )
        elif stats["hit_limit"]:
            self.status.config(
                text=(
                    f"Hit assignment limit (10000)\n"
                    f"Try MRV or MRV+Degree for faster search."
                )
            )
        else:
            self.status.config(text="No solution found")
        print("Events:", dict(counts))

    def toggle_play(self):
        if not self.snapshots:
            self.status.config(text="Please press Solve first!")
            return
        if self.playing:
            self._stop_autoplay()
            return
        if self.step_index >= len(self.snapshots) - 1:
            self.step_index = -1
        self.playing = True
        self.play_button.config(text="Pause")
        self._schedule_next()

    def _schedule_next(self):
        if not self.playing:
            return
        if self.step_index < len(self.snapshots) - 1:
            self.step_index += 1
            self.show_step()
            delay_ms = max(15, int(1000 / self.speed_var.get()))
            self.after_id = self.root.after(delay_ms, self._schedule_next)
        else:
            self._stop_autoplay()

    def show_result(self):
        self._stop_autoplay()
        if not self.snapshots:
            self.status.config(text="Please press Solve first!")
            return
        self.step_index = len(self.snapshots) - 1
        self.show_step()

    def next_step(self):
        self._stop_autoplay()
        if self.step_index < len(self.snapshots) - 1:
            self.step_index += 1
            self.show_step()

    def previous_step(self):
        self._stop_autoplay()
        if self.step_index > 0:
            self.step_index -= 1
            self.show_step()

    def show_step(self):
        snapshot = self.snapshots[self.step_index]
        self.playback_values = snapshot["values"].copy()
        self.playback_domains = {
            pos: domain.copy() for pos, domain in snapshot["domains"].items()
        }
        event_type = snapshot["event"]
        data = snapshot["data"]
        self.active_cell = data.get("cell")
        self.active_event = event_type

        self.step_label.config(
            text=f"Step {self.step_index + 1}/{len(self.snapshots)} - {event_type}"
        )

        if event_type == "DOMAIN_UPDATE":
            old_domain = set(data["old"])
            new_domain = set(data["new"])
            removed = sorted(old_domain - new_domain)
            message = (
                f"Cell: {data['cell']} (Run {data['run'][0]}={data['run'][1]})\n"
                f"Before: {sorted(old_domain)}\n"
                f"After: {sorted(new_domain)}\n"
                f"Removed: {removed}"
            )
        elif event_type == "ASSIGN":
            message = f"Assign {data['value']} to cell {data['cell']}"
        elif event_type == "BACKTRACK":
            message = (
                f"Backtrack at {data['cell']}\n"
                f"Rejected value: {data['value']}"
            )
        elif event_type == "SOLVED":
            message = "Solution found!"
        elif event_type == "INIT":
            cfg = data.get("config", {})
            message = (
                f"Initializing domains...\n"
                f"Var: {cfg.get('var')}, Val: {cfg.get('val')}"
            )
        else:
            message = f"Solver stopped ({data.get('reason', 'failed')})."

        self.event_detail.config(text=message)
        self.draw_board()


if __name__ == "__main__":
    root = tk.Tk()
    app = KakuroGUI(root)
    root.mainloop()